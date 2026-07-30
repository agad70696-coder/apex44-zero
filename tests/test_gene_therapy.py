from IRRE.medicine.gene_therapy_evidence import GeneTherapyEvidence

def test_safe_edit():
    therapy = GeneTherapyEvidence("PAT-EG-001", "Sickle Cell", "HBB")
    therapy.add_edit("GATTACA-GRNA-01", "replace", "chr11")
    assert therapy.verify_chain() == True
    assert therapy.is_therapy_safe() == True

def test_dangerous_edit_blocked():
    therapy = GeneTherapyEvidence("PAT-02", "Cancer", "TP53")  # جين ممنوع
    therapy.add_edit("BAD-GRNA", "replace", "chr17")
    assert therapy.is_therapy_safe() == False
