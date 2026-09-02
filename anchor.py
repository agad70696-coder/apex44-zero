import hashlib


class RealBlockchainAnchor:
    def build_merkle_tree(self, hashes: list) -> str:
        if not hashes:
            return ""
        if len(hashes) == 1:
            return hashes[0]
        current_level = hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                # الحماية من هجوم الترتيب
                pair = sorted([left, right])
                combined = hashlib.sha256(f"{pair[0]}{pair[1]}".encode()).hexdigest()
                next_level.append(combined)
            current_level = next_level
        return current_level[0]
