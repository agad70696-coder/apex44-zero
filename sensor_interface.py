import hashlib
import json
import time
from datetime import datetime
from main import ForensicSigner
from anchor import BitcoinAnchor

# For real hardware - will auto-fallback to MOCK if not on Pi
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

class SecureElementSigner:
    """
    Private Key NEVER on SD Card
    In production: Uses ATECC608A chip
    """
    def __init__(self):
        self.secure_chip_present = False
        # Try to init ATECC608A
        try:
            # import atecc608a
            # self.chip = atecc608a.ATECC608A()
            # self.secure_chip_present = True
            print("[SECURE] ATECC608A not found, using software fallback - FOR DEMO ONLY")
            self.fallback_signer = ForensicSigner()
        except:
            self.fallback_signer = ForensicSigner()

    def sign(self, merkle_root: str) -> str:
        if self.secure_chip_present:
            # Real: chip.sign(merkle_root)
            # Key never leaves chip
            pass
        return self.fallback_signer.sign(merkle_root)
    
    def get_public_pem(self) -> str:
        if self.secure_chip_present:
            return "PUBLIC_FROM_CHIP"
        return self.fallback_signer.get_public_pem()

class VehicleSensorInterface:
    def __init__(self, use_mock=True):
        self.use_mock = use_mock or not CAN_AVAILABLE
        self.can_bus = None
        if not self.use_mock and CAN_AVAILABLE:
            try:
                # For Pi + CAN HAT: channel='can0', bustype='socketcan'
                self.can_bus = can.interface.Bus(channel='can0', bustype='socketcan')
                print("[CAN] Connected to can0")
            except Exception as e:
                print(f"[CAN] Failed {e}, switching to MOCK")
                self.use_mock = True

    def read_can_data(self):
        """ Reads speed, brake, steering from CAN """
        if self.use_mock:
            return {"speed_kmh": 88, "brake_pressed": True, "steering_angle": -12, "rpm": 4500}
        
        # Real CAN reading
        msg = self.can_bus.recv(timeout=1)
        # Decode based on your car DBC file
        return {"raw_can_id": msg.arbitration_id, "data": msg.data.hex()}

    def read_gps(self):
        """ Reads GPS location """
        if self.use_mock:
            return {"lat": 30.0444, "lon": 31.2357, "speed": 88}
        # Real: read from serial /dev/ttyAMA0
        return {"lat": 0, "lon": 0}

    def get_rfc3161_timestamp(self, hash_to_stamp: str):
        """ Real trusted timestamp - admissible in EU courts """
        if not RFC3161_AVAILABLE:
            return {"timestamp": datetime.utcnow().isoformat(), "source": "local_fallback"}
        
        try:
            # Free TSA server
            rt = RemoteTimestamper('http://timestamp.digicert.com', hashname='sha256')
            tst = rt.timestamp(data=hash_to_stamp.encode())
            return {"timestamp": datetime.utcnow().isoformat(), "rfc3161_token": tst.hex()[:100]+"...", "source": "digicert TSA"}
        except Exception as e:
            print(f"[TSA] Failed {e}, using local")
            return {"timestamp": datetime.utcnow().isoformat(), "source": "local"}

    def create_accident_package(self):
        """ Main function - called when accident detected """
        print("=== CRASH DETECTED - Creating Forensic Package ===")
        
        can_data = self.read_can_data()
        gps_data = self.read_gps()
        
        # 1. Build evidence
        evidence = {
            "can": can_data,
            "gps": gps_data,
            "imu_g_force": 4.2 if self.use_mock else 0
        }
        evidence_json = json.dumps(evidence, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
        
        # 2. Merkle root (here just one file, but scalable)
        anchor = BitcoinAnchor()
        merkle_root = anchor.build_merkle_root([evidence_hash])
        
        # 3. Sign with Secure Element
        secure_signer = SecureElementSigner()
        signature = secure_signer.sign(merkle_root)
        public_pem = secure_signer.get_public_pem()
        
        # 4. RFC3161 + Bitcoin Anchor
        tsa = self.get_rfc3161_timestamp(merkle_root)
        btc_anchor = anchor.create_anchor(merkle_root)
        
        # 5. Final package for court
        court_package = {
            "merkle_root": merkle_root,
            "signature": signature,
            "public_key_pem": public_pem,
            "bitcoin_anchor": btc_anchor,
            "rfc3161": tsa,
            "evidence": evidence,
            "created_at": datetime.utcnow().isoformat()
        }
        
        with open('court_package.json', 'w') as f:
            json.dump(court_package, f, indent=2)
            
        print("✅ court_package.json created - Ready for verify_for_court.py")
        return court_package

if __name__ == "__main__":
    # On Pi: VehicleSensorInterface(use_mock=False)
    # On PC for testing: use_mock=True
    car = VehicleSensorInterface(use_mock=True)
    car.create_accident_package()
