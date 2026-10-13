# Экспорт в Markdown

[English](../en/markdown-export.md) | [Русский](markdown-export.md)

`research export markdown` публикует текущий `ResearchSnapshot` в виде одного самостоятельного Markdown-документа. Сайт, сервер или внешний сервис не требуются.

## Использование

```bash
research export markdown
research export markdown --output ./reports/research.md
```

По умолчанию создаётся `research.md` в текущем каталоге. Существующий файл не перезаписывается молча: при конфликте команда завершится ошибкой, нужно выбрать другой путь.

Для другого каталога с research data глобальный параметр указывается перед командой:

```bash
research --base-path ./research-data export markdown --output ./reports/research.md
```

## Разделы отчёта

- **Summary** — общее число запусков, completed, failed, aborted, running и состояния review.
- **Research history** — запуски в порядке snapshot: гипотеза, мотивация и reference, execution/review status, временные метки, параметры, метрики и уже записанные conclusion/next step.
- **Relations** — только существующие связи из `motivation.reference`.
- **Collected examples** — компактные записи из `samples.jsonl`, а не исходные датасеты.
- **Consistency** — warnings/errors, найденные проверкой согласованности.
- **Conclusions** — только выводы и следующие шаги, уже записанные в review соответствующих запусков.

## Архитектура и гарантии

CLI строит `ResearchSnapshot` и передаёт его в `MarkdownAdapter`. Adapter только отображает переданный snapshot: он не читает `.research` напрямую, не запускает ML-код, не вызывает LLM и не придумывает научные выводы. Построение snapshot читает существующие research data; ни builder, ни adapter не изменяют записи запусков.

Markdown-файл — publication artifact, а не новый источник истины. Параметры и sample records отображаются в читаемом виде; большие датасеты и предметные объекты не загружаются и не встраиваются в документ.
