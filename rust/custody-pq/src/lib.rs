//! PyO3 binding to RustCrypto `slh-dsa` (FIPS 205 SLH-DSA) for the custody-lab post-quantum
//! module.
//!
//! Keys and signatures cross the boundary as the FIPS 205 byte encodings. The parameter set is
//! named by its FIPS 205 name, for example `SLH-DSA-SHA2-128f`. The `_internal` functions take
//! the message exactly as signed (FIPS 205 `slh_sign_internal`); the others prefix the domain
//! byte, context length and context (FIPS 205 `slh_sign`). They exist so the NIST ACVP vectors
//! can check both interfaces.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand_core::{OsRng, RngCore};
use slh_dsa::{
    ParameterSet, Sha2_128f, Sha2_128s, Sha2_192f, Sha2_192s, Sha2_256f, Sha2_256s, Shake128f,
    Shake128s, Shake192f, Shake192s, Shake256f, Shake256s, Signature, SigningKey, VerifyingKey,
};

type Bytes = Vec<u8>;

fn err<E: std::fmt::Debug>(e: E) -> PyErr {
    PyValueError::new_err(format!("{e:?}"))
}

/// Call `$body` with `$p` bound to the parameter-set type named by `$name`.
macro_rules! with_parameter_set {
    ($name:expr, $p:ident, $body:expr) => {
        match $name {
            "SLH-DSA-SHA2-128s" => { type $p = Sha2_128s; $body }
            "SLH-DSA-SHA2-128f" => { type $p = Sha2_128f; $body }
            "SLH-DSA-SHA2-192s" => { type $p = Sha2_192s; $body }
            "SLH-DSA-SHA2-192f" => { type $p = Sha2_192f; $body }
            "SLH-DSA-SHA2-256s" => { type $p = Sha2_256s; $body }
            "SLH-DSA-SHA2-256f" => { type $p = Sha2_256f; $body }
            "SLH-DSA-SHAKE-128s" => { type $p = Shake128s; $body }
            "SLH-DSA-SHAKE-128f" => { type $p = Shake128f; $body }
            "SLH-DSA-SHAKE-192s" => { type $p = Shake192s; $body }
            "SLH-DSA-SHAKE-192f" => { type $p = Shake192f; $body }
            "SLH-DSA-SHAKE-256s" => { type $p = Shake256s; $body }
            "SLH-DSA-SHAKE-256f" => { type $p = Shake256f; $body }
            other => Err(PyValueError::new_err(format!("unknown parameter set {other:?}"))),
        }
    };
}

fn signing_key<P: ParameterSet>(sk: &[u8]) -> PyResult<SigningKey<P>> {
    SigningKey::<P>::try_from(sk).map_err(err)
}

fn verifying_key<P: ParameterSet>(pk: &[u8]) -> PyResult<VerifyingKey<P>> {
    VerifyingKey::<P>::try_from(pk).map_err(err)
}

/// The 32-, 48- or 64-byte randomiser input: `rand` if given, otherwise fresh from the OS.
fn randomiser<P: ParameterSet>(rand: Option<Bytes>) -> Bytes {
    rand.unwrap_or_else(|| {
        let mut fresh = vec![0u8; SigningKey::<P>::new(&mut OsRng).to_bytes().len() / 4];
        OsRng.fill_bytes(&mut fresh);
        fresh
    })
}

/// FIPS 205 names of the twelve parameter sets this extension supports.
#[pyfunction]
fn parameter_sets() -> Vec<&'static str> {
    vec![
        Sha2_128s::NAME, Sha2_128f::NAME, Sha2_192s::NAME, Sha2_192f::NAME, Sha2_256s::NAME,
        Sha2_256f::NAME, Shake128s::NAME, Shake128f::NAME, Shake192s::NAME, Shake192f::NAME,
        Shake256s::NAME, Shake256f::NAME,
    ]
}

/// A fresh key pair: (secret key, public key).
#[pyfunction]
fn keygen(parameter_set: &str) -> PyResult<(Bytes, Bytes)> {
    with_parameter_set!(parameter_set, P, {
        let sk = SigningKey::<P>::new(&mut OsRng);
        let pk: &VerifyingKey<P> = sk.as_ref();
        Ok((sk.to_vec(), pk.to_vec()))
    })
}

/// FIPS 205 `slh_keygen_internal`: the key pair determined by the three seeds.
#[pyfunction]
fn keygen_internal(
    parameter_set: &str,
    sk_seed: Bytes,
    sk_prf: Bytes,
    pk_seed: Bytes,
) -> PyResult<(Bytes, Bytes)> {
    with_parameter_set!(parameter_set, P, {
        let sk = SigningKey::<P>::slh_keygen_internal(&sk_seed, &sk_prf, &pk_seed);
        let pk: &VerifyingKey<P> = sk.as_ref();
        Ok((sk.to_vec(), pk.to_vec()))
    })
}

/// FIPS 205 `slh_sign` with a context string. `rand` is the per-signature randomiser; pass the
/// public seed for the deterministic variant, or omit it for fresh randomness (hedged signing).
#[pyfunction]
#[pyo3(signature = (parameter_set, sk, message, context = Vec::new(), rand = None))]
fn sign(
    parameter_set: &str,
    sk: Bytes,
    message: Bytes,
    context: Bytes,
    rand: Option<Bytes>,
) -> PyResult<Bytes> {
    with_parameter_set!(parameter_set, P, {
        let rand = randomiser::<P>(rand);
        let signature = signing_key::<P>(&sk)?
            .try_sign_with_context(&message, &context, Some(&rand))
            .map_err(err)?;
        Ok(signature.to_vec())
    })
}

/// FIPS 205 `slh_sign_internal`: signs `message` exactly as given.
#[pyfunction]
#[pyo3(signature = (parameter_set, sk, message, rand = None))]
fn sign_internal(
    parameter_set: &str,
    sk: Bytes,
    message: Bytes,
    rand: Option<Bytes>,
) -> PyResult<Bytes> {
    with_parameter_set!(parameter_set, P, {
        let rand = randomiser::<P>(rand);
        Ok(signing_key::<P>(&sk)?.slh_sign_internal(&message, Some(&rand)).to_vec())
    })
}

/// FIPS 205 `slh_verify` with a context string.
#[pyfunction]
#[pyo3(signature = (parameter_set, pk, message, signature, context = Vec::new()))]
fn verify(
    parameter_set: &str,
    pk: Bytes,
    message: Bytes,
    signature: Bytes,
    context: Bytes,
) -> PyResult<bool> {
    with_parameter_set!(parameter_set, P, {
        let Ok(signature) = Signature::<P>::try_from(signature.as_slice()) else {
            return Ok(false);
        };
        Ok(verifying_key::<P>(&pk)?
            .try_verify_with_context(&message, &context, &signature)
            .is_ok())
    })
}

/// FIPS 205 `slh_verify_internal`: verifies `message` exactly as given.
#[pyfunction]
fn verify_internal(
    parameter_set: &str,
    pk: Bytes,
    message: Bytes,
    signature: Bytes,
) -> PyResult<bool> {
    with_parameter_set!(parameter_set, P, {
        let Ok(signature) = Signature::<P>::try_from(signature.as_slice()) else {
            return Ok(false);
        };
        Ok(verifying_key::<P>(&pk)?.slh_verify_internal(&message, &signature).is_ok())
    })
}

#[pymodule]
fn custody_pq(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parameter_sets, m)?)?;
    m.add_function(wrap_pyfunction!(keygen, m)?)?;
    m.add_function(wrap_pyfunction!(keygen_internal, m)?)?;
    m.add_function(wrap_pyfunction!(sign, m)?)?;
    m.add_function(wrap_pyfunction!(sign_internal, m)?)?;
    m.add_function(wrap_pyfunction!(verify, m)?)?;
    m.add_function(wrap_pyfunction!(verify_internal, m)?)?;
    Ok(())
}
