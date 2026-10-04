# -*- coding: utf8 -*-
from pathlib import Path

import pytest
import yaml

from research import Experiment

__author__ = 'Mstislav Maslennikov'


def test_create_run_and_persist_yaml(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")
    run = experiment.run(
        hypothesis="Увеличение hidden_dim до 512 улучшит NDCG@20.",
        motivation={"type": "new"},
    )

    data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert data["run_id"] == "run-001"
    assert data["research"]["hypothesis"] == "Увеличение hidden_dim до 512 улучшит NDCG@20."
    assert data["research"]["motivation"] == {"type": "new", "reference": None}
    assert data["execution"]["status"] == "running"
    assert data["execution"]["started_at"] is not None
    assert data["execution"]["finished_at"] is None
    assert data["review"] == {
        "status": "needs_review",
        "conclusion": None,
        "next_step": None,
    }
    assert (tmp_path / ".research" / "active").read_text().strip() == "run-001"


def test_successful_context_manager_cleans_active(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")

    with experiment.run("H1", {"type": "new"}) as run:
        assert run.status == "running"

    data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert data["execution"]["status"] == "completed"
    assert data["execution"]["started_at"] is not None
    assert data["execution"]["finished_at"] is not None
    assert not (tmp_path / ".research" / "active").exists()


def test_exception_marks_failed_and_reraises(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")

    with pytest.raises(RuntimeError, match="CUDA out of memory"):
        with experiment.run("H1", {"type": "new"}) as run:
            raise RuntimeError("CUDA out of memory")

    data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert data["execution"]["status"] == "failed"
    assert data["execution"]["error"] == {
        "type": "RuntimeError",
        "message": "CUDA out of memory",
    }
    assert data["execution"]["finished_at"] is not None
    assert not (tmp_path / ".research" / "active").exists()


def test_abort(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")
    run = experiment.run("H1", {"type": "new"})
    run.abort()

    data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert data["execution"]["status"] == "aborted"
    assert data["execution"]["finished_at"] is not None
    assert not (tmp_path / ".research" / "active").exists()


def test_second_active_run_is_forbidden(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")
    first = experiment.run("H1", {"type": "new"})

    with pytest.raises(RuntimeError, match="already active"):
        experiment.run("H2", {"type": "new"})

    first.abort()
    second = experiment.run("H2", {"type": "previous_run", "reference": first.run_id})
    assert second.run_id == "run-002"
    second.abort()


def test_run_ids_are_sequential(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")
    for expected in ("run-001", "run-002", "run-003"):
        run = experiment.run("H", {"type": "new"})
        assert run.run_id == expected
        run.abort()


def test_reference_is_optional_for_new_motivation(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")
    with experiment.run("H", {"type": "new"}) as run:
        pass
    data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert data["research"]["motivation"]["reference"] is None


def make_experiment(tmp_path: Path) -> Experiment:
    return Experiment("graph-mamba", tmp_path / ".research")


def test_log_params(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.log_params({"hidden_dim": 512, "batch_size": 64})

    params = yaml.safe_load((run.path / "params.yaml").read_text(encoding="utf-8"))
    assert params == {"hidden_dim": 512, "batch_size": 64}


def test_log_params_updates_existing_keys(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.log_params({"hidden_dim": 256, "batch_size": 64})
        run.log_params({"hidden_dim": 512})

    params = yaml.safe_load((run.path / "params.yaml").read_text(encoding="utf-8"))
    assert params == {"hidden_dim": 512, "batch_size": 64}


def test_log_metric_creates_metrics_csv(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.log_metric("loss", 0.5)

    lines = (run.path / "metrics.csv").read_text(encoding="utf-8").splitlines()
    assert lines == [
        "step,metric_name,metric_value",
        ",loss,0.5",
    ]


def test_log_metrics_with_step(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.log_metrics({"loss": 0.5, "ndcg20": 0.428}, step=10)

    lines = (run.path / "metrics.csv").read_text(encoding="utf-8").splitlines()
    assert lines == [
        "step,metric_name,metric_value",
        "10,loss,0.5",
        "10,ndcg20,0.428",
    ]


def test_multiple_metric_records(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.log_metric("loss", 0.82, step=1)
        run.log_metric("loss", 0.51, step=10)
        run.log_metrics({"ndcg20": 0.428}, step=10)

    lines = (run.path / "metrics.csv").read_text(encoding="utf-8").splitlines()
    assert lines == [
        "step,metric_name,metric_value",
        "1,loss,0.82",
        "10,loss,0.51",
        "10,ndcg20,0.428",
    ]


def test_collect_writes_jsonl(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.collect({"example_id": "node-42", "target": 1, "prediction": 0})
        run.collect({"example_id": "node-73", "target": 0, "prediction": 1})

    lines = (run.path / "samples.jsonl").read_text(encoding="utf-8").splitlines()
    assert lines == [
        '{"example_id":"node-42","target":1,"prediction":0}',
        '{"example_id":"node-73","target":0,"prediction":1}',
    ]


def test_artifacts_are_not_in_run_yaml(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    with experiment.run("H1", {"type": "new"}) as run:
        run.log_params({"hidden_dim": 512})
        run.log_metric("loss", 0.5)
        run.collect({"example_id": "node-42", "prediction": 0})

    data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert "params" not in data
    assert "metrics" not in data
    assert "samples" not in data


def test_artifacts_survive_failed_run(tmp_path: Path):
    experiment = make_experiment(tmp_path)

    with pytest.raises(RuntimeError, match="boom"):
        with experiment.run("H1", {"type": "new"}) as run:
            run.log_params({"hidden_dim": 512})
            run.log_metric("loss", 0.5)
            run.collect({"example_id": "node-42", "prediction": 0})
            raise RuntimeError("boom")

    assert (run.path / "params.yaml").exists()
    assert (run.path / "metrics.csv").exists()
    assert (run.path / "samples.jsonl").exists()

    run_data = yaml.safe_load((run.path / "run.yaml").read_text(encoding="utf-8"))
    assert run_data["execution"]["status"] == "failed"


def test_artifact_methods_reject_terminal_run(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    run = experiment.run("H1", {"type": "new"})
    run.complete()

    with pytest.raises(RuntimeError, match="completed"):
        run.log_metric("loss", 0.5)
    with pytest.raises(RuntimeError, match="completed"):
        run.log_params({"hidden_dim": 512})
    with pytest.raises(RuntimeError, match="completed"):
        run.collect({"example_id": "node-42"})




class DictProvider:
    def __init__(self, data):
        self.data = data

    def get(self, example_id):
        return self.data[example_id]


def test_get_sample_resolves_example_without_writing_it(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    provider = DictProvider({"node-42": {"node": 42, "neighbors": [1, 2]}})

    with experiment.run("H1", {"type": "new"}) as run:
        sample = run.get_sample("node-42", provider)

    assert sample == {"node": 42, "neighbors": [1, 2]}
    assert not (run.path / "samples.jsonl").exists()


def test_get_sample_rejects_empty_id(tmp_path: Path):
    experiment = make_experiment(tmp_path)
    provider = DictProvider({})
    with experiment.run("H1", {"type": "new"}) as run:
        with pytest.raises(ValueError, match="example_id"):
            run.get_sample("", provider)