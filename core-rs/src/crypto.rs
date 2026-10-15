//! Криптография.
//!
//! Подпись и проверка dev-сессий.
//! Использует ed25519.

use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};

/// Ошибки крипто.
#[derive(Debug, thiserror::Error)]
pub enum CryptoError {
    /// Неверная длина ключа.
    #[error("invalid key length")]
    InvalidKeyLength,
    /// Неверная подпись.
    #[error("invalid signature")]
    InvalidSignature,
}

/// Генерирует новый пару ключей (priv, pub).
pub fn generate_keypair() -> (SigningKey, VerifyingKey) {
    let mut csprng = rand::rngs::OsRng;
    let signing_key = SigningKey::generate(&mut csprng);
    let verifying_key = signing_key.verifying_key();
    (signing_key, verifying_key)
}

/// Подписывает сообщение.
pub fn sign(signing_key: &SigningKey, message: &[u8]) -> Signature {
    signing_key.sign(message)
}

/// Проверяет подпись.
pub fn verify(
    verifying_key: &VerifyingKey,
    message: &[u8],
    signature: &Signature,
) -> Result<(), CryptoError> {
    verifying_key
        .verify(message, signature)
        .map_err(|_| CryptoError::InvalidSignature)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sign_and_verify_roundtrip() {
        let (sk, vk) = generate_keypair();
        let msg = b"session-data";
        let sig = sign(&sk, msg);
        assert!(verify(&vk, msg, &sig).is_ok());
    }

    #[test]
    fn verify_fails_on_wrong_message() {
        let (sk, vk) = generate_keypair();
        let sig = sign(&sk, b"correct");
        assert!(verify(&vk, b"wrong", &sig).is_err());
    }
}
