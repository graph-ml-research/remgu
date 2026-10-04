# -*- coding: utf8 -*-
from pathlib import Path

import pytest

from research import Experiment, TopKSelector, ExampleProvider, ExampleSelector

__author__ = 'Mstislav Maslennikov'

def test_top_k_selector_keeps_only_highest_priority():
    selector = TopKSelector(k=2)
    for example_id, priority in (("a", 0.1), ("b", 0.9), ("c", 0.4), ("d", 1.2)):
        selector.consider({"example_id": example_id}, priority)

    assert selector.records() == [
        {"example_id": "d"},
        {"example_id": "b"},
    ]
    assert len(selector) == 2


def test_top_k_selector_can_choose_smallest_score_with_key():
    selector = TopKSelector(
        k=2,
        key=lambda r: r["score"],
        largest=False,
        name="lowest_score",
    )
    for score in (0.8, 0.1, 0.5, 0.2):
        selector.consider({"example_id": str(score), "score": score})

    assert [r["score"] for r in selector.records()] == [0.1, 0.2]


def test_top_k_selector_can_choose_largest_change():
    selector = TopKSelector(
        k=2,
        key=lambda r: abs(r["score"] - r["baseline_score"]),
        name="largest_change",
    )
    selector.consider({"example_id": "a", "score": 0.3, "baseline_score": 0.4})
    selector.consider({"example_id": "b", "score": 0.1, "baseline_score": 0.8})
    selector.consider({"example_id": "c", "score": 0.7, "baseline_score": 0.2})

    assert [r["example_id"] for r in selector.records()] == ["b", "c"]


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


def test_top_k_selector_does_not_require_dataset_storage():
    selector = TopKSelector(k=2, key=lambda r: r["score"])
    for i in range(1000):
        selector.consider({"example_id": str(i), "score": i})

    assert len(selector) == 2
    assert [r["example_id"] for r in selector.records()] == ["999", "998"]


def test_top_k_selector_rejects_invalid_k():
    with pytest.raises(ValueError, match="positive"):
        TopKSelector(0)


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

