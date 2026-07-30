from IRRE.medicine.regenerative_evidence import RegenerativeEvidence

def test_organ_growth_ok():
    organ = RegenerativeEvidence("HEART-001", "heart", "DNA-DONOR-EG-01")
    organ.add_growth_stage("stem_cell", 1000, 98.5)
    organ.add_growth_stage("differentiation", 50000, 97.0)
    organ.add_growth_stage("maturation", 2000000, 99.0)
    organ.add_growth_stage("ready", 2500000, 99.5)
    assert organ.verify_lineage() == True
    assert organ.is_organ_safe() == True

def test_contamination_detection():
    organ = RegenerativeEvidence("LIVER-01", "liver", "DNA-02")
    organ.add_growth_stage("stem_cell", 1000, 99)
    organ.add_growth_stage("differentiation", 500, 90)  # الخلايا قلت = تلوث
    assert organ.is_organ_safe() == False
