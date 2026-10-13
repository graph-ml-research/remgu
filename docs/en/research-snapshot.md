# Research Snapshot

[English](research-snapshot.md) | [Русский](../ru/research-snapshot.md)

`ResearchSnapshot` is the common in-memory input for ReMgu's research analysis and publication layers.

It is **not** a persisted domain entity and never becomes a second source of truth. It is rebuilt from `.research/` whenever needed.

## Build a snapshot

```python
from remgu import ResearchSnapshotBuilder

snapshot = ResearchSnapshotBuilder(".research", describe_examples=False).build()
print(snapshot.summary.total_runs)
print(snapshot.summary.completed)
print(snapshot.summary.reviewed)
```

The builder reads existing `run.yaml`, `params.yaml`, `metrics.csv`, and `samples.jsonl` files. By default it also requires an `ExampleProvider` and adds a short description to each sample with an `example_id`. Explicitly pass `describe_examples=False` when descriptions are not needed. A missing provider or an empty description in enabled mode raises an error. The builder also runs the read-only consistency checker and places its findings into `snapshot.findings`.

## Model

The snapshot contains:

- `summary` — total, execution-state and review-state counts;
- `runs` — derived views of individual runs;
- `relations` — only the references already present in `motivation.reference`;
- `metrics` — flattened metric rows with their run IDs;
- `samples` — flattened compact diagnostic records with their run IDs;
- `findings` — consistency findings;
- `summary_text` — a short human-readable summary.

No dataset, graph object, model object, or other large external object is loaded.

## `research update`

```bash
research update
```

This command builds the snapshot, runs consistency analysis, and prints a short summary. It does not write anything under `.research/`.

## Architectural boundary

The core layer owns persistent runs and artifacts. The research layer derives the snapshot and consistency findings. Publication adapters consume snapshots; they should not become alternative storage implementations.
