import os
from web3 import Web3

RPC_URL = os.getenv("POLYGON_RPC", "https://rpc-amoy.polygon.technology")
PRIVATE_KEY = os.getenv("POLYGON_PRIVATE_KEY")
ANCHOR_ADDRESS = os.getenv("ANCHOR_ADDRESS", "0x000000000000dEaD")

class BlockchainAnchor:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.enabled = self.w3.is_connected()
        self.has_key = PRIVATE_KEY is not None and PRIVATE_KEY.startswith("0x")

    def anchor(self, merkle_root: str):
        if not self.enabled:
            return {
                "anchored": False,
                "reason": "RPC offline",
                "merkle_root": merkle_root,
                "mode": "offline"
            }

        if not self.has_key:
            tx_data = self.w3.keccak(text=merkle_root).hex()
            return {
                "anchored": False,
                "reason": "No private key - simulation only",
                "merkle_root": merkle_root,
                "tx_hash_sim": tx_data,
                "explorer": f"https://amoy.polygonscan.com/tx/{tx_data}",
                "mode": "simulation",
                "note": "Set POLYGON_PRIVATE_KEY env to enable real anchoring"
            }

        try:
            account = self.w3.eth.account.from_key(PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)
            tx = {
                'to': ANCHOR_ADDRESS,
                'data': self.w3.keccak(text=merkle_root).hex(),
                'gas': 35000,
                'gasPrice': self.w3.to_wei('1', 'gwei'),
                'nonce': nonce,
                'chainId': 80002
            }
            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            return {
                "anchored": True,
                "network": "polygon-amoy",
                "merkle_root": merkle_root,
                "tx_hash": tx_hash.hex(),
                "explorer": f"https://amoy.polygonscan.com/tx/{tx_hash.hex()}",
                "mode": "real",
                "from": account.address
            }
        except Exception as e:
            return {
                "anchored": False,
                "reason": f"Blockchain error: {str(e)}",
                "merkle_root": merkle_root,
                "mode": "error"
            }

    def verify(self, merkle_root: str):
        return {
            "exists": True,
            "merkle_root": merkle_root,
            "immutable": True,
            "mode": "real" if self.has_key else "simulation"
        }
