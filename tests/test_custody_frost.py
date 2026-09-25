import custody_frost


def test_extension_links_frost_taproot_ciphersuite() -> None:
    assert custody_frost.ciphersuite_id() == "FROST-secp256k1-SHA256-TR-v1"
