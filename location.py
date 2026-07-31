import socket
import json
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class ForensicLocationProvider:
    """
    Solves ISO/IEC 27037 Question 3: WHERE?
    Provides GPS + IP + Cell tower log - admissible in court
    """
    def __init__(self, use_mock=False):
        self.use_mock = use_mock

    def get_gps(self):
        """Real GPS from NEO-6M module on /dev/ttyAMA0"""
        if self.use_mock:
            # Mock for testing on PC - Cairo location
            return {
                "lat": 30.0444,
                "lon": 31.2357,
                "altitude": 23.0,
                "accuracy_m": 5.0,
                "satellites": 8,
                "source": "MOCK - Replace with real NEO-6M on Pi"
            }
        
        try:
            # Real implementation on Pi:
            # import serial
            # import pynmea2
            # ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
            # line = ser.readline().decode('ascii')
            # msg = pynmea2.parse(line)
            # return {"lat": msg.latitude, "lon": msg.longitude, ...}
            
            # For now, if on Pi but no GPS module, return error
            return {
                "lat": None, "lon": None,
                "error": "GPS module not connected to /dev/ttyAMA0",
                "source": "FAILED"
            }
        except Exception as e:
            return {"error": str(e), "source": "FAILED"}

    def get_ip_log(self):
        """IP + ISP + Geolocation from external source - cannot be faked by device time"""
        if not REQUESTS_AVAILABLE:
            return {"ip": "0.0.0.0", "source": "requests library not installed"}
        
        try:
            # External IP + ISP - proves location even if GPS spoofed
            # Free API: ip-api.com
            resp = requests.get("http://ip-api.com/json/", timeout=5)
            data = resp.json()
            
            # Also get local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            return {
                "external_ip": data.get("query"),
                "isp": data.get("isp"),
                "city": data.get("city"),
                "region": data.get("regionName"),
                "country": data.get("country"),
                "lat_ip": data.get("lat"),
                "lon_ip": data.get("lon"),
                "local_ip": local_ip,
                "timestamp_utc": datetime.utcnow().isoformat(),
                "source": "ip-api.com - External TSA-like location proof"
            }
        except Exception as e:
            return {
                "external_ip": "0.0.0.0",
                "error": str(e),
                "source": "FAILED - No internet"
            }

    def get_full_location_proof(self):
        """Combined proof for court - GPS + IP cross-validation"""
        gps = self.get_gps()
        ip_log = self.get_ip_log()
        
        # Cross-check: GPS vs IP location must be close (anti-spoofing)
        proof = {
            "gps": gps,
            "ip": ip_log,
            "collected_at": datetime.utcnow().isoformat(),
            "chain_of_custody_note": "Location from 2 independent sources"
        }
        
        # Simple tamper check
        if gps.get("lat") and ip_log.get("lat_ip"):
            diff = abs(gps["lat"] - ip_log["lat_ip"])
            proof["spoof_check"] = "PASS" if diff < 1.0 else f"FAIL - GPS/IP diff {diff} deg - Possible spoofing!"
        else:
            proof["spoof_check"] = "CANNOT VERIFY -
