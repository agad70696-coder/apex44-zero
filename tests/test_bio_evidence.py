from IRRE.bio.genomic_evidence import GenomicEvidence


def test_genomic_evidence() -> None:
    evidence = GenomicEvidence("ATCGATCG", "patient_123", "lab_cairo")
    assert evidence.verify()


def test_tamper() -> None:
    evidence = GenomicEvidence("ATCG", "p1", "lab1")
    evidence.dna_sequence = "TTTT"
    assert not evidence.verify()
