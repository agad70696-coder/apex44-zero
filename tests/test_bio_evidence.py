from IRRE.bio.genomic_evidence import GenomicEvidence

def test_genomic_evidence():
    evidence = GenomicEvidence("ATCGATCG", "patient_123", "lab_cairo")
    assert evidence.verify() == True

def test_tamper():
    evidence = GenomicEvidence("ATCG", "p1", "lab1")
    evidence.dna_sequence = "TTTT"
    assert evidence.verify() == False
