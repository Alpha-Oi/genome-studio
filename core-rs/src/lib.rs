//! Genome Studio core.
//!
//! Rust hot paths для:
//! - парсинга FASTA/FASTQ/BAM/VCF
//! - поиска PAM и off-target
//! - Consequence Engine
//! - крипто (dev-ключ)
//! - Build Resolver
//!
//! ВАЖНО: модуль `dev_override` компилируется ТОЛЬКО
//! с feature-флагом `dev_override`. В prod-сборке его кода
//! физически нет.

#![deny(unsafe_code)]
#![warn(missing_docs)]
#![warn(clippy::all)]

pub mod build;
pub mod crypto;
pub mod version;

// Dev Override — только при feature-флаге.
// В prod-сборке этот модуль НЕ существует.
#[cfg(feature = "dev_override")]
pub mod dev_override;

// Python binding — только при feature-флаге `python`.
#[cfg(feature = "python")]
mod python;

#[cfg(feature = "python")]
pub use python::register_module;
