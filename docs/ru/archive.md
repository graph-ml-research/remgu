# Research archive

[English](../en/archive.md) | [Русский](archive.md)

`research archive` — первый publication adapter ReMgu. Он создаёт самодостаточный ZIP, который можно загрузить в Yougile или отправить руководителю без какого-либо сервиса ReMgu.

## Использование

```bash
research archive
```

По умолчанию создаётся `research-archive.zip` в текущем каталоге. Другой путь можно указать так:

```bash
research archive --output ./reports/run-2026-10-07.zip
```

Существующий файл не перезаписывается молча: команда завершается ошибкой и предлагает выбрать другой путь.

## Структура архива

```text
research-archive/
├── README.md
├── report.md
├── research.yaml
├── runs/
│   └── run-001/
│       ├── run.yaml
│       ├── params.yaml
│       ├── metrics.csv
│       └── samples.jsonl
└── examples/
    └── node-42.json
```

Необязательные файлы попадают в архив только если они существуют в исходном запуске. `examples/` заполняется только для компактных sample records, содержащих `example_id`.

## Что публикуется

- `README.md` объясняет содержание архива;
- `report.md` — компактный автоматически сформированный summary;
- `research.yaml` — машинно-читаемые summary, существующие relations и consistency findings;
- `runs/` — копии известных ReMgu-артефактов;
- `examples/` — компактные диагностические записи, если их можно представить в JSON.

Исходные datasets, графы, checkpoints и другие большие объекты, которые ReMgu не умеет сериализовать, в архив не копируются.

## Source of truth и безопасность

Каталог `.research/` остаётся source of truth. Создание архива не изменяет research store. ZIP — publication artifact; его не предполагается редактировать и импортировать обратно в ReMgu.

Report не придумывает научных выводов. Conclusions и next steps выводятся только тогда, когда они уже записаны в review данных запуска.
