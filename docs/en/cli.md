# CLI workflows

[English](../../README.md) | [Русский](../ru/cli.md)

Run commands from the repository root. In this checkout, invoke the CLI as `research`. The default data directory is `.research/` under the current working directory.

## 1. Create a run

```bash
research new \
  --hypothesis "Increasing hidden_dim to 512 improves NDCG@20" \
  --motivation-type previous_run \
  --reference run-001
```

**Purpose.** Record the question being tested before training starts, and connect it to the prior run that motivated it.

**Arguments.** `--hypothesis` is required. `--motivation-type` defaults to `new`; use a descriptive value such as `previous_run` or `literature_citation`. `--reference` is an optional run/paper identifier; when using `previous_run`, provide the prior run ID.

**Expected result.** The command prints a new ID, e.g. `run-002`, creates `runs/run-002/run.yaml`, and writes the active-run pointer to `.research/active`. Only one active run is allowed at a time.

For a new research direction:

```bash
research new --hypothesis "Random-walk ordering improves graph sequence quality" --motivation-type new
```

## 2. Review a completed run

After training code exits normally, the API marks the run `completed`. Record the scientific interpretation separately:

```bash
research finish run-001 \
  --conclusion "NDCG@20 increased from 0.401 to 0.428 on the fixed validation set" \
  --next-step "Repeat with three random seeds"
```

Both `--conclusion` and `--next-step` are required. Review is allowed only for a completed run, and a reviewed run cannot be reviewed again through this command.

**Expected result.** `review.status` becomes `reviewed`; the conclusion and next step are persisted in `run.yaml`. Execution status is not changed by review.

If the active run is the one to review, the ID can be omitted:

```bash
research finish --conclusion "..." --next-step "..."
```

## 3. Inspect run history

Show the active run and both lifecycle states:

```bash
research status
```

List the latest runs (the displayed subset is ordered oldest first):

```bash
research previous --limit 10
```

Example output:

```text
run-001 | execution=completed | review=reviewed | motivation=new | hypothesis=Baseline with degree sorting
run-002 | execution=completed | review=needs_review | motivation=previous_run -> run-001 | hypothesis=Replace degree sorting with random walks
```

This is a compact summary, not a replacement for opening each run's `run.yaml` and artifacts.

## 4. Resume an interrupted workflow

If a run is still `running` but the active pointer is missing, restore it:

```bash
research resume run-002
```

Only a run with execution status `running` can be resumed. `resume` does not restart Python training or restore a process; it restores ReMgu's active-run pointer so a subsequent `Experiment.run()` can reopen the persisted run.

## 5. Check research records

```bash
research check
```

The command reports counts of completed runs and runs with non-empty hypotheses, then lists consistency issues. It is read-only; see [Consistency checks](consistency-check.md).


## 6. Build a research snapshot

```bash
research update
```

`research update` rebuilds the in-memory `ResearchSnapshot`, runs consistency analysis, and prints execution/review counts and findings. It does not modify `.research/`. See [Research Snapshot](research-snapshot.md).

## 7. Create a research archive

```bash
research archive
research archive --output ./reports/research-archive.zip
```

The command publishes a self-contained ZIP containing a README, compact report, research metadata, existing run artifacts, and compact diagnostic examples. Original datasets are not copied. Existing output files are rejected rather than overwritten. See [Research archive](archive.md).

## 8. Export a Markdown report

```bash
research export markdown
research export markdown --output ./reports/research.md
```

The command builds a `ResearchSnapshot` and renders a standalone `research.md` document with run history, relations, metrics, compact samples, consistency findings, and recorded conclusions. It does not modify `.research/`, run ML, or call an LLM. Existing output files are rejected rather than overwritten. See [Markdown export](markdown-export.md).

## 9. Store data elsewhere

Pass `--base-path` before the subcommand:

```bash
research --base-path ./research-data new --hypothesis "H1" --motivation-type new
research --base-path ./research-data status
```

The directory contains `runs/` and, while a run is active, an `active` file.

## Lifecycle rules to remember

- `research new` refuses to create a second active run.
- A run starts with execution status `running` and review status `needs_review`.
- Normal exit from `with experiment.run()` completes a running run; an uncaught exception marks it `failed`.
- A run may also be explicitly marked `aborted` via the API.
- `research finish` records a review; it does not finish execution.
- `research check` never edits run data.


## 10. Export a static site

```bash
research export site
research export site --output ./reports/site
```

The command builds a `ResearchSnapshot` and generates a static HTML site with `index.html`, one page per run under `runs/`, an examples catalogue under `examples/`, and a shared `style.css`. It uses no backend, framework, or JavaScript. The destination directory must not already exist. The output can be opened locally or hosted later on a static hosting service; deployment is not part of ReMgu. See [Static site export](static-site.md).

### Optional example descriptions

Both Markdown and site export can enrich compact examples through an application-provided `ExampleProvider`:

```bash
research export site --describe-examples --example-provider my_project.examples:MyExampleProvider
research export markdown --describe-examples --example-provider my_project.examples:MyExampleProvider
```

The provider class must be importable and constructible without arguments; configure it from environment/configuration in its constructor. `describe(example_id)` should be cheap and concise. Descriptions are transient snapshot fields, not changes to stored `samples.jsonl`. If no provider is supplied, exports keep the original compact records.

