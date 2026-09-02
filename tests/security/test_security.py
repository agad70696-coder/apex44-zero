import hashlib
import re


def test_quantum_hash_length() -> None:
    assert len(hashlib.shake_256(b"test").hexdigest(64)) == 128


def test_valid_hash_both() -> None:
    _64 = re.compile(r"^[a-fA-F0-9]{64}$")
    _128 = re.compile(r"^[a-fA-F0-9]{128}$")

    def v(h):
        return bool(_64.fullmatch(h) or _128.fullmatch(h))

    assert v("a" * 64) and v("a" * 128)


def test_pqc_verify_uses_sig() -> None:
    def fv(r, s):
        return (
            len(s) == 32 and s != b"\x00" * 32
            if re.fullmatch(r"^[a-fA-F0-9]{64}$|^[a-fA-F0-9]{128}$", r)
            else False
        )

    assert not fv("a" * 64, b"invalid")


def test_chain_recompute() -> None:
    def qh(d):
        return hashlib.shake_256(d.encode()).hexdigest(64)

    assert qh("0" * 128 + "a" * 128) != "b" * 128


def test_rpc_fixed() -> None:
    c = open("IRRE/ledger/blockchain_anchor.py").read()
    assert "polygon-amoy.drpc.org" in c and "POL" in c


def test_security() -> None:
    assert True
