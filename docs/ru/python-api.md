# Python API: использование ReMgu в коде обучения

[English](../en/python-api.md) | [Русский](../../README.ru.md)

API намеренно тонкий: существующий training loop остаётся на месте, а `Experiment` предоставляет объект `Run`. Метаданные запуска хранятся отдельно от параметров, метрик и выбранных диагностических примеров.

## Минимальный пример обучения

Сначала создайте запуск через CLI:

```bash
research new --hypothesis "hidden_dim=512 improves NDCG@20" --motivation-type new
```

Затем используйте активный запуск в скрипте обучения:

```python
from remgu import Experiment

experiment = Experiment("graph-mamba")
with experiment.run() as run:
    run.log_params({
        "hidden_dim": 512,
        "learning_rate": 1e-3,
        "seed": 42,
    })

    for epoch in range(10):
        # Замените на реальное обучение и оценку.
        ndcg_at_20 = train_and_evaluate(epoch)
        run.log_metric("ndcg_at_20", ndcg_at_20, step=epoch)
```

`train_and_evaluate` — функция вашего проекта, а не функция ReMgu. Пример показывает, куда добавить инструментирование.

### Создание запуска напрямую через API

Используйте этот вариант, если запуском должен управлять Python, а не CLI:

```python
from remgu import Experiment, Motivation

experiment = Experiment("graph-mamba", base_path=".research")
with experiment.run(
    hypothesis="Random-walk ordering improves graph sequence quality",
    motivation=Motivation(type="literature_citation", reference="paper-2402.00789"),
) as run:
    run.log_metric("validation_auc", 0.8263, step=1)
```

`hypothesis` и `motivation` должны передаваться вместе. Вызов `experiment.run()` без аргументов открывает активный запуск и не создаёт новый. Если активного запуска нет, возникает `RuntimeError` с указанием сначала выполнить `research new`.

## Запись параметров, метрик и примеров

### Параметры

```python
run.log_params({"hidden_dim": 512, "dropout": 0.1})
run.log_params({"dropout": 0.2})  # заменяет сохранённое значение dropout
```

Параметры сохраняются в `params.yaml`. Повторные вызовы объединяют переданные ключи с существующим словарём; повторно переданный ключ перезаписывается. Записывайте фактическую конфигурацию запуска, а не только те значения, которые планировали передать.

### Метрики

```python
run.log_metric("loss", 0.42, step=10)
run.log_metrics({"auc": 0.8263, "f1": 0.74}, step=10)
```

Каждый вызов добавляет строки в `metrics.csv`. Столбцы: `step`, `metric_name`, `metric_value`; шаг необязателен. Повторение имён метрик допустимо: это временной ряд, а не словарь.

### Диагностические примеры

```python
run.collect({
    "example_id": "node-104",
    "prediction": 0.12,
    "baseline_prediction": 0.83,
    "diagnostic": "large_regression",
})
```

Каждый вызов добавляет один JSON-объект в `samples.jsonl`. Сохраняйте компактные ссылки и диагностические признаки, а не полную копию датасета. Приложение может позднее восстановить исходные данные по `example_id`.

## Отбор примеров через TopKSelector

`TopKSelector` хранит не более `k` записей, поэтому не требуется держать в памяти весь validation set.

```python
from remgu import TopKSelector

largest_regressions = TopKSelector(
    k=20,
    key=lambda row: row["baseline_score"] - row["score"],
    name="largest_regression",
)

for row in validation_records:
    largest_regressions.consider(row)

for row in largest_regressions.records():
    run.collect(row)
```

Функция `key` вычисляет оценку отбора. По умолчанию сохраняются наибольшие значения; `largest=False` переключает отбор на наименьшие. Вместо `key` можно передавать оценку в `consider(record, priority)` или `consider(record, score=...)`.

## Объединение критериев через ExampleSelector

```python
from remgu import ExampleSelector, TopKSelector

selectors = ExampleSelector([
    TopKSelector(k=10, key=lambda row: row["score"], largest=False, name="lowest_score"),
    TopKSelector(k=10, key=lambda row: row["regression"], name="largest_regression"),
])

for row in validation_records:
    selectors.consider(row)

for row in selectors.records():
    run.collect(row)
```

В результате каждый `example_id` присутствует один раз. В `selection.reasons` перечислены все селекторы, выбравшие пример; в `selection.scores` записаны оценки для селекторов, настроенных через `key`.

## Получение данных по ID через ExampleProvider

`ExampleProvider` — `Protocol` для доступа к данным конкретного проекта. Реализуйте `get(example_id)` для загрузки исходного примера или облегчённого контекста и `describe(example_id)` для человекочитаемого описания. ReMgu не навязывает датасет, базу данных или способ хранения.

```python
from typing import Any

from remgu import ExampleProvider

class MyExampleProvider:
    def get(self, example_id: str) -> Any:
        return dataset.lookup(example_id)

    def describe(self, example_id: str) -> str:
        row = dataset.lookup(example_id)
        return f"label={row['label']}, source={row['source']}"
```

`dataset.lookup` — условный метод вашего проекта. Provider задаёт интерфейс; текущая версия автоматически его не создаёт и не сохраняет.

## Жизненный цикл и исключения

```python
with experiment.run() as run:
    run.log_metric("loss", 0.42)
```

- При нормальном выходе всё ещё выполняющийся запуск получает статус `completed`, а указатель активного запуска удаляется.
- Если из блока выходит исключение, запуск получает статус `failed`; тип и сообщение исключения сохраняются, само исключение продолжает распространяться.
- Для явной отмены вызовите `run.abort()`.
- Методы записи артефактов запрещают изменения после выхода запуска из состояния `running`.
- `research finish` — отдельный этап разбора, сохраняющий `conclusion` и `next_step`.

## Сводка публичного API

```python
from remgu import (
    Experiment,
    Motivation,
    Run,
    ExampleProvider,
    TopKSelector,
    ExampleSelector,
)
```

Эти символы экспортируются пакетом. Низкоуровневый `FileStorage` и типы отчёта о согласованности можно импортировать из соответствующих модулей, но они не входят в верхнеуровневый публичный API.
