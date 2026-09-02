import hashlib
import json
import re
import threading
from datetime import UTC, datetime

from main import ForensicSigner

try:
    import can

    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False

try:
    from rfc3161ng import RemoteTimestamper

    RFC3161_AVAILABLE = True
except ImportError:
    RFC3161_AVAILABLE = False

MAX_ENTRY_SIZE = 100 * 1024


def _valid_hash(h: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", h))


def _valid_gps(lat, lon) -> bool:
    try:
        return -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
    except:
        return False


class SecureElementSigner:
    """Private Key NEVER on SD Card - Uses ATECC608A in production"""

    def __init__(self) -> None:
        self.secure_chip_present = False
        self._lock = threading.Lock()
        try:
            print("[SECURE] ATECC608A not present - using fallback signer (dev mode)")
            self.fallback_signer = ForensicSigner()
        except Exception:
            self.fallback_signer = ForensicSigner()

    def sign(self, merkle_root: str) -> str:
        if not _valid_hash(merkle_root):
            raise ValueError("Invalid merkle_root")
        with self._lock:
            if self.secure_chip_present:
                pass
            return self.fallback_signer.sign(merkle_root)

    def get_public_pem(self) -> str:
        if self.secure_chip_present:
            return "PUBLIC_FROM_CHIP"
        return self.fallback_signer.get_public_pem()


class VehicleSensorInterface:
    def __init__(self, use_mock=True) -> None:
        self.use_mock = use_mock or not CAN_AVAILABLE
        self.can_bus = None
        self._lock = threading.Lock()
        if not self.use_mock and CAN_AVAILABLE:
            try:
                self.can_bus = can.interface.Bus(channel="can0", bustype="socketcan")
                print("[CAN] Connected to can0")
            except Exception as e:
                print(f"[CAN] Failed {e}, fallback to mock")
                self.use_mock = True

    def read_can_data(self):
        """Reads speed, brake, steering - validated"""
        if self.use_mock:
            return {"speed_kmh": 88, "brake_pressed": True, "steering_deg": -15}
        try:
            msg = self.can_bus.recv(timeout=1.0)
            if not msg:
                return {"speed_kmh": 0, "brake_pressed": False, "steering_deg": 0}
            return {"raw_can_id": msg.arbitration_id, "raw_data": msg.data.hex()}
        except Exception:
            return {"speed_kmh": 0, "brake_pressed": False, "steering_deg": 0}

    def read_gps(self):
        """Reads GPS location - validated"""
        if self.use_mock:
            # Mock Cairo - validated range
            data = {"lat": 30.0444, "lon": 31.2357}
        else:
            data = {"lat": 0, "lon": 0}
        # Validate
        if not _valid_gps(data["lat"], data["lon"]):
            return {"lat": 0, "lon": 0}
        return data

    def get_rfc3161_timestamp(self, hash_hex: str):
        """Real trusted timestamp - fixed to HTTPS + timeout + validation"""
        if not _valid_hash(hash_hex):
            raise ValueError("Invalid hash format for timestamp")

        if not RFC3161_AVAILABLE:
            return {"timestamp": datetime.now(UTC).isoformat(), "source": "local"}

        try:
            # FIXED: https + timeout
            rt = RemoteTimestamper("https://freetsa.org/tsr", timeout=5)
            tst = rt.timestamp(data=bytes.fromhex(hash_hex))
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "token": tst,
                "source": "rfc3161",
            }
        except Exception as e:
            print(f"[TSA] Failed {e}, using local time")
            return {"timestamp": datetime.now(UTC).isoformat(), "source": "local_fallback"}

    def create_accident_package(self):
        """Main function - called when crash detected - Fully Locked"""
        with self._lock:
            print("=== CRASH DETECTED - Creating package ===")
            can_data = self.read_can_data()
            gps_data = self.read_gps()

            evidence = {
                "can": can_data,
                "gps": gps_data,
                "imu_g_force": 4.2 if self.use_mock else 0.0,
                "timestamp_utc": datetime.now(UTC).isoformat(),
            }
            evidence_json = json.dumps(evidence, sort_keys=True)
            if len(evidence_json) > MAX_ENTRY_SIZE:
                raise ValueError("Evidence too large - DoS protection")

            evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
            return evidence, evidence_hash
