import os
import re

print("=== فحص إصلاحات v3.0 ===")

checks = {
    "1. ForensicSigner اتمسح؟": True,
    "2. chain = [] اتلغى؟": True,
    "3. rfc3161ng موجود؟": False,
    "4. Merkle Root بـ hashlib؟": False,
    "5. cryptography مستخدم؟": False
}

# فحص كل ملفات.py
for root, dirs, files in os.walk("."):
    if ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

                # 1. ForensicSigner الوهمي لسه موجود؟
                if "class ForensicSigner" in content and "cryptography" not in content:
                    print(f"❌ لقيت ForensicSigner وهمي في {path}")
                    checks["1. ForensicSigner اتمسح؟"] = False

                # 2. chain = [] لسه موجود؟
                if re.search(r'chain\s*=\s*\[\s*\]', content):
                    # استثناء: لو في تعليق
                    if "chain = []" not in content.split("#")[0]:
                        pass
                    else:
                        # لو هو self.chain = [] في __init__ بتاع القديم
                        if "self.chain = []" in content:
                            print(f"❌ لقيت self.chain = [] في {path}")
                            checks["2. chain = [] اتلغى؟"] = False

                # 4. Merkle
                if "hashlib.sha256" in content and "merkle" in content.lower():
                    checks["4. Merkle Root بـ hashlib؟"] = True

                # 5. cryptography
                if "from cryptography" in content or "import cryptography" in content:
                    checks["5. cryptography مستخدم؟"] = True

# 3. rfc3161ng
for root, dirs, files in os.walk("."):
    for f in files:
        if f in ["trusted_timestamp.py", "requirements.txt", "apex44_v3.py"]:
            path = os.path.join(root, f)
            try:
                with open(path, 'r', errors='ignore') as file:
                    if "rfc3161ng" in file.read():
                        checks["3. rfc3161ng موجود؟"] = True
            except:
                pass

print("\n=== النتيجة ===")
for k,v in checks.items():
    print(f"{'✅ PASS' if v else '❌ FAIL'} - {k}")

if all(checks.values()):
    print("\n🎉 كل الإصلاحات اتعملت - انت v3.0 Evidence Edition 4/4")
else:
    print("\n⚠️ لسه في حاجات ناقصة - شوف الـ FAIL فوق")
