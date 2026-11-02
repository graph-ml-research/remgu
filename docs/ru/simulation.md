# API симулятора: контролируемые эксперименты с графовой зависимостью

Пакет симуляции предоставляет небольшую среду без новых обязательных зависимостей для проверки гипотез о структуре графа и доступности информации. Это не фреймворк обучения моделей; результаты на синтетических данных не гарантируют перенос на production.

## Сценарий: несёт ли критический мост целевой сигнал?

### Мотивация и гипотеза

Пусть метка целевой вершины зависит от признака, находящегося в другом сообществе графа. Если сообщества соединены единственным мостом, его удаление должно сделать исходный признак недостижимым. Сравним один и тот же граф с фиксированным seed до и после вмешательства.

Гипотеза для конкретного запуска не подтверждается, если мост удалён, но его концы остаются связными, либо если измеренное поведение модели не соответствует ожидаемой зависимости. Accuracy — измеряемый результат, а не гарантия: если исходный признак соответствует отрицательному классу, предсказание по умолчанию может остаться правильным и после разрыва связи.

### Запуск через Python API

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
    hypothesis="Удаление единственного моста делает положительный удалённый сигнал недоступным.",
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

Генератор обеспечивает связность внутри каждого сообщества цепочкой, добавляет внутренние рёбра с вероятностью `edge_probability` и соединяет сообщества заданным мостом. По умолчанию источник сигнала — последняя вершина, а целевые вершины находятся в другом сообществе. В примере ребро `(4, 5)` соответствует размерам сообществ `(5, 5)`.

### Ожидаемый результат и интерпретация

Для указанного seed признак источника положительный. В baseline источник достижим из всех целевых вершин, accuracy равна 1.0. После удаления ребра `(4, 5)` целевые вершины не могут достичь источника, baseline выдаёт предсказание по умолчанию, и accuracy падает до 0.0. Проверка критического моста сообщает, что его концы разъединены.

Точные числа зависят от seed и конфигурации. Для контролируемого сравнения используйте одну и ту же конфигурацию и seed; иначе изменения графа и признаков могут смешаться с эффектом вмешательства.

### Операторы графа и преобразования данных

Графовые операторы возвращают новый мир и не изменяют входной объект. `AddIsolatedNodesOperator` позволяет проверять, что добавление несущественных изолированных вершин не меняет метки исходных вершин. `RemoveEdgeOperator` может удалить заданный мост, сохранив метаданные о том, какое ребро было критическим.

`TransformPipeline` поддерживает преобразование конечного датасета и ленивое преобразование батчей по мере поступления. Режим `batch` обрабатывает и выдаёт по одному батчу, не материализуя весь поток. Источник случайности передаётся явно, чтобы обеспечить воспроизводимость.

```python
from remgu import NumericNoiseTransform, RandomSource, TransformPipeline

pipeline = TransformPipeline([NumericNoiseTransform("feature", 0.05)], mode="batch")
batches = pipeline.transform_batches(training_batches, RandomSource(seed=21))
for batch in batches:
    train_step(batch)  # существующий код обучения
```

Замените `training_batches` и `train_step` своим загрузчиком данных и шагом обучения. Само обучение ReMgu не реализует.

### Сохранение результата в существующем research-запуске

```python
from remgu import Experiment, Motivation, ResearchRunAdapter

research_experiment = Experiment("graph-study")
with research_experiment.run(
    "Критический мост управляет доступом к удалённому признаку",
    Motivation(type="new"),
) as run:
    ResearchRunAdapter().record(run, intervened)
```

Адаптер сохраняет конфигурацию и статус в параметрах запуска, метрики — в `metrics.csv`, а краткую сводку — в `samples.jsonl`. Он не создаёт и не завершает запуск и не меняет существующую схему `.research`.

## Диагностика и ограничения

- `Probe` вызывает необязательный метод адаптера `get_probe_data()`. Если метода нет или он возвращает `None`, результат явно указывает, что диагностика недоступна. Градиенты и активации автоматически не выводятся.
- `ModelIntervener` поддерживает явную временную замену существующего атрибута с записью для восстановления. Это не универсальный механизм вмешательства в нейросети.
- Включённый baseline — простое правило достижимости, а не бенчмарк современных GNN или Mamba-архитектур.
- CLI симулятора, браузерный UI и live-дашборд доступны; они остаются лёгкими необязательными компонентами. GPU-профилирование зависит от `remgu[monitor]`; спектральный генератор графов не входит в текущую версию.


- Доступны необязательные средства отчётности и визуализации без обязательных ML-зависимостей: `StaticHtmlReport`, `GraphRenderer`, `MetricRenderer`, `ArchitectureAdapter` и `DotSvgRenderer`. `DashboardServer` использует SSE и по умолчанию слушает только loopback. Мониторинг ресурсов работает по принципу best effort; недоступные измерения не подменяются нулём. Встроенный рендерер поддерживает лишь подмножество синтаксиса Graphviz DOT.

## CLI: запуск, отчёт и дашборд

```bash
research simulation run --seed 7 --nodes-per-community 8 --output result.json
research simulation report result.json --output report.html
research simulation dashboard result.json --port 8765
```

Статический отчёт — автономный HTML-файл. Команда `research simulation dashboard result.json` показывает **сохранённый результат** и не подключается автоматически к завершённому или другому обучению. Для Live View передавайте экземпляр `DashboardServer` в цикл обучения и вызывайте `update_state()` с текущими метриками/ресурсами и `publish_event()` для логов; эти обновления доставляются в браузер через SSE. Сервер по умолчанию доступен только через loopback. Для остановки нажмите Ctrl+C.

### Подключение к работающему обучению

```python
from remgu import DashboardServer, ResourceMonitor

dashboard = DashboardServer({"status": "running"})
resource_monitor = ResourceMonitor()
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

Пример иллюстративный: `train_one_epoch`, метрики и их истории принадлежат вызывающему циклу обучения. CLI-команда с `result.json` не подключается к такому циклу автоматически.

## Отбор и генерация примеров

```python
from remgu import ExampleSelectionService, SyntheticExampleGenerator

records = [
    {"example_id": "a", "correct": False, "confidence": 0.93},
    {"example_id": "b", "correct": True, "confidence": 0.99},
]
selected = ExampleSelectionService().select(records, "confident_errors", limit=5)
synthetic = SyntheticExampleGenerator().generate(4, seed=17)
```

Стратегии отбора проверяют наличие необходимых метаданных. HTML-отчёт и live-дашборд сохраняют не более 100 отобранных примеров и показывают по 10 строк на странице; исходная выборка не изменяется. Синтетические примеры остаются в памяти и не меняют `samples.jsonl`.

## Статические отчёты и визуализаторы

```python
from remgu import StaticHtmlReport, GraphRenderer, MetricRenderer

report_path = StaticHtmlReport().render(result, "report.html", events=probe_events)
dot_text = GraphRenderer().to_dot(world)
metric_svg = MetricRenderer().render({"validation_accuracy": [0.61, 0.72, 0.79]})
```

Весь пользовательский текст (логи, ошибки, подписи и ячейки таблиц) проходит через `html.escape()` перед вставкой в HTML; динамические значения в браузере назначаются через `textContent`, а не `innerHTML`. Измерения ресурсов работают по принципу best effort: отсутствующая метрика CPU/GPU/RAM обозначается как `None`/«не измерялась», а не ноль. В отчёт попадают длительность и наблюдавшийся пик памяти, если они доступны; текущая загрузка относится к серверному дашборду.

## Контракт архитектуры модели: DOT

```python
from remgu import ArchitectureAdapter, DotSvgRenderer

class MyModelAdapter:
    def get_architecture_dot(self) -> str | None:
        return 'digraph Model { input [label="Input"]; input -> encoder; encoder -> output; }'

dot = ArchitectureAdapter().get_architecture_dot(MyModelAdapter())
if dot is not None:
    svg = DotSvgRenderer().render(dot)
```

Адаптер возвращает **текст DOT**, а не изображение. `DotSvgRenderer` поддерживает небольшое подмножество DOT без внешних зависимостей и не заменяет полноценный Graphviz. Неподдерживаемый DOT приводит к явному сообщению, а не к молчаливому искажению схемы. `easydot`/`viz.js` можно добавить как необязательные альтернативы после проверки API, лицензии и автономной работы.

## События и управление в дашборде

`DashboardServer` предоставляет страницу, `/api/state` и SSE-поток `/events`. Диагностические события публикуются через `publish_event`; события с типом/категорией `probe` показываются в отдельной панели Probe. `ExperimentController` разрешает только явно зарегистрированные hot-параметры и callbacks управления. `hot` показываются ползунком с кнопкой Apply, `structural` помечаются предупреждением о перезапуске, а `view` меняют только отображение на клиенте. Серверная валидация обязательна; отключение браузера не останавливает обучение. Для мониторинга установите `pip install "remgu[monitor]"`; используются `psutil` и `pynvml`, а недоступные измерения возвращаются как `None`.

Встроенные SVG-визуализаторы предназначены для ограниченных по размеру представлений. `EmbeddingRenderer` рисует уже спроецированные 2D-координаты, но не запускает PCA/t-SNE/UMAP. Проекция эмбеддингов и исследование больших графов остаются ответственностью вызывающего кода. Интроспекция архитектуры, градиенты и активации доступны только при явной поддержке соответствующего адаптера.

### Архитектурные адаптеры для конкретных типов моделей

Необязательные адаптеры используют duck typing и не импортируют целевые ML-фреймворки. `ArchitectureAdapter` автоматически проверяет только уже загруженные модули в `sys.modules`; ошибки интроспекции превращаются в `None`. `ModelAdapter.get_architecture_dot() -> str | None` — необязательный контракт:

- `TorchArchitectureAdapter` читает иерархию `named_modules()`.
- `KerasArchitectureAdapter` показывает коллекцию `layers` в последовательном порядке; он не восстанавливает произвольный ветвящийся граф Functional API.
- `CatBoostArchitectureAdapter` строит ограниченную сводку ансамбля и отмечает пропущенные деревья; внутренние split-структуры деревьев не отображаются.
- `SpacyPipelineArchitectureAdapter` показывает последовательность `pipe_names`.
- `Word2VecArchitectureAdapter` показывает концептуальный поток «токен → поиск embedding → вектор», а не обычный граф нейросетевых слоёв.

Если модель не предоставляет нужные метаданные, штатный результат — `None`. Адаптеры намеренно не импортируют фреймворки и не делают их обязательными зависимостями.
