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
## 🚗 Hardware Product (Vehicle Mount)

This is now a real device that mounts in a car:

| Part | Price | Job |
| :--- | :--- | :--- |
| **Raspberry Pi 4 + CAN HAT** | ~1500 EGP | Reads speed, brake, steering from car CAN bus |
| **Secure Element ATECC608A** | ~120 EGP | Stores Private Key INSIDE chip, not on SD Card |
| **sensor_interface.py** | Included | Unified driver for CAN / GPS / IMU / Camera |
| **RFC3161 + Bitcoin Anchor** | Free | Real trusted timestamp + Bitcoin proof |

### How it works on car:
1. `sensor_interface.py` detects crash from IMU G-force
2. Reads CAN data (was brake pressed? speed?)
3. Signs with key inside Secure Element (key never leaves chip)
4. Gets RFC3161 timestamp from DigiCert TSA
5. Creates `court_package.json` ready for court
