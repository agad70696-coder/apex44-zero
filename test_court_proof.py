import hashlib
from main import ForensicSigner

def merkle_root(h_list):
    cur = h_list[:]
    while len(cur) > 1:
        if len(cur) % 2 == 1:
            cur.append(cur[-1])
        nxt = []
        for i in range(0, len(cur), 2):
            nxt.append(hashlib.sha256((cur[i]+cur[i+1]).encode()).hexdigest())
        cur = nxt
    return cur[0]

print("=== محاكاة محكمة - APEX44 Zero ===\n")

# 1. الضابط بيجمع أدلة حقيقية
print("1. الضابط صور الحادثة:")
h1 = hashlib.sha256(b"car-crash-image-1.jpg").hexdigest()
h2 = hashlib.sha256(b"speed-log-120kmh.json").hexdigest()
h3 = hashlib.sha256(b"lidar-scan-data").hexdigest()
root_original = merkle_root([h1, h2, h3])
print(f" Merkle Root الأصلي: {root_original[:20]}...\n")

# 2. الضابط بيمضي - Private بيفضل معاه
officer = ForensicSigner()
public_for_court = officer.get_public_pem()
signature = officer.sign(root_original)

print("2. الضابط مضى التقرير:")
print(f" Public Key للمحكمة:\n {public_for_court[:60]}...\n")
print(f" التوقيع: {signature[:30]}...\n")

# 3. المحكمة بتتأكد - قبل التزوير
is_valid = officer.verify(root_original, signature, public_for_court)
print(f"3. المحكمة بتفحص التقرير الأصلي: {is_valid} -> مقبول ✅\n")

# 4. محاولة تزوير - حد غير سرعة العربية من 120 لـ 60
print("4. محاولة تزوير! حد غير اللوج من 120kmh لـ 60kmh")
h2_fake = hashlib.sha256(b"speed-log-60kmh.json").hexdigest()
root_fake = merkle_root([h1, h2_fake, h3])
print(f" Merkle Root المزور: {root_fake[:20]}...\n")

# 5. المحكمة بتكشف التزوير بنفس التوقيع والـ Public بس
is_valid_after = officer.verify(root_fake, signature, public_for_court)
print(f"5. المحكمة بتفحص بعد التزوير: {is_valid_after} -> مرفوض ❌ تزوير مكشوف!")
print("\n=== الحكم: تم كشف التلاعب بدون الحاجة للـ Private Key ===")
