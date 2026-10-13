# Research Snapshot

[English](../en/research-snapshot.md) | [Русский](research-snapshot.md)

`ResearchSnapshot` — единая производная модель, которую используют исследовательский и publication-слои ReMgu.

Это **не persistable domain entity** и не второй source of truth. Snapshot каждый раз строится заново из `.research/`.

## Построение snapshot

```python
from remgu import ResearchSnapshotBuilder

snapshot = ResearchSnapshotBuilder(".research", describe_examples=False).build()
print(snapshot.summary.total_runs)
print(snapshot.summary.completed)
print(snapshot.summary.reviewed)
```

Builder читает существующие `run.yaml`, `params.yaml`, `metrics.csv` и `samples.jsonl`. По умолчанию он также требует `ExampleProvider` и добавляет к каждому sample с `example_id` краткое описание. Если описания не нужны, это отключается явно через `describe_examples=False`. Отсутствующий provider или пустое описание при включённом режиме приводят к ошибке. Кроме того, запускается read-only проверка согласованности, а её findings попадают в `snapshot.findings`.

## Модель

Snapshot содержит:

- `summary` — общее число запусков и распределение по execution/review status;
- `runs` — производные представления отдельных запусков;
- `relations` — только ссылки, уже записанные в `motivation.reference`;
- `metrics` — плоские строки метрик с ID запуска;
- `samples` — плоские компактные диагностические записи с ID запуска;
- `findings` — результаты проверки согласованности;
- `summary_text` — короткое текстовое резюме.

Исходные datasets, графы, модели и другие большие внешние объекты не загружаются.

## `research update`

```bash
research update
```

Команда строит snapshot, выполняет проверку согласованности и выводит краткое резюме. Файлы `.research/` не изменяются.

## Архитектурная граница

Core-слой отвечает за сохранение запусков и их артефактов. Research-слой строит snapshot и результаты consistency analysis. Publication adapters получают snapshot и не должны превращаться во второй механизм хранения.
