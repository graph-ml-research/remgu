# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from remgu.experiment import Experiment
from remgu.example import TopKSelector
from remgu.example.example_selector import ExampleSelector



def test_multi_selector_merges_reasons_without_duplicate_examples():
    lowest = TopKSelector(k=2, key=lambda r: r["score"], largest=False, name="lowest_score")
    regression = TopKSelector(k=2, key=lambda r: r["regression"], name="largest_regression")
    selectors = ExampleSelector([lowest, regression])

    records = [
        {"example_id": "a", "score": 0.1, "regression": 0.2},
        {"example_id": "b", "score": 0.9, "regression": 0.8},
        {"example_id": "c", "score": 0.2, "regression": 0.9},
    ]
    for record in records:
        selectors.consider(record)

    result = {r["example_id"]: r for r in selectors.records()}
    assert set(result) == {"a", "b", "c"}
    assert result["a"]["selection"]["reasons"] == ["lowest_score"]
    assert result["b"]["selection"]["reasons"] == ["largest_regression"]
    assert result["c"]["selection"]["reasons"] == ["lowest_score", "largest_regression"]
    assert result["c"]["selection"]["scores"] == {"lowest_score": 0.2, "largest_regression": 0.9}


def test_selected_records_can_be_written_to_run(tmp_path: Path):
    experiment = Experiment("graph-mamba", tmp_path / ".research")
    selector = TopKSelector(k=2, key=lambda r: r["error"])
    selector.consider({"example_id": "a", "error": 0.1})
    selector.consider({"example_id": "b", "error": 0.9})
    selector.consider({"example_id": "c", "error": 0.4})

    with experiment.run("H1", {"type": "new"}) as run:
        for record in selector.records():
            run.collect(record)

    lines = (run.path / "samples.jsonl").read_text(encoding="utf-8").splitlines()
    assert lines == [
        '{"example_id":"b","error":0.9}',
        '{"example_id":"c","error":0.4}',
    ]

