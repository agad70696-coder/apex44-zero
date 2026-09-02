from IRRE.materials.nano_evidence import NanoMaterialEvidence


def test_nano_creation() -> None:
    sensor = NanoMaterialEvidence("G-001", "graphene", 100.0)
    assert sensor.verify_chain()
    assert not sensor.is_tampered()


def test_nano_tamper_detection() -> None:
    sensor = NanoMaterialEvidence("G-001", "graphene", 100.0)
    sensor.apply_stress(stress_level=50, temperature=100)  # ضغط وحرارة عالية
    assert sensor.is_tampered()
    assert len(sensor.logs) == 1
