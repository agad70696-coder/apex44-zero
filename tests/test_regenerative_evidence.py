from IRRE.medicine.regenerative_evidence import RegenerativeEvidence


def test_organ_growth_ok() -> None:
    organ = RegenerativeEvidence("HEART-001", "heart", "DNA-DONOR-EG-01")
    organ.add_growth_stage("stem_cell", 1000, 98.5)
    organ.add_growth_stage("differentiation", 50000, 97.0)
    organ.add_growth_stage("maturation", 2000000, 99.0)
    organ.add_growth_stage("ready", 2500000, 99.5)
    assert organ.verify_lineage()
    assert organ.is_organ_safe()


def test_contamination_detection() -> None:
    organ = RegenerativeEvidence("LIVER-01", "liver", "DNA-02")
    organ.add_growth_stage("stem_cell", 1000, 99)
    organ.add_growth_stage("differentiation", 500, 90)  # الخلايا قلت = تلوث
    assert not organ.is_organ_safe()
