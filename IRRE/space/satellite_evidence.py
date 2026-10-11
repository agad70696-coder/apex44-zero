"""Satellite evidence record with a coarse altitude-discontinuity heuristic.

This is not a validated GPS-spoofing detector. The threshold is deliberately simple and
is only intended to support the synthetic regression examples in this repository.
"""
import hashlib
import time


def orbit_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()


class SatelliteEvidence:
    """Record sample trajectory points and flag large altitude discontinuities."""

    ALTITUDE_JUMP_REVIEW_THRESHOLD_KM = 1000.0

    def __init__(
        self, satellite_id: str, altitude: float, latitude: float, longitude: float
    ) -> None:
        self.satellite_id = satellite_id
        self.altitude = altitude
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = str(time.time())
        self.orbit_hash = orbit_hash(
            f"{satellite_id}{altitude}{latitude}{longitude}{self.timestamp}"
        )
        self.trajectory: list[dict[str, object]] = []

    def update_position(self, new_alt: float, new_lat: float, new_lon: float) -> dict[str, object]:
        distance_change = abs(new_alt - self.altitude)
        entry: dict[str, object] = {
            "old_alt": self.altitude,
            "new_alt": new_alt,
            "distance_change": distance_change,
            "hash": orbit_hash(f"{self.satellite_id}{new_alt}{new_lat}{new_lon}{time.time()}"),
            "is_spoofed": distance_change > self.ALTITUDE_JUMP_REVIEW_THRESHOLD_KM,
        }
        self.altitude = new_alt
        self.latitude = new_lat
        self.longitude = new_lon
        self.trajectory.append(entry)
        return entry

    def is_orbit_tampered(self) -> bool:
        return any(bool(log["is_spoofed"]) for log in self.trajectory)

    def verify_orbit(self) -> bool:
        return len(self.orbit_hash) == 64
