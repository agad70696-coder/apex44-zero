# ✅ Release Checklist - لا إصدار بدونها
**إلزامي قبل أي Tag**

### البوابة 1: الجودة
- [ ] `pytest tests/ -v` => 100% نجاح (0 فشل)
- [ ] لا يوجد Critical Bugs مفتوحة في Issues

### البوابة 2: المراجعة
- [ ] مراجعة كود مكتملة (PR Approved)
- [ ] `docs/ENGINEERING_STANDARD_v1.0.md` لم يُكسر

### البوابة 3: التوثيق
- [ ] `README.md` محدث (طريقة التشغيل + Badges)
- [ ] `CHANGELOG.md` محدث بالإصدار الجديد
- [ ] `docs/` محدثة

### البوابة 4: الأداء والأمان
- [ ] `python scripts/benchmark.py` => < 2 ثانية لكل 10k حرف
- [ ] استهلاك الذاكرة < 100MB (check via `memory_profiler`)
- [ ] `python apex_shield.py --self-check` => OK
- [ ] فحص الأمان: لا يوجد `eval()`, `hardcoded key` في الكود

### البوابة 5: النشر
- [ ] `git tag vX.Y.Z` تم إنشاؤه
- [ ] `GitHub Release` مع ملاحظات من CHANGELOG
