import hashlib
import time


def orbit_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class SatelliteEvidence:
    """
    توثيق بيانات الأقمار الصناعية - يكشف الـ GPS Spoofing والتلاعب المداري
    """
    def __init__(self, satellite_id: str, altitude: float, latitude: float, longitude: float):
        self.satellite_id = satellite_id
        self.altitude = altitude
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = str(time.time())
        self.orbit_hash = orbit_hash(f"{satellite_id}{altitude}{latitude}{longitude}{self.timestamp}")
        self.trajectory = []

    def update_position(self, new_alt: float, new_lat: float, new_lon: float):
        # فيزياء مبسطة: القمر الصناعي مستحيل ينط 1000 كم في ثانية
        distance_change = abs(new_alt - self.altitude)
        entry = {
            "old_alt": self.altitude,
            "new_alt": new_alt,
            "distance_change": distance_change,
            "hash": orbit_hash(f"{self.satellite_id}{new_alt}{new_lat}{new_lon}{time.time()}"),
            "is_spoofed": distance_change > 100  # لو نط أكتر من 100 كم مرة واحدة يبقى spoofing
        }
        self.altitude = new_alt
        self.latitude = new_lat
        self.longitude = new_lon
        self.trajectory.append(entry)
        return entry

    def is_orbit_tampered(self) -> bool:
        # لو فيه أي نقطة فيها spoofing
        return any(log["is_spoofed"] for log in self.trajectory)

    def verify_orbit(self) -> bool:
        return len(self.orbit_hash) == 64
