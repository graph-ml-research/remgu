# Python API: use ReMgu from a training script

[English](../../README.md) | [Русский](../ru/python-api.md)

The API is deliberately thin: keep your existing training loop and use `Experiment` to obtain a `Run`. Run metadata is stored separately from parameters, metrics, and selected diagnostic examples.

## Minimal training example

Create the run in the CLI first:

```bash
research new --hypothesis "hidden_dim=512 improves NDCG@20" --motivation-type new
```

Then use the active run in your training script:

```python
from remgu import Experiment

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

`train_and_evaluate` is application code, not a ReMgu function. The example shows where to place the instrumentation.

### Create a run directly through the API

Use this when run creation should be controlled by Python rather than the CLI:

```python
from remgu import Experiment, Motivation

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
from remgu import TopKSelector

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
from remgu import ExampleSelector, TopKSelector

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

`ExampleProvider` is a `Protocol` for application-specific data access. Implement `get(example_id)` to load the source example or lightweight context, and `describe(example_id)` to return a human-readable description. ReMgu does not prescribe a dataset, database, or storage engine.

```python
from typing import Any

from remgu import ExampleProvider

class MyExampleProvider:
    def get(self, example_id: str) -> Any:
        return dataset.lookup(example_id)

    def describe(self, example_id: str) -> str:
        row = dataset.lookup(example_id)
        return f"label={row['label']}, source={row['source']}"
```

`dataset.lookup` is an application-specific placeholder. ReMgu does not prescribe or persist a provider. For exports, you can inject an instance into `ResearchSnapshotBuilder` and opt into short descriptions; this keeps the publication adapters snapshot-only:

```python
from remgu import ResearchSnapshotBuilder, StaticSiteAdapter

provider = MyExampleProvider()  # configured by your application
snapshot = ResearchSnapshotBuilder(
    ".research", example_provider=provider, describe_examples=True
).build()
StaticSiteAdapter().export(snapshot, "site")
```

Descriptions are added only to the in-memory snapshot and are not written back to `samples.jsonl`. `describe()` should be cheap and concise; it should not load a large sample or run model inference.

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
from remgu import (
    Experiment,
    Motivation,
    Run,
    ExampleProvider,
    TopKSelector,
    ExampleSelector,
)
```

The current package exports these symbols. The low-level `FileStorage` and consistency-report types can be imported from their modules, but are not part of the package's top-level public exports.


## Read-only research analysis

Important research-layer classes are exported directly from `remgu`:

```python
from remgu import ResearchChecker, ResearchSnapshotBuilder

report = ResearchChecker(".research").check()
snapshot = ResearchSnapshotBuilder(".research").build()
```

`FileStorage` is an implementation detail here; student-facing code should not need to construct it just to run consistency checks.

## Markdown publication adapter

```python
from remgu import MarkdownAdapter, ResearchSnapshotBuilder

snapshot = ResearchSnapshotBuilder(".research").build()
report_path = MarkdownAdapter().export(snapshot, "research.md")
```

`MarkdownAdapter` only renders the in-memory snapshot. It does not read the research store, modify runs, execute ML, or infer conclusions. Existing output files are not overwritten.


## Static site publication

```python
from remgu import ResearchSnapshotBuilder, StaticSiteAdapter

snapshot = ResearchSnapshotBuilder(".research").build()
site_path = StaticSiteAdapter().export(snapshot, "site")
```

`StaticSiteAdapter` accepts only a `ResearchSnapshot`; it never reads `.research` or accesses `Run` objects. It writes a static site without JavaScript or a backend and refuses to overwrite an existing destination directory.
