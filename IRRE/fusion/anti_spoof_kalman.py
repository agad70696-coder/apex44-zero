import math
import time


# Preserved demonstration values; no vehicle-safety calibration evidence is included.
EARTH_MEAN_RADIUS_METRES = 6_371_000
DEMO_MIN_UPDATE_INTERVAL_SECONDS = 0.1
DEMO_GPS_CAN_DISTANCE_TOLERANCE_METRES = 15.0
DEMO_MIN_CAN_SPEED_MPS = 2.0
DEMO_SPOOF_SCORE_THRESHOLD = 50


class KalmanAntiSpoofV8:
    """V8 Anti-Spoofing: GPS + CAN + IMU Fusion"""

    def __init__(self) -> None:
        self.last_gps = None
        self.last_time = None
        self.last_speed_can = 0.0
        self.spoof_score = 0

    def _distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = EARTH_MEAN_RADIUS_METRES
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return 2 * R * math.asin(math.sqrt(a))

    def update(
        self,
        gps_lat: float,
        gps_lon: float,
        gps_speed: float,
        can_speed: float,
        imu_accel: float,
    ) -> dict[str, bool | str | float | int]:
        now = time.time()
        if self.last_gps is None:
            self.last_gps = (gps_lat, gps_lon)
            self.last_time = now
            self.last_speed_can = can_speed
            return {"spoof": False, "reason": "init"}
        dt = now - self.last_time
        if dt < DEMO_MIN_UPDATE_INTERVAL_SECONDS:
            return {"spoof": False}
        gps_dist = self._distance(self.last_gps[0], self.last_gps[1], gps_lat, gps_lon)
        can_dist = (self.last_speed_can + can_speed) / 2 * dt
        if gps_dist > 83 * dt + 20:
            self.spoof_score += 30
            return {
                "spoof": True,
                "reason": f"IMPOSSIBLE_JUMP {gps_dist:.1f}m",
                "score": self.spoof_score,
            }
        if abs(gps_dist - can_dist) > DEMO_GPS_CAN_DISTANCE_TOLERANCE_METRES and can_speed > DEMO_MIN_CAN_SPEED_MPS:
            self.spoof_score += 10
        else:
            self.spoof_score = max(0, self.spoof_score - 1)
        self.last_gps = (gps_lat, gps_lon)
        self.last_time = now
        self.last_speed_can = can_speed
        return {
            "spoof": self.spoof_score > DEMO_SPOOF_SCORE_THRESHOLD,
            "score": self.spoof_score,
            "gps_dist": gps_dist,
            "can_dist": can_dist,
        }
