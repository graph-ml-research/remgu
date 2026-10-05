# ReMgu

**English** | [Русский](README.ru.md)

**Experiment lifecycle management for reproducible ML research.**

ReMgu connects a research hypothesis to a concrete run, its metrics and diagnostic examples, and a written conclusion with the next step. It stores this record as ordinary files in `.research/`, so the history can be inspected, versioned, and reviewed without a tracking server.

> **Current scope:** run lifecycle, parameters, metrics, diagnostic samples, and read-only consistency checks. Knowledge-base management, agent workflows, report/site generation, and `research update` are not implemented in this version.

## Start here

| What you want to do | Interface | Guide |
|---|---|---|
| Create a run before training | CLI | [CLI workflow](docs/en/cli.md#1-create-a-run) |
| Run existing training code and log results | Python API | [Python API](docs/en/python-api.md#minimal-training-example) |
| Record parameters, metrics, and diagnostic examples | Python API | [Run artifacts](docs/en/python-api.md#record-parameters-metrics-and-examples) |
| Review a completed run and record the conclusion | CLI | [CLI workflow](docs/en/cli.md#2-review-a-completed-run) |
| Inspect previous runs and the active run | CLI | [CLI workflow](docs/en/cli.md#3-inspect-run-history) |
| Find incomplete or inconsistent research records | CLI / API | [Consistency check](docs/en/consistency-check.md) |
| Understand the files ReMgu creates | Reference | [On-disk format](docs/en/data-format.md) |

## The research loop

```text
question / observation
        ↓
   hypothesis + motivation
        ↓
       run-001
        ├── params.yaml
        ├── metrics.csv
        └── samples.jsonl
        ↓
 execution: completed / failed / aborted
        ↓
 conclusion + next step
        ↓
    next hypothesis
```

A **run** is one concrete execution. The hypothesis and motivation explain why it exists; execution metadata records what happened; review metadata records what was learned and what should happen next.

## Quick start

From a checkout of this repository, install the dependency and create a run:

```bash
python -m pip install pyyaml
python -m research.cli new \
  --hypothesis "Increasing hidden_dim to 512 improves NDCG@20" \
  --motivation-type previous_run \
  --reference run-001
```

The command prints the new run ID. It creates `.research/` in the current directory unless `--base-path` is supplied. The reference above is illustrative: use an existing run ID, or omit `--reference` and use `--motivation-type new` for a new research direction.

In your training script:

```python
from research import Experiment, Motivation

experiment = Experiment("graph-mamba")
with experiment.run() as run:
    run.log_params({"hidden_dim": 512, "learning_rate": 1e-3})

    # Replace this block with your training and evaluation code.
    run.log_metric("ndcg_at_20", 0.428, step=1)
    run.collect({"example_id": "user-104", "score": 0.12, "reason": "large_regression"})
```

The no-argument `experiment.run()` resumes the active run created by the CLI. Exiting the `with` block marks a still-running run as completed; an uncaught exception marks it as failed and records its type and message.

After validating the result, review it:

```bash
python -m research.cli finish run-002 \
  --conclusion "NDCG@20 increased from 0.401 to 0.428 on the fixed validation set" \
  --next-step "Repeat with three random seeds"
```

Use the actual ID printed by `research new`; `run-002` is only an example. Full walkthroughs: [CLI](docs/en/cli.md) · [Python API](docs/en/python-api.md).

## Interfaces

### Command line

```bash
python -m research.cli --help
python -m research.cli new --help
python -m research.cli status
python -m research.cli previous --limit 10
python -m research.cli resume run-001
python -m research.cli finish run-001 --conclusion "..." --next-step "..."
python -m research.cli check
```

The CLI defaults to `.research/`. Pass `--base-path /path/to/research-data` before the subcommand to use another directory.

### Python API

```python
from research import Experiment, Motivation, Run, ExampleProvider, TopKSelector
```

- `Experiment` opens the active run or creates one programmatically.
- `Run` tracks execution state and writes parameters, metrics, and diagnostic records.
- `Motivation` describes why a hypothesis is being tested.
- `TopKSelector` keeps the highest- or lowest-scoring diagnostic records in bounded memory.
- `ExampleSelector` merges named selection criteria and annotates why each example was selected.
- `ExampleProvider` defines how a stored example ID can be resolved to source data and a readable description.

See the [API guide](docs/en/python-api.md) for signatures and complete examples.

## Design principles

- **Research context stays with the run.** A run stores its hypothesis and motivation, not just a metric dump.
- **Ordinary training scripts stay ordinary.** ReMgu wraps the code you already run; it does not require a new training framework.
- **Files are the source of truth.** YAML, CSV, and JSONL are human-readable and easy to version or inspect.
- **Execution and review are separate.** A successful process is not the same thing as a scientifically reviewed result.
- **Checks are read-only.** `research check` reports problems without repairing or rewriting run records.

## Documentation

- [CLI workflows](docs/en/cli.md)
- [Python API](docs/en/python-api.md)
- [Consistency checks](docs/en/consistency-check.md)
- [On-disk data format](docs/en/data-format.md)
- [Architecture and boundaries](docs/en/architecture.md)
- [Russian documentation](README.ru.md)

## Development status

ReMgu is an evolving research tool. The current implementation is intentionally file-based and small. The documentation describes the implementation in this repository; future knowledge management, publication, and agent features are explicitly out of scope until implemented.

## Attribution and license

Copyright 2026 Mstislav Maslennikov. Developed and maintained by Mstislav Maslennikov. Licensed under [Apache License 2.0](LICENSE) when the license file is present in the repository.


Originally developed to support research work of students at the Open Information Technologies Laboratory, Faculty of Computational Mathematics and Cybernetics, Lomonosov Moscow State University. It is maintained as an independent research software project.
