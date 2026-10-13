# Экспорт статического сайта

[English](../en/static-site.md) | [Русский](static-site.md)

`research export site` публикует `ResearchSnapshot` в виде статического HTML-сайта. Его можно открыть с локального диска, а позднее разместить на GitHub Pages или другом статическом хостинге. ReMgu не выполняет deployment.

## Использование

```bash
research export site
research export site --output ./reports/site
research --base-path ./research-data export site --output ./reports/site
```

По умолчанию создаётся каталог `site/` в текущем рабочем каталоге. Каталог назначения не должен существовать заранее: существующий сайт не перезаписывается автоматически.

## Создаваемые файлы

```text
site/
├── index.html
├── style.css
├── runs/
│   ├── run-001.html
│   └── ...
└── examples/
    └── index.html
```

Главная страница содержит статистику запусков, хронологию исследования, записанные выводы и следующие шаги, а также consistency findings. На странице каждого запуска отображаются гипотеза, мотивация и reference, execution/review status, временные метки, параметры, метрики и компактные samples. Если snapshot построен с `ExampleProvider` и `describe_examples=True`, перед каждой записью примера выводится краткое человекочитаемое описание.

## Архитектура и гарантии

CLI строит `ResearchSnapshot` и передаёт его в `StaticSiteAdapter`. Adapter только отображает переданный snapshot: он не читает `.research`, не обращается к объектам `Run`, не запускает ML, не вызывает LLM и не придумывает научные выводы. Сайт использует обычные HTML и CSS, без backend, JavaScript-фреймворка или JavaScript. Динамический текст экранируется для HTML. Исследовательские данные не изменяются.
