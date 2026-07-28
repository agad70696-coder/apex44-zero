import os, sys, subprocess

def check(cmd, name):
    print(f"🔍 {name}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {name} نجح")
        return True
    except:
        print(f"❌ {name} فشل - الإصدار ممنوع")
        return False

checks = []
checks.append(check("pytest tests/ -q", "جميع الاختبارات 100%"))
checks.append(os.path.exists("README.md"))
checks.append(os.path.exists("CHANGELOG.md"))
checks.append(check("python apex_shield.py --self-check", "قابلية إعادة التشغيل"))
# أضف هنا فحص الأداء والذاكرة لاحقاً

if all(checks):
    print("\n🟢 مسموح بالنشر - كل البوابات نجحت")
else:
    print("\n🔴 ممنوع النشر - راجع RELEASE_CHECKLIST")
    sys.exit(1)
