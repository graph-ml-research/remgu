# Changelog

## 0.3.0

- Added `ModelAdapter.get_architecture_dot()` and automatic best-effort detection for already-loaded PyTorch and TensorFlow/Keras modules; unsupported models return `None`.
- Added bounded `TopKSelector`-based diagnostic example selection and paginated HTML tables in reports and the live dashboard.
- Added the `monitor` extra with `psutil` and `pynvml`; GPU metrics no longer depend on shelling out to `nvidia-smi`.
- Added `param_types` (`hot`, `structural`, `view`) to `SimulationConfig` and improved dashboard controls, top resource strip, and progressive disclosure.
- Clarified static-result versus live-training dashboard workflows and strengthened HTML text escaping guidance.
- Added CLI commands to run controlled graph simulations, generate offline HTML reports, and start a loopback-only live dashboard.
- Added bounded-memory example selection and deterministic in-memory synthetic examples.
- Added dependency-free SVG renderers for graphs, metrics, DOT architecture subsets, and 2D embedding coordinates.
- Added framework-neutral architecture introspection and best-effort CPU/RAM/GPU resource monitoring.
- Added a static report with historical duration/peak resource summaries and separate diagnostic event rendering.
- Added an SSE dashboard with separate Probe diagnostics, bounded event history, and allowlisted optional hot-parameter/lifecycle controls.
- Escaped dynamic HTML text and used `textContent` for browser updates; restricted the server to loopback by default.
- Kept visualization, GPU monitoring, and model-framework integrations optional.
