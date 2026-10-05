# Architecture and boundaries

[English](../../README.md) | [Русский](../ru/architecture.md)

## What REMgu owns

```text
research question
       ↓
 hypothesis + motivation
       ↓
      Run ───────────────┐
       │                 │
       ├─ run.yaml       ├─ execution lifecycle
       ├─ params.yaml    ├─ effective configuration
       ├─ metrics.csv    ├─ metric history
       └─ samples.jsonl  └─ compact diagnostic examples
       ↓
 conclusion + next step
```

REMgu provides a small persistence and lifecycle layer around an existing Python experiment. It does not own model training, data loading, metric calculation, hyperparameter search, scheduling, or a remote tracking service.

## Main components

- `Experiment` — facade used by training code to create a run or reopen the active run.
- `Run` — one concrete execution; records lifecycle transitions and writes artifacts.
- `Motivation`, `ResearchMetadata`, `Execution`, `Review` — structured parts of the run record.
- `FileStorage` — filesystem persistence for run metadata and the active pointer.
- `TopKSelector` / `ExampleSelector` — bounded-memory selection of diagnostic examples.
- `ExampleProvider` — protocol for application-specific resolution of example IDs.
- `check_consistency` — read-only validation of persisted research records.
- `research.cli` — command-line interface over the same file-based state.

## Architectural boundaries

**Experiment code → REMgu.** The project owns training, evaluation, datasets, and domain-specific metrics. REMgu records the hypothesis, configuration snapshot, metric stream, and selected diagnostic examples.

**REMgu → filesystem.** The current implementation stores ordinary YAML, CSV, JSONL, and a small text pointer. It does not require a database or server.

**Consistency check → stored files.** The checker reads raw records so it can report malformed entries. It does not mutate them or attempt automatic repair.

**Future knowledge/agent layers → REMgu.** A future knowledge base or agent may create hypotheses and inspect results, but should not be coupled into this core lifecycle. Those layers are not implemented in the current version.

## Why execution and review are separate

A process can exit successfully without supporting the hypothesis. Therefore `execution.status = completed` does not imply `review.status = reviewed`. The review step stores the researcher's conclusion and the proposed next step independently.

## Current limitations

- Storage is local and file-based; concurrent writers and distributed execution are not coordinated.
- The active pointer supports one active run per research directory.
- REMgu does not calculate metrics or validate their scientific meaning.
- `samples.jsonl` is not a dataset store and does not resolve IDs by itself.
- Consistency checking reports structural/workflow issues but does not repair them.
- Publication, knowledge-base management, agent orchestration, and site generation are future directions, not current features.
