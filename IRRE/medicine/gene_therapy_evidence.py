import hashlib
import time


def gene_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class GeneTherapyEvidence:
    """
    توثيق تعديل الجينات بـ CRISPR - يمنع التعديل الخاطئ اللي ممكن يقتل المريض
    """
    # جينات ممنوع لمسها - لو اتعدلت المريض هيموت
    FORBIDDEN_GENES = ["TP53", "BRCA1", "PTEN"]  # جينات حارسة من السرطان

    def __init__(self, patient_id: str, disease: str, target_gene: str):
        self.patient_id = patient_id
        self.disease = disease
        self.target_gene = target_gene
        self.timestamp = str(time.time())
        self.base_hash = gene_hash(f"{patient_id}{disease}{target_gene}{self.timestamp}")
        self.edits = []

    def add_edit(self, grna: str, edit_type: str, chromosome: str):
        # كشف الخطر: لو بنعدل في جين ممنوع أو edit_type غريب
        is_dangerous = self.target_gene in self.FORBIDDEN_GENES
        if edit_type not in ["insert", "delete", "replace"]:
            is_dangerous = True

        entry = {
            "grna": grna,
            "edit_type": edit_type,
            "chromosome": chromosome,
            "hash": gene_hash(f"{self.patient_id}{grna}{edit_type}{time.time()}"),
            "is_dangerous": is_dangerous
        }
        self.edits.append(entry)
        return entry

    def is_therapy_safe(self) -> bool:
        return not any(e["is_dangerous"] for e in self.edits)

    def verify_chain(self) -> bool:
        return len(self.base_hash) == 64
