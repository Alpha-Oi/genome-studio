# Dev Override

## Принцип

Dev Override - не настройка, а отдельная сборка.
В prod-сборке кода для обхода T2 физически нет.

## Три сборки

PROD - для всех
- T0: отключаемо
- T1: с трением
- T2: жёстко
- Нет dev-кода

INTERNAL - для команды
- всё как prod +
- dev override через подписанный ключ
- не распространяется

DEV - только для разработчика
- T0/T1/T2: всё отключаемо
- локально
- изолированно
- без экспорта наружу

## Активация dev-режима

Цепочка (все условия обязательны):
1. Сборка с feature dev_override
2. Подписанный ключ разработчика (ed25519)
3. Проверка среды: localhost / air-gapped
4. Нет внешних сетевых интерфейсов
5. Sandbox DB

Если хоть одно не выполнено - dev-режим не включается.

## Compile-time flags (Rust)

#[cfg(feature = "dev_override")]
pub fn check_t2(seq: &Sequence) -> CheckResult {
    CheckResult::Allow
}

#[cfg(not(feature = "dev_override"))]
pub fn check_t2(seq: &Sequence) -> CheckResult {
    real_check(seq)
}

В prod-сборке ветка Allow не компилируется.

## Build-time flags (Python)

import os
BUILD_MODE = os.environ.get("GS_BUILD", "prod")

def check_t2(seq):
    if BUILD_MODE == "dev" and _dev_key_valid():
        return Allow()
    return real_check(seq)

В prod-сборке BUILD_MODE жёстко "prod".

## Изоляция dev

Правило                          | Реализация
---------------------------------|------------------
Только локально                  | loopback only
Нет экспорта                     | export disabled
Нет лабораторного оборудования   | integrations disabled
Нет телеметрии                   | telemetry disabled
Sandbox DB                       | local only
Синтетические тесты              | реальные патогены - моки

## Управление ключами

~/.gs/keys/
  dev-signing.key    - приватный, только у разработчика
  dev-signing.pub    - публичный, вшит в dev-сборку
  revocation.list

Правила:
- Приватный ключ - не в git, не в облаке
- При компрометации - отзыв, пересборка
- Смена ключа - раз в N месяцев

## Dev Panel

Отдельный UI-модуль:
- виден только в dev
- не доступен через API
- не сохраняется в проект
- показывает статус: сборка, ключ, среда, сеть, экспорт

## Что нельзя даже в dev

- Экспорт реальных патогенов
- Заказ последовательностей
- Интеграция с лабораторией
- Отправка в облако
- Шаринг dev-сборки

Правило: dev - для тестирования логики, не для производства.

## Документы

- docs/policy/DEV_POLICY.md - что можно/нельзя
- docs/policy/ACCESS.md - кто имеет доступ
- docs/policy/KEYS.md - управление ключами
- docs/policy/INCIDENT.md - при утечке
