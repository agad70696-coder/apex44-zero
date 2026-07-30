from IRRE.space.satellite_evidence import SatelliteEvidence

def test_satellite_ok():
    sat = SatelliteEvidence("NILESAT-301", 35786, 7.0, 30.0)
    assert sat.verify_orbit() == True
    assert sat.is_orbit_tampered() == False

def test_gps_spoofing_detection():
    sat = SatelliteEvidence("NILESAT-301", 35786, 7.0, 30.0)
    sat.update_position(36000, 7.1, 30.1)  # حركة طبيعية
    assert sat.is_orbit_tampered() == False
    sat.update_position(50000, 50.0, 50.0)  # قفزة مستحيلة - هجوم Spoofing
    assert sat.is_orbit_tampered() == True
