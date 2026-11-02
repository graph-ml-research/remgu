# Simulation API: controlled graph-dependency experiments

The simulation package provides a small, dependency-free environment for testing hypotheses about graph structure and information availability. It is intentionally not a training framework and does not claim that synthetic results transfer directly to production data.

## Scenario: does a critical bridge carry the target signal?

### Motivation and hypothesis

Suppose a target label depends on a feature located in another graph community. If the communities are connected by a single bridge, removing that bridge should make the source feature unreachable. The experiment compares the same seeded world before and after this intervention.

The hypothesis is falsified for a particular run if the bridge is removed but its endpoints remain connected, or if the measured model behaviour does not match the expected dependency. Accuracy is a measured outcome, not a guarantee: if the source feature produces the negative class, the baseline's default prediction may remain correct after disconnection.

### Run through the Python API

```python
from remgu import (
    CriticalBridgeCheck,
    RemoveEdgeOperator,
    SimulationConfig,
    SimulationExperiment,
    SimulationRunner,
    PredictionAccuracyCheck,
)

config = SimulationConfig(
    experiment_id="critical-bridge",
    hypothesis="Removing the only bridge makes a positive remote signal unavailable.",
    seed=4,
    community_sizes=(5, 5),
    edge_probability=0.0,
)
runner = SimulationRunner(checks=[PredictionAccuracyCheck(), CriticalBridgeCheck()])
experiment = SimulationExperiment(config, runner)

baseline = experiment.run()
intervened = experiment.run([RemoveEdgeOperator((4, 5))])
print(baseline.metrics)
print(intervened.metrics)
print(intervened.checks)
```

The generator keeps each community internally connected with a chain, samples additional within-community edges according to `edge_probability`, and uses the designated bridge between communities. The default source is the last node; the default targets are nodes in the other community. The bridge endpoints `(4, 5)` match the example's community sizes.

### Expected result and interpretation

With the stated seed, the source feature is positive. The baseline can reach the source from all target nodes and achieves accuracy 1.0. After removing edge `(4, 5)`, the targets cannot reach the source, so the dependency baseline predicts its configured default and accuracy drops to 0.0. The critical-bridge check reports that the endpoints are disconnected.

The exact numbers depend on the seed and configuration. Reuse the same configuration and seed for a controlled comparison; otherwise graph and feature changes can confound the intervention.

### Operators and data transforms

Graph operators return a new world and do not mutate the input. `AddIsolatedNodesOperator` is useful for checking that irrelevant isolated nodes do not alter existing labels. `RemoveEdgeOperator` can remove the designated bridge while preserving metadata identifying which edge was intended to be critical.

`TransformPipeline` supports both finite-dataset transforms and lazy batch-by-batch transforms. The batch mode processes and yields one batch at a time; it does not materialize the complete stream. The random source must be explicitly supplied so the transform sequence is reproducible.

```python
from remgu import NumericNoiseTransform, RandomSource, TransformPipeline

pipeline = TransformPipeline([NumericNoiseTransform("feature", 0.05)], mode="batch")
batches = pipeline.transform_batches(training_batches, RandomSource(seed=21))
for batch in batches:
    train_step(batch)  # your existing training code
```

Replace `training_batches` and `train_step` with your data loader and training step. ReMgu does not implement model training itself.

### Recording the result in an existing research run

```python
from remgu import Experiment, Motivation, ResearchRunAdapter

experiment_log = Experiment("graph-study")
with experiment_log.run(
    "A critical bridge controls remote feature access",
    Motivation(type="new"),
) as run:
    ResearchRunAdapter().record(run, intervened)
```

The adapter records configuration and status in run parameters, metrics in `metrics.csv`, and a compact summary in `samples.jsonl`. It does not create or finalize the run and does not change the existing `.research` schema.

## Diagnostics and limitations

- `Probe` calls an adapter's optional `get_probe_data()` method. If the method is absent or returns `None`, the result explicitly says diagnostics are unavailable. It does not infer gradients or activations.
- `ModelIntervener` supports an explicit temporary attribute replacement and restoration record. It is not a universal neural-network intervention engine.
- The included baseline is a deliberately simple reachability rule, not a benchmark of modern GNN or Mamba architectures.
- Optional reporting and visualization tools are available without mandatory ML dependencies: `StaticHtmlReport`, `GraphRenderer`, `MetricRenderer`, `ArchitectureAdapter`, and `DotSvgRenderer`. The local `DashboardServer` uses SSE and binds to loopback by default. Resource monitoring is best-effort; unavailable measurements are represented as unavailable, not zero. The built-in DOT renderer supports a limited subset of Graphviz syntax.

## CLI: run, report, dashboard

```bash
research simulation run --seed 7 --nodes-per-community 8 --output result.json
research simulation report result.json --output report.html
research simulation dashboard result.json --port 8765
```

The static report is an offline HTML file. `research simulation dashboard result.json` displays the **saved result** and does not attach to a running or completed training process. For live monitoring, pass `DashboardServer` into the training loop and call `update_state()` with current metrics/resources and `publish_event()` for logs; updates are streamed to the browser over SSE. The server binds to loopback by default. Press Ctrl+C to stop it.

### Live training integration

```python
from remgu import DashboardServer

dashboard = DashboardServer({"status": "running"})
url = dashboard.start()
try:
    for epoch in range(num_epochs):
        train_one_epoch()
        dashboard.update_state({
            "status": "running",
            "main_metric_value": validation_accuracy,
            "metrics": {"loss": loss, "accuracy": validation_accuracy},
            "metric_history": {"loss": loss_history, "accuracy": accuracy_history},
            "live_resources": resource_monitor.sample(),
        })
        dashboard.publish_event({"type": "log", "message": f"epoch={epoch}"})
finally:
    dashboard.stop()
```

The example is illustrative: `train_one_epoch`, metric variables, and `resource_monitor` belong to the caller's training loop.

## Selecting and generating examples

```python
from remgu import ExampleSelectionService, SyntheticExampleGenerator

records = [
    {"example_id": "a", "correct": False, "confidence": 0.93},
    {"example_id": "b", "correct": True, "confidence": 0.99},
]
selected = ExampleSelectionService().select(records, "confident_errors", limit=5)
synthetic = SyntheticExampleGenerator().generate(4, seed=17)
```

Selection strategies validate the metadata they need. HTML reports and the live dashboard retain at most 100 ranked examples and paginate 10 rows at a time; the original sample source is not modified. Synthetic examples remain in memory and do not modify `samples.jsonl`.

## Static reports and renderers

```python
from remgu import StaticHtmlReport, GraphRenderer, MetricRenderer

report_path = StaticHtmlReport().render(result, "report.html", events=probe_events)
dot_text = GraphRenderer().to_dot(world)
metric_svg = MetricRenderer().render({"validation_accuracy": [0.61, 0.72, 0.79]})
```

All user-provided text (logs, errors, labels, and table cells) is passed through `html.escape()` before insertion into HTML; browser values are assigned using `textContent`, never `innerHTML`. Resource data is best-effort: a missing CPU/GPU/RAM measurement is `None`/“not measured”, not zero. The report uses historical duration and observed peak memory when available; live usage belongs to the server dashboard.

## Model architecture DOT contract

```python
from remgu import ArchitectureAdapter, DotSvgRenderer

class MyModelAdapter:
    def get_architecture_dot(self) -> str | None:
        return 'digraph Model { input [label="Input"]; input -> encoder; encoder -> output; }'

dot = ArchitectureAdapter().get_architecture_dot(MyModelAdapter())
if dot is not None:
    svg = DotSvgRenderer().render(dot)
```

The adapter returns DOT **text**, not an image. `DotSvgRenderer` implements a small, dependency-free DOT subset; it is not a replacement for full Graphviz. Unsupported DOT is reported rather than silently misrendered. `easydot`/`viz.js` can be added as optional alternatives if their API, license, and offline behavior are verified.

## Dashboard events and controls

`DashboardServer` exposes `/api/state`, an SSE stream at `/events`, and a local dashboard page. Publish diagnostic records with `publish_event`; events with type/category `probe` appear in the dedicated Probe panel. `ExperimentController` only exposes explicitly registered hot parameters and lifecycle callbacks. Hot parameters use a range slider plus Apply, structural parameters are marked as requiring restart, and view parameters stay client-side. Server-side validation is mandatory. Install monitoring with `pip install "remgu[monitor]"`; it uses `psutil` and `pynvml`, and unavailable measurements are `None`.

The built-in SVG renderers support bounded small/medium visualizations. `EmbeddingRenderer` draws already-projected 2D coordinates; it does not run PCA/t-SNE/UMAP. Projection and large-graph exploration remain the caller's responsibility. Framework-specific model introspection and gradients/activations are available only when an adapter explicitly implements them.

### Framework-specific architecture adapters

The optional adapters are duck-typed and do not import their target frameworks:

- `TorchArchitectureAdapter` reads a `named_modules()` hierarchy.
- `KerasArchitectureAdapter` shows the exposed `layers` collection in sequence order; it does not reconstruct arbitrary branched functional graphs.
- `CatBoostArchitectureAdapter` draws a bounded ensemble overview and marks omitted trees; it does not render individual split structures.
- `SpacyPipelineArchitectureAdapter` shows the ordered `pipe_names` chain.
- `Word2VecArchitectureAdapter` shows a conceptual token → embedding lookup → vector flow, not a neural layer graph.

Use `None` as the normal result when a model does not expose the required metadata. These adapters intentionally avoid framework imports and must not turn the corresponding packages into required dependencies.
