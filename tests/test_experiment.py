# -*- coding: utf8 -*-
from pathlib import Path
import pytest
import yaml
from research import Experiment, Motivation

__author__ = 'Mstislav Maslennikov'


def test_custom_base_path(tmp_path: Path):
    base = tmp_path / "research-data"
    experiment = Experiment("graph-mamba", base)

    with experiment.run("H1", Motivation(type="literature_citation", reference="paper-123")):
        pass

    assert (base / "runs" / "run-001" / "run.yaml").exists()


def test_run_without_arguments_continues_active_cli_run(tmp_path: Path):
    base = tmp_path / ".research"
    from research.cli import main
    assert main(
        (
            "--base-path",
            str(base),
            "new",
            "--hypothesis",
            "H1",
            "--motivation-type",
            "previous_run",
            "--reference",
            "run-002",
        )
    ) == 0

    experiment = Experiment("graph-mamba", base)
    with experiment.run() as run:
        assert run.run_id == "run-001"
        assert run.research.hypothesis == "H1"
        assert run.research.motivation.type == "previous_run"
        assert run.research.motivation.reference == "run-002"

    data = yaml.safe_load((base / "runs" / "run-001" / "run.yaml").read_text())
    assert data["execution"]["status"] == "completed"
    assert data["review"]["status"] == "needs_review"
    assert not (base / "active").exists()


def test_run_without_arguments_requires_active_run(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")

    with pytest.raises(RuntimeError, match="research new"):
        experiment.run()


def test_run_without_arguments_does_not_create_second_run(tmp_path: Path):
    base = tmp_path / ".research"
    experiment = Experiment("graph-mamba", base)

    with experiment.run("H1", Motivation(type="new")) as first:
        assert first.run_id == "run-001"

    with pytest.raises(RuntimeError, match="research new"):
        experiment.run()

    assert not (base / "runs" / "run-002").exists()


def test_run_rejects_partial_programmatic_arguments(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")

    with pytest.raises(ValueError, match="provided together"):
        experiment.run("H1")

    with pytest.raises(ValueError, match="provided together"):
        experiment.run(motivation=Motivation(type="new"))
