# -*- coding: utf8 -*-
from pathlib import Path
import pytest
import yaml
from research.cli import main


__author__ = 'Mstislav Maslennikov'

def run_cli(base: Path, *args: str) -> int:
    return main(("--base-path", str(base), *args))


def read_run(base: Path, run_id: str = "run-001"):
    return yaml.safe_load((base / "runs" / run_id / "run.yaml").read_text(encoding="utf-8"))


def test_new_creates_running_execution_and_pending_review(tmp_path: Path, capsys):
    assert run_cli(
        tmp_path / ".research",
        "new",
        "--hypothesis", "H1",
        "--motivation-type", "new",
    ) == 0
    data = read_run(tmp_path / ".research")
    assert data["execution"]["status"] == "running"
    assert data["review"]["status"] == "needs_review"
    assert (tmp_path / ".research" / "active").read_text().strip() == "run-001"


def test_new_forbids_second_active_run(tmp_path: Path):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    with pytest.raises(SystemExit, match="already active"):
        run_cli(base, "new", "--hypothesis", "H2")


def test_resume_restores_missing_active_pointer_without_changing_state(tmp_path: Path):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    (base / "active").unlink()
    assert run_cli(base, "resume", "run-001") == 0
    data = read_run(base)
    assert data["execution"]["status"] == "running"
    assert data["review"]["status"] == "needs_review"
    assert (base / "active").read_text().strip() == "run-001"


def test_resume_rejects_terminal_run(tmp_path: Path):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    (base / "active").unlink()
    data = read_run(base)
    data["execution"]["status"] = "completed"
    data["execution"]["finished_at"] = "2026-09-25T10:00:00Z"
    (base / "runs" / "run-001" / "run.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="Only a running run"):
        run_cli(base, "resume", "run-001")


def test_finish_moves_review_to_reviewed(tmp_path: Path):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    data = read_run(base)
    data["execution"]["status"] = "completed"
    data["execution"]["finished_at"] = "2026-09-25T10:00:00Z"
    (base / "runs" / "run-001" / "run.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )
    (base / "active").unlink()

    assert run_cli(
        base,
        "finish",
        "run-001",
        "--conclusion",
        "H1 supported",
        "--next-step",
        "Run H2",
    ) == 0
    data = read_run(base)
    assert data["execution"]["status"] == "completed"
    assert data["review"] == {
        "status": "reviewed",
        "conclusion": "H1 supported",
        "next_step": "Run H2",
    }


def test_finish_requires_completed_execution(tmp_path: Path):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    with pytest.raises(SystemExit, match="only after a completed execution"):
        run_cli(
            base,
            "finish",
            "run-001", "--conclusion", "x",
            "--next-step", "y",
        )


def test_finish_requires_both_review_fields(tmp_path: Path):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    data = read_run(base)
    data["execution"]["status"] = "completed"
    data["execution"]["finished_at"] = "2026-09-25T10:00:00Z"
    (base / "runs" / "run-001" / "run.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )
    (base / "active").unlink()
    with pytest.raises(SystemExit, match="--conclusion is required"):
        run_cli(base, "finish", "run-001", "--next-step", "y")
    with pytest.raises(SystemExit, match="--next-step is required"):
        run_cli(base, "finish", "run-001", "--conclusion", "x")


def test_status_reports_both_lifecycles(tmp_path: Path, capsys):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "H1")
    assert run_cli(base, "status") == 0
    output = capsys.readouterr().out
    assert "execution.status: running" in output
    assert "review.status: needs_review" in output


def test_previous_lists_recent_runs_oldest_first(tmp_path: Path, capsys):
    base = tmp_path / ".research"
    run_cli(base, "new", "--hypothesis", "First hypothesis", "--motivation-type", "new")
    capsys.readouterr()
    (base / "active").unlink()

    run_cli(
        base,
        "new",
        "--hypothesis", "Second hypothesis",
        "--motivation-type", "previous_run",
        "--reference", "run-001",
    )
    capsys.readouterr()
    (base / "active").unlink()

    assert run_cli(base, "previous") == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert lines[0].startswith("run-001 | execution=running | review=needs_review")
    assert lines[1].startswith("run-002 | execution=running | review=needs_review")
    assert "motivation=previous_run -> run-001" in lines[1]
    assert "hypothesis=Second hypothesis" in lines[1]


def test_previous_limit_returns_only_requested_number(tmp_path: Path, capsys):
    base = tmp_path / ".research"
    for i in range(3):
        run_cli(base, "new", "--hypothesis", f"H{i + 1}")
        capsys.readouterr()
        (base / "active").unlink()

    assert run_cli(base, "previous", "--limit", "2") == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert len(lines) == 2
    assert lines[0].startswith("run-002 |")
    assert lines[1].startswith("run-003 |")


def test_previous_when_no_runs(tmp_path: Path, capsys):
    assert run_cli(tmp_path / ".research", "previous") == 0
    assert capsys.readouterr().out.strip() == "runs: none"