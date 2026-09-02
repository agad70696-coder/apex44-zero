from IRRE.energy.grid_evidence import EnergyGridEvidence


def test_energy_ok() -> None:
    meter = EnergyGridEvidence("METER-CAIRO-001", 0)
    meter.add_reading(100, 20)
    assert meter.verify_grid()
    assert not meter.detect_energy_fraud()


def test_carbon_fraud() -> None:
    meter = EnergyGridEvidence("METER-CAIRO-001", 0)
    meter.add_reading(100, 20)  # طبيعي
    meter.add_reading(-50, 10)  # استهلاك بالسالب = سرقة / تزوير
    assert meter.detect_energy_fraud()


def test_carbon_overclaim() -> None:
    meter = EnergyGridEvidence("METER-01", 0)
    meter.add_reading(10, 100)  # بتدعي توفير 100 كجم CO2 باستهلاك 10 كيلو بس - نصب
    assert meter.detect_energy_fraud()
