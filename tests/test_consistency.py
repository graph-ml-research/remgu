from pathlib import Path

import yaml

from research.cli import main
from research.consistency import check_consistency


def run_cli(base: Path, *args: str) -> int:
    return main(("--base-path", str(base), *args))


def write_run(base: Path, run_id: str, data: dict) -> None:
    path = base / "runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "run.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def base_run(hypothesis="H1", motivation=None, status="completed", conclusion=None, next_step=None):
    return {
        "run_id": "run-001",
        "research": {
            "hypothesis": hypothesis,
            "motivation": motivation or {"type": "new", "reference": None},
        },
        "execution": {"status": status},
        "review": {
            "status": "reviewed" if conclusion else "needs_review",
            "conclusion": conclusion,
            "next_step": next_step,
        },
    }


def test_check_reports_completed_and_hypothesis_runs(tmp_path: Path):
    base = tmp_path / ".research"
    write_run(base, "run-001", base_run(conclusion="supported", next_step="H2"))
    write_run(base, "run-002", base_run(hypothesis="H2", status="failed"))

    report = check_consistency(__import__("research.storage", fromlist=["FileStorage"]).FileStorage(base))

    assert report.completed_runs == ["run-001"]
    assert report.runs_with_hypotheses == ["run-001", "run-002"]
    assert report.issues == []


def test_check_flags_weak_motivation_and_missing_conclusion(tmp_path: Path):
    base = tmp_path / ".research"
    write_run(base, "run-001", base_run(motivation={"type": "previous_run"}))

    from research.storage import FileStorage
    report = check_consistency(FileStorage(base))
    codes = {issue.code for issue in report.issues}
    assert "weak_motivation" in codes
    assert "missing_conclusion" in codes


def test_check_handles_failed_and_aborted_runs_without_requiring_conclusion(tmp_path: Path):
    base = tmp_path / ".research"
    write_run(base, "run-001", base_run(status="failed"))
    write_run(base, "run-002", base_run(status="aborted"))

    from research.storage import FileStorage
    report = check_consistency(FileStorage(base))
    assert report.completed_runs == []
    assert not any(issue.code == "missing_conclusion" for issue in report.issues)


def test_check_detects_broken_previous_run_reference(tmp_path: Path):
    base = tmp_path / ".research"
    write_run(
        base,
        "run-001",
        base_run(
            motivation={"type": "previous_run", "reference": "run-999"},
            conclusion="done",
            next_step="next",
        ),
    )

    from research.storage import FileStorage
    report = check_consistency(FileStorage(base))
    assert any(issue.code == "broken_motivation_reference" for issue in report.issues)


def test_check_is_read_only(tmp_path: Path):
    base = tmp_path / ".research"
    data = base_run()
    write_run(base, "run-001", data)
    before = (base / "runs" / "run-001" / "run.yaml").read_bytes()

    from research.storage import FileStorage
    check_consistency(FileStorage(base))

    assert (base / "runs" / "run-001" / "run.yaml").read_bytes() == before


## missing
def test_check_cli_output(tmp_path: Path, capsys):
    base = tmp_path / ".research"
    write_run(base, "run-001", base_run(conclusion="done", next_step="next"))

    assert run_cli(base, "check") == 0
    output = capsys.readouterr().out
    assert "completed runs: 1" in output
    assert "runs with hypotheses: 1" in output
    assert "issues: none" in output
