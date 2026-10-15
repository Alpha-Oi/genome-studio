# ADR 0005: Три сборки

## Статус
Принято.

## Решение
Prod / Internal / Dev. Из одной кодовой базы.

## Обоснование
- Prod для пользователей.
- Internal для команды.
- Dev для разработчика (локально).

## Реализация
- Compile-time flags (Rust).
- Build-time env (Python).
- CI проверяет отсутствие dev-флагов в prod.
