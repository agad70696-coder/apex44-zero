from IRRE.medicine.personalized_evidence import PersonalizedMedicineEvidence

def test_safe_prescription():
    patient = PersonalizedMedicineEvidence("PAT-101", "CYP2D6-normal", 30, 70.0)
    patient.add_prescription("paracetamol", 500, 95.0)
    assert patient.is_treatment_safe() == True

def test_lethal_combo_detected():
    patient = PersonalizedMedicineEvidence("PAT-102", "CYP2D6-poor", 25, 60.0)
    patient.add_prescription("codeine", 30, 20.0)  # قاتل للي عنده الطفرة دي
    assert patient.is_treatment_safe() == False

def test_overdose():
    patient = PersonalizedMedicineEvidence("PAT-103", "normal", 30, 60.0)
    patient.add_prescription("drugX", 5000, 10)  # 5000 مج لوزن 60 كجم = تسمم
    assert patient.is_treatment_safe() == False
