# Markdown export

[English](markdown-export.md) | [Русский](../ru/markdown-export.md)

`research export markdown` publishes the current in-memory `ResearchSnapshot` as one standalone Markdown report. It requires no website, server, or external service.

## Usage

```bash
research export markdown
research export markdown --output ./reports/research.md
```

The default output is `research.md` in the current working directory. Existing files are never overwritten implicitly; choose another output path if the destination already exists.

When using a non-default research directory, place the global option before the command:

```bash
research --base-path ./research-data export markdown --output ./reports/research.md
```

## Report sections

- **Summary** — total, completed, failed, aborted, and running runs, plus review counts.
- **Research history** — runs in snapshot order, including hypothesis, motivation/reference, execution and review status, timestamps, parameters, metrics, and recorded conclusion/next step.
- **Relations** — existing `motivation.reference` links only.
- **Collected examples** — compact sample records from `samples.jsonl`, not source datasets.
- **Consistency** — warnings and errors from the snapshot's consistency analysis.
- **Conclusions** — only conclusions and next steps already recorded in run review data.

## Architecture and guarantees

The CLI builds a `ResearchSnapshot` and passes it to `MarkdownAdapter`. The adapter only renders the supplied snapshot; it does not read `.research`, execute ML code, call an LLM, or infer scientific conclusions. Snapshot construction reads the existing research store, and neither the builder nor the adapter changes run records.

The Markdown file is a publication artifact, not a new source-of-truth format. Parameters and sample records are shown as readable text; large datasets and domain-specific objects are not loaded or embedded.
