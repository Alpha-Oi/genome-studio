//! Python binding через PyO3.
//!
//! Компилируется только с feature `python` (через maturin).

use pyo3::prelude::*;

use crate::build;
use crate::version;

/// Возвращает версию gs-core.
#[pyfunction]
fn version() -> &'static str {
    version::version()
}

/// Возвращает режим сборки.
#[pyfunction]
fn build_mode() -> &'static str {
    build::resolve().as_str()
}

/// Доступен ли dev-override.
#[pyfunction]
fn dev_override_available() -> bool {
    build::dev_override_compiled()
}

/// Проверяет наличие dev-ключа.
#[pyfunction]
fn signing_key_present() -> bool {
    build::signing_key_present()
}

/// Регистрирует модуль `gs_core._gs_core`.
#[pymodule]
pub fn register_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(build_mode, m)?)?;
    m.add_function(wrap_pyfunction!(dev_override_available, m)?)?;
    m.add_function(wrap_pyfunction!(signing_key_present, m)?)?;
    Ok(())
}
