import hashlib


def personal_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()


class PersonalizedMedicineEvidence:
    """
    Synthetic evidence object used by repository tests.

    This is test/demo logic, not clinical dosing guidance.
    """

    LETHAL_COMBOS = {
        "CYP2D6-poor": ["codeine", "tramadol"],
        "HLA-B*58:01": ["allopurinol"],
    }

    MAX_DOSE_MG_PER_KG = 50.0

    def __init__(
        self,
        patient_id: str,
        genome_marker: str,
        age: int,
        weight: float,
    ) -> None:
        if weight <= 0:
            raise ValueError("weight must be positive")

        self.patient_id = patient_id
        self.genome_marker = genome_marker
        self.age = age
        self.weight = weight
        self.prescriptions: list[dict[str, float | str]] = []

        self.base_hash = personal_hash(
            f"{patient_id}{genome_marker}{age}{weight}"
        )

    def add_prescription(
        self,
        drug: str,
        dose_mg: float,
        confidence: float,
    ) -> None:
        if dose_mg < 0:
            raise ValueError("dose_mg must be non-negative")
        if not 0.0 <= confidence <= 100.0:
            raise ValueError("confidence must be between 0 and 100")

        self.prescriptions.append(
            {
                "drug": drug,
                "dose_mg": float(dose_mg),
                "confidence": float(confidence),
            }
        )

    def is_treatment_safe(self) -> bool:
        lethal_drugs = set(self.LETHAL_COMBOS.get(self.genome_marker, []))

        for prescription in self.prescriptions:
            drug = str(prescription["drug"])
            dose_mg = float(prescription["dose_mg"])

            if drug in lethal_drugs:
                return False

            dose_per_kg = dose_mg / self.weight
            if dose_per_kg > self.MAX_DOSE_MG_PER_KG:
                return False

        return True
