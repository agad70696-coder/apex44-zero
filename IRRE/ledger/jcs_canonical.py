import json

try:
    import rfc8785

    HAS_JCS = True

    def canonicalize_jcs(d) -> bytes:
        # rfc8785.dumps returns bytes per spec - do NOT .encode()
        result = rfc8785.dumps(d)
        if isinstance(result, bytes):
            return result
        return result.encode("utf-8")

    def is_jcs() -> bool:
        return True

    def canonical_hash(d) -> str:
        import hashlib

        return hashlib.sha256(canonicalize_jcs(d)).hexdigest()
except ImportError:
    HAS_JCS = False

    def canonicalize_jcs(d) -> bytes:
        return json.dumps(d, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )

    def is_jcs() -> bool:
        return False

    def canonical_hash(d) -> str:
        import hashlib

        return hashlib.sha256(canonicalize_jcs(d)).hexdigest()
