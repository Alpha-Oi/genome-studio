//! Build Resolver.
//!
//! Определяет режим сборки: prod / internal / dev.
//! В отличие от Python-версии, здесь решение принимается
//! на уровне скомпилированного бинарника.

use std::path::PathBuf;

/// Режим сборки.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BuildMode {
    /// Production — для всех пользователей.
    Prod,
    /// Internal — для команды.
    Internal,
    /// Dev — только локально, с dev_override.
    Dev,
}

impl BuildMode {
    /// Строковое представление.
    pub fn as_str(&self) -> &'static str {
        match self {
            BuildMode::Prod => "prod",
            BuildMode::Internal => "internal",
            BuildMode::Dev => "dev",
        }
    }
}

/// Доступен ли dev-override в этой сборке.
///
/// TRUE только если скомпилировано с feature `dev_override`.
/// В prod-сборке — всегда FALSE.
pub const fn dev_override_compiled() -> bool {
    cfg!(feature = "dev_override")
}

/// Путь к dev-ключу.
pub fn signing_key_path() -> PathBuf {
    let mut path = dirs_home();
    path.push(".gs");
    path.push("keys");
    path.push("dev-signing.key");
    path
}

/// Домашний каталог.
fn dirs_home() -> PathBuf {
    std::env::var_os("HOME")
        .or_else(|| std::env::var_os("USERPROFILE"))
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."))
}

/// Проверка наличия dev-ключа.
pub fn signing_key_present() -> bool {
    signing_key_path().is_file()
}

/// Определяет текущий режим сборки.
///
/// Логика:
/// 1. Если dev_override не скомпилирован — PROD.
/// 2. Если нет ключа — PROD.
/// 3. Если GS_BUILD != "dev" — PROD.
/// 4. Иначе — DEV.
pub fn resolve() -> BuildMode {
    if !dev_override_compiled() {
        return BuildMode::Prod;
    }

    if !signing_key_present() {
        return BuildMode::Prod;
    }

    let env = std::env::var("GS_BUILD")
        .unwrap_or_else(|_| "prod".to_string())
        .to_lowercase();

    match env.as_str() {
        "dev" => BuildMode::Dev,
        "internal" => BuildMode::Internal,
        _ => BuildMode::Prod,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dev_override_not_compiled_by_default() {
        // В тестах без --features dev_override должно быть false.
        #[cfg(not(feature = "dev_override"))]
        assert!(!dev_override_compiled());
    }

    #[test]
    fn prod_by_default() {
        #[cfg(not(feature = "dev_override"))]
        assert_eq!(resolve(), BuildMode::Prod);
    }

    #[test]
    fn mode_strings() {
        assert_eq!(BuildMode::Prod.as_str(), "prod");
        assert_eq!(BuildMode::Internal.as_str(), "internal");
        assert_eq!(BuildMode::Dev.as_str(), "dev");
    }
}
