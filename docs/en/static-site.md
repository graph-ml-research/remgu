# Static site export

[English](static-site.md) | [Русский](../ru/static-site.md)

`research export site` publishes a `ResearchSnapshot` as a static HTML site. The output can be opened from the local filesystem and can later be hosted on GitHub Pages or another static host. ReMgu does not deploy it.

## Usage

```bash
research export site
research export site --output ./reports/site
research --base-path ./research-data export site --output ./reports/site
```

The default destination is `site/` in the current working directory. The destination directory must not already exist; existing sites are never overwritten implicitly.

## Generated files

```text
site/
├── index.html
├── style.css
├── runs/
│   ├── run-001.html
│   └── ...
└── examples/
    └── index.html
```

The home page contains run counts, chronological research history, recorded conclusions and next steps, and consistency findings. Each run page contains its hypothesis, motivation/reference, execution and review state, timestamps, parameters, metrics, and compact samples. If the snapshot was built with an `ExampleProvider` and `describe_examples=True`, a short human-readable description appears before each sample record.

## Architecture and guarantees

The CLI builds a `ResearchSnapshot` and passes it to `StaticSiteAdapter`. The adapter only renders the supplied snapshot; it does not read `.research`, access `Run` instances, run ML, call an LLM, or infer scientific conclusions. The generated site uses plain HTML and CSS, with no backend, JavaScript framework, or JavaScript runtime requirement. Dynamic text is HTML-escaped. The export does not modify research data.
