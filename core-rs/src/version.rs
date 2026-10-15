//! Версия ядра.

/// Версия gs-core.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Возвращает версию.
pub fn version() -> &'static str {
    VERSION
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_is_not_empty() {
        assert!(!version().is_empty());
    }
}
