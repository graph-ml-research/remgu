# Проверка согласованности

[English](../en/consistency-check.md) | [Русский](../../README.ru.md)

## Зачем она нужна

Исследовательские записи становятся неполными, если эксперимент завершился ошибкой, разбор откладывается или метаданные редактируются вручную. `research check` находит распространённые проблемы, не мешая обычным запускам и не изменяя файлы.

## Запуск

```bash
python -m research.cli check
```

Проверка читает все найденные `runs/<run-id>/run.yaml`, включая записи со статусами `running`, `failed` и `aborted`. Она сообщает:

- количество завершённых запусков;
- количество запусков с непустой гипотезой;
- отсутствующие или некорректные секции research/execution/review;
- отсутствующие гипотезы и слабую мотивацию;
- ссылки мотивации на неизвестные ID запусков;
- завершённые запуски без вывода;
- неизвестные статусы и несовместимые состояния разбора;
- нечитаемый YAML или некорректную структуру верхнего уровня.

Пример вывода (иллюстративный):

```text
completed runs: 4
runs with hypotheses: 6
issues:
  warning: run-002: missing_conclusion: completed run has no conclusion
  warning: run-005: weak_motivation: previous_run motivation has no reference
```

Точные сообщения зависят от содержимого файлов.

## Гарантия read-only

Проверка читает исходный YAML, а не создаёт объекты `Run`. Поэтому она может описывать некорректные метаданные, не прерывая анализ остальных запусков. Она не переписывает `run.yaml`, не меняет `active` и не изменяет статусы исполнения или разбора. Исправьте найденные проблемы вручную и повторите проверку.

## Использование из Python

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

`report.ok` равен `True`, только если проблем не найдено. `ConsistencyIssue` содержит `run_id`, машинный `code`, человекочитаемое `message` и `severity` (по умолчанию `warning`; структурные ошибки получают `error`). Это диагностический отчёт, а не инструмент автоматического исправления.

## Как интерпретировать результат

Чистый отчёт не доказывает научную состоятельность гипотезы или статистическую значимость метрики. Проверяются только структурные правила и правила исследовательского workflow, реализованные в REMgu. Научная интерпретация остаётся задачей исследователя.
