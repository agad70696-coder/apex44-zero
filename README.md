# APEX44 Zero - Forensic Integrity Protocol

> **Tamper-Evident Evidence Chain for Automotive & 3D-Printed Parts**

APEX44 Zero secures digital evidence with military-grade cryptography, making forensic reports impossible to forge.

### 🔬 Scientific Core (v2.0)
- **ECDSA SECP256K1:** Each evidence is signed with a private key. No signature = Fake evidence.
- **Merkle Tree Root:** 100 evidence hashes combined into 1 Root. Changing 1 byte changes the Root.
- **RFC 3161 Timestamp Ready:** For trusted time authority integration.

### How it detects forgery?
If someone changes a single log from "120km/h" to "60km/h", the Merkle Root changes completely and `verify()` returns `False`.

### For Insurance Companies
We provide a PDF report with:
- Merkle Root
- ECDSA Signature
- Verification QR Code

Built by Amr Gad - Cairo, Egypt.
