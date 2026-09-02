from IRRE.quantum.quantum_sensing_evidence import QuantumSensingEvidence


def test_sensor_ok() -> None:
    sensor = QuantumSensingEvidence("Q-GRAV-01", "Aswan Dam")
    sensor.add_reading(9.81, 0.99)
    assert sensor.is_sensor_intact()
