# Research archive

[English](archive.md) | [Русский](../ru/archive.md)

`research archive` is the first ReMgu publication adapter. It creates a self-contained ZIP that can be uploaded to a task tracker or sent to a supervisor without a ReMgu service.

## Usage

```bash
research archive
```

By default the command creates `research-archive.zip` in the current directory. A different destination can be selected with:

```bash
research archive --output ./reports/run-2026-10-07.zip
```

An existing output file is never overwritten implicitly; the command fails and asks you to choose another path.

## Archive structure

```text
research-archive/
├── README.md
├── report.md
├── research.yaml
├── runs/
│   └── run-001/
│       ├── run.yaml
│       ├── params.yaml
│       ├── metrics.csv
│       └── samples.jsonl
└── examples/
    └── node-42.json
```

Optional files are included only when they exist in the source run. `examples/` is populated only for compact sample records containing an `example_id`.

## What is published

- `README.md` explains the archive and its contents.
- `report.md` is a compact automatically generated summary.
- `research.yaml` contains machine-readable summary, existing relations and consistency findings.
- `runs/` contains copies of the known ReMgu artifacts.
- `examples/` contains compact diagnostic records when they can be represented as JSON.

The adapter does not copy original datasets, graph objects, model checkpoints, or other large objects that ReMgu does not know how to serialize.

## Source of truth and safety

The `.research/` directory remains the source of truth. Archive creation is read-only with respect to the research store. The ZIP is a publication artifact and is not intended to be edited and imported back into ReMgu.

The report never invents scientific conclusions. Conclusions and next steps are rendered only when they are already present in run review data.
