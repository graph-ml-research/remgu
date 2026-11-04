# ReMgu

**English** | [Русский](README.ru.md)

Experiment lifecycle management for reproducible ML research.

ReMgu connects a research hypothesis to a concrete run, its metrics and diagnostic examples, and a written conclusion with the next step. It stores this record as ordinary files in `.research/`, so the history can be inspected, versioned, and reviewed without a tracking server.

> **Current scope:** run lifecycle, parameters, metrics, diagnostic samples, read-only consistency checks, controlled graph simulations, offline HTML reports, and an optional local live dashboard. Knowledge-base management and agent workflows are not implemented. Research snapshots, ZIP archives, Markdown exports, and static HTML sites are available through `research update`, `research archive`, `research export markdown`, and `research export site`.

## Start here

| What you want to do | Interface | Guide |
|---|---|---|
| Create a run before training | CLI | [CLI workflow](docs/en/cli.md#1-create-a-run) |
| Run existing training code and log results | Python API | [Python API](docs/en/python-api.md#minimal-training-example) |
| Record parameters, metrics, and diagnostic examples | Python API | [Run artifacts](docs/en/python-api.md#record-parameters-metrics-and-examples) |
| Review a completed run and record the conclusion | CLI | [CLI workflow](docs/en/cli.md#2-review-a-completed-run) |
| Inspect previous runs and the active run | CLI | [CLI workflow](docs/en/cli.md#3-inspect-run-history) |
| Find incomplete or inconsistent research records | CLI / API | [Consistency check](docs/en/consistency-check.md) |
| Build an in-memory research snapshot | CLI / API | [Research Snapshot](docs/en/research-snapshot.md) |
| Create a self-contained ZIP for a supervisor | CLI | [Research archive](docs/en/archive.md) |
| Publish a static HTML site | CLI | [Static site export](docs/en/static-site.md) |
| Run a controlled graph-dependency simulation and generate a report | CLI / Python API | [Simulation API](docs/en/simulation.md) |
| Understand the files ReMgu creates | Reference | [On-disk format](docs/en/data-format.md) |

## Choose your path

ReMgu has two independent workflows. You can use the research tracker without running any simulator:

```text
Real experiment (your data and training code)
Experiment + Run  →  .research/  →  review and share results

Optional synthetic sandbox (controlled test worlds)
SimulationExperiment + operators  →  result.json  →  HTML report
```

- **New to ReMgu?** Start with [Quick start](#quick-start), then run the [hello](examples/hello_remgu.py) example.
- **Want to test a controlled hypothesis?** Read [Simulation](docs/en/simulation.md).
- **Want to see graphs and examples in a browser?** Read [Reports and dashboard](#simulation-reports-and-dashboard).

The simulator is optional. You can use `Experiment` and `Run` for real data, text, images, tables, or any other ML task; ReMgu does not require a graph world.

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


## Installation

ReMgu requires Python 3.10 or newer.

### Option 1: Use ReMgu in your project code
If you want to import ReMgu in your training code (`from remgu import Experiment`), install the package into your project environment:

```bash
pip install remgu
```

The `research` command will then be available while you are inside that environment:

```bash
research --help
```

### Option 2: Use only the research command line

If you need ReMgu only as the `research` command (without importing it in code), install it via [pipx](https://pipx.pypa.io):

```bash
pipx install remgu
```

Pipx creates a dedicated environment for `remgu` and adds the `research` command to `PATH`.
The command will be available from any directory, without activating any environment.

```bash
research --help
```

Upgrade: `pipx upgrade remgu`.


## Quick start

From a checkout of this repository, install the dependency and create a run:

```bash
research new \
  --hypothesis "Increasing hidden_dim to 512 improves NDCG@20" \
  --motivation-type previous_run \
  --reference run-001
```

The command prints the new run ID. It creates `.research/` in the current directory unless `--base-path` is supplied. The reference above is illustrative: use an existing run ID, or omit `--reference` and use `--motivation-type new` for a new research direction.

In your training script:

```python
from remgu import Experiment, Motivation

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
research finish run-001 \
  --conclusion "NDCG@20 increased from 0.401 to 0.428 on the fixed validation set" \
  --next-step "Repeat with three random seeds"
```

Use the actual ID printed by `research new`; `run-001` is only an example. Full walkthroughs: [CLI](docs/en/cli.md) · [Python API](docs/en/python-api.md).

## Interfaces

### Command line

```bash
research --help
research new --help
research status
research previous --limit 10
research resume run-001
research finish run-001 --conclusion "..." --next-step "..."
research check
research update
research archive
research export markdown
research export site
```

The CLI defaults to `.research/`. Pass `--base-path /path/to/research-data` before the subcommand to use another directory.

### Python API

```python
from remgu import Experiment, Motivation, Run, ExampleProvider, TopKSelector
from remgu import SimulationExperiment, SimulationConfig, RemoveEdgeOperator
```

- `Experiment` opens the active run or creates one programmatically.
- `Run` tracks execution state and writes parameters, metrics, and diagnostic records.
- `Motivation` describes why a hypothesis is being tested.
- `TopKSelector` keeps the highest- or lowest-scoring diagnostic records in bounded memory.
- `ExampleSelector` merges named selection criteria and annotates why each example was selected.
- `ExampleProvider` defines how a stored example ID can be resolved to source data and a readable description.
- `SimulationExperiment` runs a controlled synthetic experiment; `SimulationConfig` fixes its settings and seed, while graph operators make explicit interventions.

See the [API guide](docs/en/python-api.md) for signatures and complete examples.

## First successful run

If you want to see what ReMgu does before adapting your own training script, run this example from the repository root:

```bash
python examples/hello_remgu.py
```

It simulates five training steps and creates a run under `.research/`. Open the printed run directory: `run.yaml` describes the hypothesis and status, `params.yaml` stores the settings, `metrics.csv` contains the loss history, and `samples.jsonl` stores optional diagnostic examples. These are ordinary text files; you can inspect them in an editor or open `metrics.csv` in a spreadsheet. The example does not train a real model.

### Tiny glossary

- **Hypothesis:** the claim you want to test.
- **Metric:** a number used to describe a result, such as loss or accuracy.
- **Baseline:** a simple reference method that tells you whether a more complex method helps.
- **Seed:** a number used to make random choices repeatable between runs.
- **Invariant:** a property expected to stay true after a controlled change, such as predictions not changing when irrelevant nodes are added.
- **Augmentation:** a controlled change or addition to training examples.

## Design principles

- **Research context stays with the run.** A run stores its hypothesis and motivation, not just a metric dump.
- **Ordinary training scripts stay ordinary.** ReMgu wraps the code you already run; it does not require a new training framework.
- **Files are the source of truth.** YAML, CSV, and JSONL are human-readable and easy to version or inspect.
- **Execution and review are separate.** A successful process is not the same thing as a scientifically reviewed result.
- **Research analysis is read-only.** `research check`, `research update`, `research archive`, `research export markdown`, and `research export site` do not rewrite the `.research` source data.


## Simulation, reports, and dashboard

Use these tools when you want to test a research hypothesis, save a result, inspect examples, or watch training in a browser. Start with the scenario that matches your goal:

- **Run a reproducible graph experiment:** `research simulation run --seed 7 --nodes-per-community 8 --output result.json`
- **Open a report:** `research simulation report result.json --output report.html` — creates a standalone HTML file.
- **Watch a saved result:** `research simulation dashboard result.json --port 8765` — then open the printed local URL. This shows the result already saved in `result.json`; it does not attach to a training process.
- **Watch training while it runs:** use `DashboardServer` with `with dashboard.run():` or `@dashboard.track()`. Resource sampling and server cleanup happen automatically. To show live loss/accuracy, pass a small metrics callback or call `dashboard.log_metrics(loss=..., accuracy=...)` after each epoch.

A live dashboard shows metric history, available CPU/RAM/GPU measurements, selected examples, graph/model previews, logs, and any controls explicitly configured by the experiment. A slider is shown only for a parameter that the training code has registered as changeable during training.

```python
from remgu import DashboardServer

dashboard = DashboardServer()

@dashboard.track()
def train():
    for epoch in range(num_epochs):
        train_one_epoch()
        dashboard.log_metrics(loss=loss, accuracy=validation_accuracy)

train()  # opens the dashboard while training and closes it afterwards
```

For CPU/RAM/GPU monitoring, install the optional dependencies with `pip install "remgu[monitor]"`. Metrics unavailable on the current machine are shown as unavailable, not as zero. The dashboard runs locally by default. See the [simulation and visualization guide](docs/en/simulation.md) for complete examples and interpretation notes.

## Documentation

- [CLI workflows](docs/en/cli.md)
- [Python API](docs/en/python-api.md)
- [Consistency checks](docs/en/consistency-check.md)
- [Research Snapshot](docs/en/research-snapshot.md)
- [Research archive](docs/en/archive.md)
- [Markdown export](docs/en/markdown-export.md)
- [Static site export](docs/en/static-site.md)
- [On-disk data format](docs/en/data-format.md)
- [Architecture and boundaries](docs/en/architecture.md)
- [Controlled simulation API](docs/en/simulation.md)
- [Russian documentation](README.ru.md)

## Development status

ReMgu is an evolving research tool. The current implementation is intentionally file-based and small. The dependency-free simulation package supports a basic graph-dependency scenario, graph interventions, reproducible transforms, and optional diagnostic contracts. Browser visualization, standalone HTML reports, a live dashboard, selected examples, optional resource monitoring, and framework-specific model previews are available. The DOT renderer intentionally supports a safe subset of Graphviz.

## Attribution and license

Copyright 2026 Mstislav Maslennikov. Developed and maintained by Mstislav Maslennikov. Licensed under [Apache License 2.0](LICENSE).

Originally developed to support research work of students at the Open Information Technologies Laboratory, Faculty of Computational Mathematics and Cybernetics, Lomonosov Moscow State University. It is maintained as an independent research software project.
