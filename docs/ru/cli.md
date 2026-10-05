# Сценарии CLI

[English](../en/cli.md) | [Русский](../../README.ru.md)

Команды выполняются из корня репозитория. В текущей версии CLI запускается через `python -m research.cli`. Каталог данных по умолчанию — `.research/` в текущем рабочем каталоге.

## 1. Создать запуск

```bash
python -m research.cli new \
  --hypothesis "Увеличение hidden_dim до 512 улучшит NDCG@20" \
  --motivation-type previous_run \
  --reference run-001
```

**Зачем.** До начала обучения зафиксировать проверяемое утверждение и связать его с предыдущим запуском, который подсказал эксперимент.

**Аргументы.** `--hypothesis` обязателен. `--motivation-type` по умолчанию равен `new`; можно указать, например, `previous_run` или `literature_citation`. `--reference` — необязательный идентификатор предыдущего запуска или статьи; для `previous_run` укажите ID существующего запуска.

**Ожидаемый результат.** Команда печатает новый ID, например `run-002`, создаёт `runs/run-002/run.yaml` и записывает указатель активного запуска в `.research/active`. Одновременно может быть активен только один запуск.

Для нового направления:

```bash
python -m research.cli new --hypothesis "Порядок узлов через random walk улучшает качество графовой последовательности" --motivation-type new
```

## 2. Разобрать завершённый запуск

После нормального завершения кода обучения API переводит запуск в `completed`. Научную интерпретацию нужно зафиксировать отдельно:

```bash
python -m research.cli finish run-002 \
  --conclusion "NDCG@20 вырос с 0.401 до 0.428 на фиксированной validation-выборке" \
  --next-step "Повторить с тремя random seed"
```

Параметры `--conclusion` и `--next-step` обязательны. Разбор разрешён только для завершённого запуска. Команда не позволяет повторно разобрать запуск, уже имеющий статус `reviewed`.

**Ожидаемый результат.** `review.status` становится `reviewed`, а вывод и следующий шаг сохраняются в `run.yaml`. Статус исполнения при этом не меняется.

Если нужный запуск активен, ID можно не указывать:

```bash
python -m research.cli finish --conclusion "..." --next-step "..."
```

## 3. Посмотреть историю запусков

Показать активный запуск и оба состояния жизненного цикла:

```bash
python -m research.cli status
```

Показать последние запуски (выбранный набор выводится от старого к новому):

```bash
python -m research.cli previous --limit 10
```

Пример вывода:

```text
run-001 | execution=completed | review=reviewed | motivation=new | hypothesis=Baseline with degree sorting
run-002 | execution=completed | review=needs_review | motivation=previous_run -> run-001 | hypothesis=Replace degree sorting with random walks
```

Это краткая сводка, а не замена изучению `run.yaml` и артефактов каждого запуска.

## 4. Возобновить работу с незавершённым запуском

Если запуск всё ещё имеет статус `running`, но файл активного указателя потерян, восстановите его:

```bash
python -m research.cli resume run-002
```

Возобновить можно только запуск со статусом `running`. Команда не перезапускает обучение и не восстанавливает процесс ОС; она восстанавливает указатель REMgu, чтобы последующий вызов `Experiment.run()` мог открыть сохранённый запуск.

## 5. Проверить исследовательские записи

```bash
python -m research.cli check
```

Команда выводит количество завершённых запусков и запусков с непустыми гипотезами, затем перечисляет найденные проблемы. Проверка не меняет данные; подробности — [проверка согласованности](consistency-check.md).

## 6. Хранить данные в другом каталоге

`--base-path` указывается перед подкомандой:

```bash
python -m research.cli --base-path ./research-data new --hypothesis "H1" --motivation-type new
python -m research.cli --base-path ./research-data status
```

В каталоге находятся `runs/` и файл `active`, пока есть активный запуск.

## Правила жизненного цикла

- `research new` отказывается создавать второй активный запуск.
- Новый запуск получает `execution.status = running` и `review.status = needs_review`.
- Нормальный выход из `with experiment.run()` завершает активный запуск; необработанное исключение помечает его как `failed`.
- Через API запуск также можно явно завершить со статусом `aborted`.
- `research finish` фиксирует научный разбор, а не завершает исполнение.
- `research check` не редактирует записи запусков.
