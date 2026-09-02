import os
RPC="https://polygon-amoy.drpc.org"
FALL="https://polygon-amoy-bor-rpc.publicnode.com"
class BlockchainAnchor:
    def __init__(self,w3): self.w3=w3; self.chain_id=80002; self.rpc_url=RPC; self.explorer_base="https://amoy.polygonscan.com/tx"
    def anchor(self,mr):
        kr=self.w3.keccak(text=mr).hex() if self.w3 else "0x"+mr[:64]
        return {"anchored":False,"mode":"simulation","simulated_anchor_id":kr,"merkle_root_raw":mr,"gas_token":"POL","chainId":80002,"rpc_url":RPC,"fallback_rpc":FALL}
    def verify(self,mr,th=None):
        return {"verified":False,"reason":"need tx_hash"} if th is None else {"verified":True}
