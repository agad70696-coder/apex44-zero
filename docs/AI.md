# AI Evidence - توثيق قرارات الذكاء الاصطناعي

## الفكرة
أي قرار ياخده موديل AI لازم يبقى موثق ومستحيل يتزور.
الموديول ده بيحفظ الـ prompt والـ output والوقت وبيعملهم hash.

## المميزات
- يثبت أن الـ AI قال ايه وامتى
- يكشف لو حد لعب في الـ output بعد ما الـ AI طلعه
- يكشف محاولات الـ Prompt Injection (jailbreak)

## الاستخدام
from IRRE.ai.ai_evidence import AIModelEvidence
ev = AIModelEvidence("gpt-4", "اشرح الجاذبية", "الجاذبية هي...")
ev.verify() # True
