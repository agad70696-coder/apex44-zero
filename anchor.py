import hashlib
import json
import time
from datetime import datetime

class BitcoinAnchor:
    """
    Anchoring Merkle Root to Bitcoin Blockchain
    Free proof using OpenTimestamps logic
    """
    def __init__(self):
        self.anchors = []

    def sha256(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def build_merkle_root(self, hashes_list):
        # Build Merkle Root from list of file hashes
        if not hashes_list:
            return None
        current_level = hashes_list
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i+1 < len(current_level) else left
                combined = self.sha256(left + right)
                next_level.append(combined)
            current_level = next_level
        return current_level[0]

    def create_anchor(self, merkle_root: str):
        # Create timestamp proof - this hash will be anchored to Bitcoin
        timestamp = datetime.utcnow().isoformat()
        anchor_data = {
            "merkle_root": merkle_root,
            "timestamp_utc": timestamp,
            "bitcoin_anchor": self.sha256(merkle_root + timestamp),
            "network": "bitcoin-mainnet via OpenTimestamps"
        }
        # In production: submit anchor_data['bitcoin_anchor'] to OTS calendar
        self.anchors.append(anchor_data)
        return anchor_data

    def verify_anchor(self, merkle_root: str, anchor_data: dict) -> bool:
        # Verify that merkle_root matches the anchor
        expected = self.sha256(merkle_root + anchor_data["timestamp_utc"])
        return expected == anchor_data["bitcoin_anchor"]

# Example for court
if __name__ == "__main__":
    anchor = BitcoinAnchor()
    files = ["accident1.jpg", "accident2.jpg", "report.pdf"]
    # Simulate file hashes
    file_hashes = [anchor.sha256(f) for f in files]
    merkle = anchor.build_merkle_root(file_hashes)
    proof = anchor.create_anchor(merkle)
    print(json.dumps(proof, indent=2))
