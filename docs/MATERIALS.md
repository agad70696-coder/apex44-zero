# Materials Science - توثيق سلامة المواد الذكية

## الفكرة
الجرافين والنانو تيوب حساسة جدا - أي لمسة بتغير موصليتها.
الموديول ده بيحول المادة نفسها لدليل جنائي.

## كيف يعمل
- Graphene sensor بيتسجل بهاش SHA3-256
- أي Stress أو حرارة بتغير الـ conductivity
- لو نزلت تحت 70% -> يعتبر تلاعب فيزيائي (Physical Tampering)

## الاستخدام
from IRRE.materials.nano_evidence import NanoMaterialEvidence
sensor = NanoMaterialEvidence("chip-01", "graphene", 100.0)
sensor.apply_stress(10, 30)
sensor.is_tampered() # False لو سليم
