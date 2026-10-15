# Contributing

Спасибо за интерес к Genome Studio. Мы приветствуем bug reports, feature requests и pull requests.

## Как сообщить о проблеме

1. Проверь, что это не уже существующий issue.
2. Открой новый issue через GitHub.
3. Опиши: что делал, что ожидал, что получил. Приложи скриншот и текст ошибки.

## Как предложить фичу

1. Открой Feature request.
2. Опиши: зачем это нужно, кто пользователь, как увидеть что работает.
3. Жди обсуждения перед началом реализации.

## Pull requests

1. Fork репозитория.
2. Создай ветку: git checkout -b feature/краткое-название
3. Внеси изменения.
4. Убедись что всё зелёное:

       uv run --package genome-studio-backend pytest backend/tests -q
       pnpm --dir ui typecheck
       pnpm --dir ui build:prod

5. Commit: git commit -m "Add: краткое описание"
6. Push: git push origin feature/краткое-название
7. Открой Pull Request.

## Стиль кода

- Python: ruff (line-length 100), mypy strict.
- TypeScript: strict, без any.
- Rust: rustfmt, clippy без warnings.
- Комментарии осмысленные, на русском или английском.

## Правила

- Одна фича = один PR.
- Каждая новая функция покрывается тестами.
- Не коммить секреты, API-ключи, .env файлы.
- Не менять публичные API без обсуждения.
- Все коммиты должны проходить CI.

## Установка окружения разработчика

См. README.md, раздел Быстрый старт.

## Лицензия

Отправляя PR, ты соглашаешься, что твой вклад распространяется под лицензией проекта (см. LICENSE).