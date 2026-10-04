# Research consistency and publication layer

This layer sits above the REMgu core run lifecycle. It reads persisted `run.yaml` files and produces analysis; it does not mutate runs and does not participate in experiment execution.

## Boundary

```text
REMgu core
  runs / run.yaml / params / metrics / samples
             |
             v
Research consistency/publication layer
  check -> snapshot -> update -> archive/export (future)
```

The core owns execution state and run persistence. The research layer owns cross-run interpretation, consistency checks, snapshots, and future publication/export views.

## Current command

```bash
research check
```

`research check` is read-only. It reports:

- number of completed runs;
- number of runs containing a non-empty hypothesis;
- weak or missing motivations;
- missing conclusions for completed runs;
- broken run references;
- invalid lifecycle/status combinations and malformed `run.yaml` structures.

Failed and aborted runs are included in the scan and do not require a conclusion merely because they are terminal.

The checker reads raw YAML rather than constructing `Run` objects so that one malformed run can be reported without preventing analysis of the remaining runs.

## Future `research update`

Do not implement yet. The intended boundary is:

```text
runs + metrics + samples
          |
          v
   Research Snapshot
          |
          +--> future archive
          +--> future markdown export
          +--> future static site
```

`research update` should eventually rebuild a derived `ResearchSnapshot` from the current source files. It should not become a second persistence system for experiment execution.
