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
- Reports and visualization are available without installing ML frameworks as mandatory dependencies. By default, the dashboard is accessible only on the local machine. When a resource cannot be measured or a model diagram cannot be built, ReMgu indicates that the data is unavailable; the built-in architecture renderer supports only part of Graphviz DOT syntax.


## Reports and dashboard: choose a scenario

### 1. Run a hypothesis check and save the result

```bash
research simulation run --seed 7 --nodes-per-community 8 --output result.json
research simulation report result.json --output report.html
```

The first command runs an experiment with a fixed seed and saves its result. The second creates an HTML report that can be opened in a browser or shared. Keeping the seed fixed helps compare interventions without mixing their effects with random changes in the generated data.

### 2. Inspect a saved result in the browser

```bash
research simulation dashboard result.json --port 8765
```

Open the local URL printed by the command. The page can show metric charts, available resource measurements, selected examples, and graph/model previews when the corresponding data is present. This command displays the saved `result.json`; it does not attach itself to a running training process.

### 3. Watch your own training

The shortest option is to decorate your training function. ReMgu starts the local dashboard, samples available resources in the background, and stops the server even if training raises an exception.

```python
from remgu import DashboardServer

dashboard = DashboardServer()

@dashboard.track()
def train():
    print("Dashboard URL:", dashboard.url)
    for epoch in range(num_epochs):
        train_one_epoch()
        dashboard.log_metrics(loss=loss, accuracy=validation_accuracy)

train()
```

`train_one_epoch`, `loss`, and `validation_accuracy` are supplied by your own project. The only call needed to publish metrics is `log_metrics(...)`; you do not need to create a `ResourceMonitor`, assemble a state dictionary, or call `update_state()` yourself. Alternatively, use `with dashboard.run(): ...`; the server and resource sampling run inside the block and stop on exit. To provide metrics without calling `log_metrics`, pass a zero-argument `metrics` callback to `run()` or `track()`; it should return a dictionary of current values.

### What the page shows

- **Metric chart** shows how loss, accuracy, and other numeric values change during training. Loss often goes down and accuracy often goes up, but interpret them together and use the appropriate validation data.
- **CPU and RAM** show process load when the operating system permits measurement. GPU and VRAM appear when the relevant drivers and libraries are available. Missing measurements are shown as unavailable, not as zero.
- **Selected examples** help reveal where the model makes mistakes or behaves unusually.
- **Parameter slider** appears only for parameters that the experiment author explicitly connected to live control. This could be a learning rate; moving a slider does not automatically change an arbitrary Python variable. Parameters that require rebuilding the model or optimizer are marked as requiring a restart.
- **Logs** show messages and diagnostic events published by the training code.

### Example selection strategies

`ExampleSelectionService` supports `random` for a random sample; `top_k` for records with the largest `score` (or a different `score_key`); `errors` for incorrect predictions; `confident_errors` for incorrect predictions ranked from highest to lowest confidence; `correct_predictions` for correct predictions; `hard` for records with the largest `difficulty`; `rare_examples` for records with the smallest `frequency`; and `has_bridge` for records marked `has_bridge=True`.

For example, `confidence=0.93` means 93% confidence. The `confident_errors` strategy does **not** impose a 90% cutoff: it ranks incorrect predictions by confidence, so an error at 0.93 appears before an error at 0.4. `correct_predictions` requires `correct`; `confident_errors` requires `correct` and `confidence`; `hard` requires `difficulty`; `rare_examples` requires numeric `frequency`; and `has_bridge` requires `has_bridge`. Missing required fields produce a clear error.

### Enable CPU/RAM/GPU monitoring

```bash
pip install "remgu[monitor]"
```

This installation is optional; reports and the rest of the dashboard still work without it. Available measurements depend on the operating system, drivers, and installed libraries. By default, the dashboard listens only on your own computer.

### Additional Python tools

```python
from remgu import StaticHtmlReport, GraphRenderer, MetricRenderer

report_path = StaticHtmlReport().render(result, "report.html", events=probe_events)
dot_text = GraphRenderer().to_dot(world)
metric_svg = MetricRenderer().render({"validation_accuracy": [0.61, 0.72, 0.79]})
```

`StaticHtmlReport` creates a standalone report, `GraphRenderer` returns a graph description, and `MetricRenderer` creates an SVG chart from an existing metric history. These tools visualize supplied data; they do not train a model or calculate metrics on your behalf.

### Model architecture preview

```python
from remgu import ArchitectureAdapter, DotSvgRenderer

dot = ArchitectureAdapter().get_architecture_dot(model)
if dot is not None:
    svg = DotSvgRenderer().render(dot)
```

If a model is unsupported or does not expose enough metadata, the result is `None`. Adapters for PyTorch, Keras, CatBoost, spaCy, and Word2Vec use metadata already available on the object; they do not install or automatically import heavyweight ML frameworks. The diagram is an overview, not a guarantee that every internal computation is represented.
