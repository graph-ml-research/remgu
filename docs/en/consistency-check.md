# Consistency check

[English](../../README.md) | [Русский](../ru/consistency-check.md)

## Why it exists

Research records tend to become incomplete when experiments fail, a review is postponed, or metadata is edited by hand. `research check` identifies common problems without preventing normal runs and without modifying files.

## Run it

```bash
python -m research.cli check
```

The checker reads every `runs/<run-id>/run.yaml` it can find, including records for `running`, `failed`, and `aborted` executions. It reports:

- number of completed runs;
- number of runs with a non-empty hypothesis;
- missing or empty research/execution/review sections;
- missing hypotheses or weak motivations;
- motivation references to unknown run IDs;
- completed runs without conclusions;
- invalid execution/review statuses and incompatible review states;
- unreadable YAML or an invalid top-level structure.

Example output (illustrative):

```text
completed runs: 4
runs with hypotheses: 6
issues:
  warning: run-002: missing_conclusion: completed run has no conclusion
  warning: run-005: weak_motivation: previous_run motivation has no reference
```

Exact messages depend on the records on disk.

## Read-only guarantee

The checker reads raw YAML instead of constructing `Run` objects, so malformed metadata can be reported without aborting the entire check. It does not rewrite `run.yaml`, update `active`, or change execution/review statuses. Fix reported issues manually, then run the check again.

## Python usage

```python
from research.consistency import check_consistency
from research.storage import FileStorage

storage = FileStorage(".research")
report = check_consistency(storage)

print(report.ok)
print(report.completed_runs)
print(report.runs_with_hypotheses)
for issue in report.issues:
    print(issue.severity, issue.run_id, issue.code, issue.message)
```

`report.ok` is true only when no issues were found. `ConsistencyIssue` contains `run_id`, machine-readable `code`, human-readable `message`, and `severity` (`warning` by default; structural errors use `error`). This is a diagnostic report, not an automatic repair tool.

## Interpreting the result

A clean consistency report does not prove that a hypothesis is scientifically sound or that a metric is statistically significant. It only checks the structural and workflow-level rules implemented by REMgu. Scientific interpretation remains the responsibility of the researcher.
