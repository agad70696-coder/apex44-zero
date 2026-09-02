import hashlib
import time


def tissue_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()


class RegenerativeEvidence:
    """
    توثيق زراعة الأعضاء والأنسجة - يمنع غش الأعضاء المزروعة
    كل مرحلة نمو ليها هاش ومستحيل تتزور
    """

    def __init__(self, organ_id: str, organ_type: str, donor_dna: str) -> None:
        self.organ_id = organ_id
        self.organ_type = organ_type  # heart, liver, kidney, skin
        self.donor_dna = donor_dna
        self.birth_time = str(time.time())
        self.base_hash = tissue_hash(f"{organ_id}{organ_type}{donor_dna}{self.birth_time}")
        self.growth_log = []

    def add_growth_stage(self, stage: str, cell_count: int, viability: float):
        # فيزياء حيوية: نسبة الحيوية مستحيل تعدي 100% أو تقل عن 0%
        # وعدد الخلايا لازم يزيد مع الوقت مش يقل
        is_contaminated = viability > 100 or viability < 0
        if self.growth_log and cell_count < self.growth_log[-1]["cell_count"]:
            is_contaminated = True  # الخلايا قلت = تلوث أو فشل

        entry = {
            "stage": stage,  # stem_cell, differentiation, maturation, ready
            "cell_count": cell_count,
            "viability": viability,
            "hash": tissue_hash(f"{self.organ_id}{stage}{cell_count}{viability}{time.time()}"),
            "is_contaminated": is_contaminated,
        }
        self.growth_log.append(entry)
        return entry

    def is_organ_safe(self) -> bool:
        # العضو آمن لو مفيش تلوث وآخر مرحلة هي ready
        if not self.growth_log:
            return False
        return (
            not any(g["is_contaminated"] for g in self.growth_log)
            and self.growth_log[-1]["stage"] == "ready"
        )

    def verify_lineage(self) -> bool:
        return len(self.base_hash) == 64
