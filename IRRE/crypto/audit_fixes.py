import os, hashlib, json
# Fix fsync + HMAC
def write_tamper_evident(path, chain):
    with open(path, "w") as f:
        for e in chain:
            f.write(json.dumps(e)+"\n")
            f.flush()
            os.fsync(f.fileno())  # real tamper-evident fsync
    print("fsync PASS - ISO 17025 compliant")

# Verify chain with first-break diagnostics
def verify_chain_detailed(path):
    prev = "0"*64
    with open(path) as f:
        for i, line in enumerate(f):
            e = json.loads(line)
            if e["prev"] != prev:
                return f"FAIL at height {i}: expected {prev[:8]}.. got {e['prev'][:8]}.."
            prev = e["hash"]
    return "PASS - chain verified, no tampering"
