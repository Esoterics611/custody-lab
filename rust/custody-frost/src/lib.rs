//! PyO3 binding to ZF FROST (`frost-secp256k1-tr`): DKG, two-round signing, aggregation.
//!
//! Every value crosses the boundary as bytes in the crate's own serialization, and maps of
//! per-participant values as `dict[int, bytes]` keyed by participant identifier (1..=n). The
//! binding holds no state: each signer process keeps its own key package and nonces, so no
//! process ever holds another participant's secret.

use std::collections::{BTreeMap, HashMap};

use frost_secp256k1_tr::{
    self as frost,
    keys::{dkg, Tweak},
    rand_core::OsRng,
    Ciphersuite, Identifier, Secp256K1Sha256TR,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

type Bytes = Vec<u8>;

fn err<E: std::fmt::Debug>(e: E) -> PyErr {
    PyValueError::new_err(format!("{e:?}"))
}

fn id(i: u16) -> PyResult<Identifier> {
    Identifier::try_from(i).map_err(err)
}

/// Decode a `dict[int, bytes]` into a map keyed by FROST identifier.
fn decode_map<T>(
    map: HashMap<u16, Bytes>,
    decode: impl Fn(&[u8]) -> Result<T, frost::Error>,
) -> PyResult<BTreeMap<Identifier, T>> {
    map.into_iter()
        .map(|(i, b)| Ok((id(i)?, decode(&b).map_err(err)?)))
        .collect()
}


/// The FROST ciphersuite identifier compiled into this extension.
#[pyfunction]
fn ciphersuite_id() -> &'static str {
    <Secp256K1Sha256TR as Ciphersuite>::ID
}

/// DKG part 1 for participant `identifier`: (secret package, broadcast package).
#[pyfunction]
fn dkg_part1(identifier: u16, max_signers: u16, min_signers: u16) -> PyResult<(Bytes, Bytes)> {
    let (secret, package) = dkg::part1(id(identifier)?, max_signers, min_signers, OsRng).map_err(err)?;
    Ok((secret.serialize().map_err(err)?, package.serialize().map_err(err)?))
}

/// DKG part 2, given the other participants' round 1 packages: (secret package, private
/// packages to send, keyed by recipient).
#[pyfunction]
fn dkg_part2(
    secret1: Bytes,
    round1_packages: HashMap<u16, Bytes>,
) -> PyResult<(Bytes, HashMap<u16, Bytes>)> {
    let recipients: Vec<u16> = round1_packages.keys().copied().collect();
    let secret = dkg::round1::SecretPackage::deserialize(&secret1).map_err(err)?;
    let round1 = decode_map(round1_packages, dkg::round1::Package::deserialize)?;
    let (secret2, round2) = dkg::part2(secret, &round1).map_err(err)?;
    let mut packages = HashMap::new();
    for i in recipients {
        packages.insert(i, round2[&id(i)?].serialize().map_err(err)?);
    }
    Ok((secret2.serialize().map_err(err)?, packages))
}

/// DKG part 3: (this participant's key package, the group's public key package).
#[pyfunction]
fn dkg_part3(
    secret2: Bytes,
    round1_packages: HashMap<u16, Bytes>,
    round2_packages: HashMap<u16, Bytes>,
) -> PyResult<(Bytes, Bytes)> {
    let secret = dkg::round2::SecretPackage::deserialize(&secret2).map_err(err)?;
    let round1 = decode_map(round1_packages, dkg::round1::Package::deserialize)?;
    let round2 = decode_map(round2_packages, dkg::round2::Package::deserialize)?;
    let (key_package, public_key_package) = dkg::part3(&secret, &round1, &round2).map_err(err)?;
    Ok((key_package.serialize().map_err(err)?, public_key_package.serialize().map_err(err)?))
}

/// The group verifying key as 32 x-only bytes (BIP340 encoding).
#[pyfunction]
fn group_public_key(public_key_package: Bytes) -> PyResult<Bytes> {
    let package = frost::keys::PublicKeyPackage::deserialize(&public_key_package).map_err(err)?;
    let sec1 = package.verifying_key().serialize().map_err(err)?;
    Ok(sec1[1..].to_vec())
}

/// The BIP86 Taproot output key (x-only, 32 bytes): the group key tweaked with
/// H_TapTweak(P) and no script tree. Funds sent to this key are spent with `taproot=True`.
#[pyfunction]
fn taproot_output_key(public_key_package: Bytes) -> PyResult<Bytes> {
    let package = frost::keys::PublicKeyPackage::deserialize(&public_key_package).map_err(err)?;
    let tweaked = package.tweak(None::<&[u8]>);
    let sec1 = tweaked.verifying_key().serialize().map_err(err)?;
    Ok(sec1[1..].to_vec())
}

/// Signing round 1: (nonces, kept secret by the signer; commitments, sent to the coordinator).
#[pyfunction]
fn commit(key_package: Bytes) -> PyResult<(Bytes, Bytes)> {
    let key_package = frost::keys::KeyPackage::deserialize(&key_package).map_err(err)?;
    let (nonces, commitments) = frost::round1::commit(key_package.signing_share(), &mut OsRng);
    Ok((nonces.serialize().map_err(err)?, commitments.serialize().map_err(err)?))
}

/// Coordinator: bind the message to the chosen signers' commitments.
#[pyfunction]
fn signing_package(commitments: HashMap<u16, Bytes>, message: Bytes) -> PyResult<Bytes> {
    let commitments = decode_map(commitments, frost::round1::SigningCommitments::deserialize)?;
    frost::SigningPackage::new(commitments, &message).serialize().map_err(err)
}

/// The message inside a signing package. A signer checks this against its authorisation before
/// producing a share: it verifies what it signs, not what the coordinator says it signs.
#[pyfunction]
fn signing_package_message(signing_package: Bytes) -> PyResult<Bytes> {
    let package = frost::SigningPackage::deserialize(&signing_package).map_err(err)?;
    Ok(package.message().clone())
}

/// Signing round 2: this signer's signature share. With `taproot`, the share is for the BIP86
/// tweaked key (a Taproot key-path spend).
#[pyfunction]
#[pyo3(signature = (signing_package, nonces, key_package, taproot=false))]
fn sign(signing_package: Bytes, nonces: Bytes, key_package: Bytes, taproot: bool) -> PyResult<Bytes> {
    let package = frost::SigningPackage::deserialize(&signing_package).map_err(err)?;
    let nonces = frost::round1::SigningNonces::deserialize(&nonces).map_err(err)?;
    let key_package = frost::keys::KeyPackage::deserialize(&key_package).map_err(err)?;
    let share = if taproot {
        frost::round2::sign_with_tweak(&package, &nonces, &key_package, None)
    } else {
        frost::round2::sign(&package, &nonces, &key_package)
    };
    Ok(share.map_err(err)?.serialize())
}

/// Coordinator: verify each share and aggregate into a 64-byte BIP340 signature. `taproot` must
/// match the value the signers used.
#[pyfunction]
#[pyo3(signature = (signing_package, shares, public_key_package, taproot=false))]
fn aggregate(
    signing_package: Bytes,
    shares: HashMap<u16, Bytes>,
    public_key_package: Bytes,
    taproot: bool,
) -> PyResult<Bytes> {
    let package = frost::SigningPackage::deserialize(&signing_package).map_err(err)?;
    let shares = decode_map(shares, frost::round2::SignatureShare::deserialize)?;
    let public = frost::keys::PublicKeyPackage::deserialize(&public_key_package).map_err(err)?;
    let signature = if taproot {
        frost::aggregate_with_tweak(&package, &shares, &public, None)
    } else {
        frost::aggregate(&package, &shares, &public)
    };
    signature.map_err(err)?.serialize().map_err(err)
}

#[pymodule]
fn custody_frost(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ciphersuite_id, m)?)?;
    m.add_function(wrap_pyfunction!(dkg_part1, m)?)?;
    m.add_function(wrap_pyfunction!(dkg_part2, m)?)?;
    m.add_function(wrap_pyfunction!(dkg_part3, m)?)?;
    m.add_function(wrap_pyfunction!(group_public_key, m)?)?;
    m.add_function(wrap_pyfunction!(taproot_output_key, m)?)?;
    m.add_function(wrap_pyfunction!(commit, m)?)?;
    m.add_function(wrap_pyfunction!(signing_package, m)?)?;
    m.add_function(wrap_pyfunction!(signing_package_message, m)?)?;
    m.add_function(wrap_pyfunction!(sign, m)?)?;
    m.add_function(wrap_pyfunction!(aggregate, m)?)?;
    Ok(())
}
