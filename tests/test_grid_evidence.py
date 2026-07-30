from IRRE.energy.grid_evidence import EnergyGridEvidence

def test_energy_ok():
    meter = EnergyGridEvidence("METER-CAIRO-001", 0)
    meter.add_reading(100, 20)
    assert meter.verify_grid() == True
    assert meter.detect_energy_fraud() == False

def test_carbon_fraud():
    meter = EnergyGridEvidence("METER-CAIRO-001", 0)
    meter.add_reading(100, 20)  # طبيعي
    meter.add_reading(-50, 10)  # استهلاك بالسالب = سرقة / تزوير
    assert meter.detect_energy_fraud() == True

def test_carbon_overclaim():
    meter = EnergyGridEvidence("METER-01", 0)
    meter.add_reading(10, 100)  # بتدعي توفير 100 كجم CO2 باستهلاك 10 كيلو بس - نصب
    assert meter.detect_energy_fraud() == True
