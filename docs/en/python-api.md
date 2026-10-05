# Python API: use REMgu from a training script

[English](../../README.md) | [Русский](../ru/python-api.md)

The API is deliberately thin: keep your existing training loop and use `Experiment` to obtain a `Run`. Run metadata is stored separately from parameters, metrics, and selected diagnostic examples.

## Minimal training example

Create the run in the CLI first:

```bash
python -m research.cli new --hypothesis "hidden_dim=512 improves NDCG@20" --motivation-type new
```

Then use the active run in your training script:

```python
from research import Experiment

experiment = Experiment("graph-mamba")
with experiment.run() as run:
    run.log_params({
        "hidden_dim": 512,
        "learning_rate": 1e-3,
        "seed": 42,
    })

    for epoch in range(10):
        # Replace with real training and evaluation.
        ndcg_at_20 = train_and_evaluate(epoch)
        run.log_metric("ndcg_at_20", ndcg_at_20, step=epoch)
```

`train_and_evaluate` is application code, not a REMgu function. The example shows where to place the instrumentation.

### Create a run directly through the API

Use this when run creation should be controlled by Python rather than the CLI:

```python
from research import Experiment, Motivation

experiment = Experiment("graph-mamba", base_path=".research")
with experiment.run(
    hypothesis="Random-walk ordering improves graph sequence quality",
    motivation=Motivation(type="literature_citation", reference="paper-2402.00789"),
) as run:
    run.log_metric("validation_auc", 0.8263, step=1)
```

`hypothesis` and `motivation` must be supplied together. Calling `experiment.run()` with no arguments reopens the active run; it does not create a new run. If no active run exists, it raises `RuntimeError` and asks you to run `research new` first.

## Record parameters, metrics, and examples

### Parameters

```python
run.log_params({"hidden_dim": 512, "dropout": 0.1})
run.log_params({"dropout": 0.2})  # updates the stored value of dropout
```

Parameters are written to `params.yaml`. Repeated calls merge the supplied keys into the existing mapping; a key supplied again is replaced. Store the effective configuration used for this run, not only the values you intended to pass.

### Metrics

```python
run.log_metric("loss", 0.42, step=10)
run.log_metrics({"auc": 0.8263, "f1": 0.74}, step=10)
```

Each call appends rows to `metrics.csv`. The columns are `step`, `metric_name`, and `metric_value`; the step is optional. Repeated metric names are allowed because the file is a time series, not a dictionary.

### Diagnostic examples

```python
run.collect({
    "example_id": "node-104",
    "prediction": 0.12,
    "baseline_prediction": 0.83,
    "diagnostic": "large_regression",
})
```

Each call appends one JSON object to `samples.jsonl`. Store compact references and diagnostic fields, not a full copy of the dataset. The application can later resolve `example_id` to the original data.

## Select diagnostic examples with TopKSelector

`TopKSelector` keeps at most `k` records, avoiding the need to retain the entire validation set in memory.

```python
from research import TopKSelector

largest_regressions = TopKSelector(
    k=20,
    key=lambda row: row["baseline_score"] - row["score"],
    name="largest_regression",
)

for row in validation_records:
    largest_regressions.consider(row)

for row in largest_regressions.records():
    run.collect(row)
```

The `key` callable calculates the selection score. By default the largest scores are retained. Set `largest=False` to keep the smallest scores. Alternatively, pass the score to `consider(record, priority)` or `consider(record, score=...)`.

## Combine multiple criteria with ExampleSelector

```python
from research import ExampleSelector, TopKSelector

selectors = ExampleSelector([
    TopKSelector(k=10, key=lambda row: row["score"], largest=False, name="lowest_score"),
    TopKSelector(k=10, key=lambda row: row["regression"], name="largest_regression"),
])

for row in validation_records:
    selectors.consider(row)

for row in selectors.records():
    run.collect(row)
```

The result contains each selected `example_id` once. Its `selection.reasons` lists all selectors that selected it, and `selection.scores` contains scores for selectors configured with a `key`.

## Resolve example IDs with ExampleProvider

`ExampleProvider` is a `Protocol` for application-specific data access. Implement `get(example_id)` to load the source example or lightweight context, and `describe(example_id)` to return a human-readable description. REMgu does not prescribe a dataset, database, or storage engine.

```python
from typing import Any

from research import ExampleProvider

class MyExampleProvider:
    def get(self, example_id: str) -> Any:
        return dataset.lookup(example_id)

    def describe(self, example_id: str) -> str:
        row = dataset.lookup(example_id)
        return f"label={row['label']}, source={row['source']}"
```

`dataset.lookup` is an application-specific placeholder. The provider is an interface; this version does not automatically instantiate or persist a provider.

## Lifecycle and exceptions

```python
with experiment.run() as run:
    run.log_metric("loss", 0.42)
```

- On normal exit, a run still in `running` becomes `completed` and its active pointer is removed.
- If an exception escapes the block, the run becomes `failed`; its exception type and message are stored, and the exception continues to propagate.
- Call `run.abort()` to mark a running run as `aborted` explicitly.
- Artifact-writing methods reject changes after the run leaves `running`.
- `research finish` is a separate review step and records `conclusion` and `next_step`.

## Public API summary

```python
from research import (
    Experiment,
    Motivation,
    Run,
    ExampleProvider,
    TopKSelector,
    ExampleSelector,
)
```

The current package exports these symbols. The low-level `FileStorage` and consistency-report types can be imported from their modules, but are not part of the package's top-level public exports.
