"""Regression tests for forensic signatures and tamper detection."""
import hashlib

import pytest

from main import ForensicSigner


def merkle_root(h_list: list[str]) -> str:
    if not h_list:
        raise ValueError("A Merkle tree requires at least one leaf")
    cur = list(h_list)
    while len(cur) > 1:
        if len(cur) % 2 == 1:
            cur.append(cur[-1])
        cur = [
            hashlib.sha256((cur[i] + cur[i + 1]).encode("ascii")).hexdigest()
            for i in range(0, len(cur), 2)
        ]
    return cur[0]


def test_signature_verifies_for_original_merkle_root() -> None:
    leaves = [
        hashlib.sha256(b"car-crash-image-1.jpg").hexdigest(),
        hashlib.sha256(b"speed-log-120kmh.json").hexdigest(),
        hashlib.sha256(b"lidar-scan-data").hexdigest(),
    ]
    root = merkle_root(leaves)
    signer = ForensicSigner()
    signature = signer.sign(root)
    public_key = signer.get_public_pem()
    assert signer.verify(root, signature, public_key)


def test_signature_rejects_tampered_merkle_root() -> None:
    first = hashlib.sha256(b"car-crash-image-1.jpg").hexdigest()
    speed = hashlib.sha256(b"speed-log-120kmh.json").hexdigest()
    lidar = hashlib.sha256(b"lidar-scan-data").hexdigest()
    root_original = merkle_root([first, speed, lidar])
    root_fake = merkle_root(
        [first, hashlib.sha256(b"speed-log-60kmh.json").hexdigest(), lidar]
    )
    signer = ForensicSigner()
    signature = signer.sign(root_original)
    assert not signer.verify(root_fake, signature, signer.get_public_pem())


def test_signature_rejects_wrong_public_key() -> None:
    digest = hashlib.sha256(b"synthetic evidence").hexdigest()
    signer = ForensicSigner()
    signature = signer.sign(digest)
    other = ForensicSigner()
    assert not signer.verify(digest, signature, other.get_public_pem())


def test_signer_rejects_non_digest_input() -> None:
    signer = ForensicSigner()
    with pytest.raises(ValueError):
        signer.sign("not-a-hex-digest")


def test_merkle_root_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        merkle_root([])
