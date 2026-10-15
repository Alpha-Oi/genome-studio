//! Dev Override.
//!
//! ВНИМАНИЕ: этот модуль компилируется ТОЛЬКО с feature `dev_override`.
//! В prod-сборке его кода физически нет.
//!
//! Назначение: разрешить разработчику отключать T0/T1/T2
//! в изолированной локальной среде для тестирования.

use crate::build;

/// Результат проверки безопасности.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CheckResult {
    /// Разрешено.
    Allow,
    /// Заблокировано.
    Deny,
}

/// Точка входа dev-override: разрешить отключение T2.
///
/// Возвращает Allow только если:
/// - скомпилировано с feature `dev_override`;
/// - есть подписанный ключ;
/// - режим сборки — Dev;
/// - среда изолирована (проверка в вызывающем коде).
pub fn check_t2_override() -> CheckResult {
    if !build::dev_override_compiled() {
        return CheckResult::Deny;
    }
    if !build::signing_key_present() {
        return CheckResult::Deny;
    }
    if build::resolve() != build::BuildMode::Dev {
        return CheckResult::Deny;
    }
    CheckResult::Allow
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn t2_override_requires_all_conditions() {
        // В тестовой среде без ключа и без режима dev — Deny.
        let result = check_t2_override();
        assert_eq!(result, CheckResult::Deny);
    }
}
