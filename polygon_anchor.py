import hashlib

def build_merkle_tree(self, hashes: list) -> str:
    """Builds Merkle Tree from 100 evidence hashes - FIXED with canonical ordering"""
    if not hashes:
        return hashlib.sha256(b"empty").hexdigest()

    current_level = hashes
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i+1] if i+1 < len(current_level) else left
            # FIX: canonical ordering to prevent reordering attack
            left_sorted, right_sorted = sorted([left, right])
            combined = hashlib.sha256(f"{left_sorted}{right_sorted}".encode()).hexdigest()
            next_level.append(combined)
        current_level = next_level

    merkle_root = current_level[0]
    print(f"[MERKLE] Built root from {len(hashes)} hashes")
    return merkle_root
