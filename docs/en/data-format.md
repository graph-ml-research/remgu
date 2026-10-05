# On-disk data format

[English](../../README.md) | [Русский](../ru/data-format.md)

By default, ReMgu writes to `.research/` relative to the current working directory:

```text
.research/
├── active                  # ID of the current active run; absent otherwise
└── runs/
    ├── run-001/
    │   ├── run.yaml        # hypothesis, motivation, execution, review
    │   ├── params.yaml     # effective configuration snapshot (created on first log_params)
    │   ├── metrics.csv     # appended metric records (created on first metric)
    │   └── samples.jsonl   # compact diagnostic records (created on first collect)
    └── run-002/
        └── run.yaml
```

Optional artifact files are created lazily. A run does not need to contain all three artifacts.

## `run.yaml`

```yaml
run_id: run-003
research:
  hypothesis: "Increasing hidden_dim to 512 improves NDCG@20."
  motivation:
    type: previous_run
    reference: run-002
execution:
  status: completed
  started_at: "2026-09-19T00:00:00Z"
  finished_at: "2026-09-19T01:00:00Z"
  error: null
review:
  status: needs_review
  conclusion: null
  next_step: null
```

The example illustrates the schema; timestamps and values must describe the actual run. Execution status is one of `running`, `completed`, `failed`, or `aborted`. Review status is `needs_review` or `reviewed`.

### Lifecycle distinction

Execution answers **what happened when the code ran?** Review answers **what do we conclude, and what should we do next?** A completed execution can remain `needs_review` until a researcher records a conclusion and next step.

## Artifacts

- `params.yaml`: mapping of effective run parameters. Repeated `log_params` calls merge keys; later values replace earlier values for the same key.
- `metrics.csv`: append-only rows with `step`, `metric_name`, and `metric_value`. It can contain repeated metric names at different steps.
- `samples.jsonl`: one compact JSON object per line, typically keyed by `example_id`. It should point to source examples rather than duplicate large records or datasets.

## Active pointer and IDs

The `active` file contains one run ID, such as `run-003`. IDs are allocated by incrementing the largest numeric suffix found in the runs directory and formatted with at least three digits. The pointer is removed when a run completes, fails, or is aborted.

## Version control

These are ordinary text files and can be committed alongside the experiment code. Decide separately whether large or sensitive diagnostic fields should be committed; ReMgu does not anonymize or filter collected records automatically. Do not store credentials, personal data, or full private datasets in the research directory without an explicit data-handling policy.
