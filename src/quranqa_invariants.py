from pathlib import Path
import hashlib

def sha256(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def load_qrels(path: Path):
    qrels={}; zero=set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            qid,_,pid,_=line.split()[:4]
            if pid=="-1":
                zero.add(qid)
                continue
            qrels.setdefault(qid,set()).add(pid)
    return qrels, zero

# البحث عن qrels في المستودع الرسمي
candidates = list(Path("official_quranqa").rglob("qrels*.txt")) + list(Path("official_quranqa").rglob("*qrel*"))
print("Candidates:", candidates[:5])
# جرب أول ملف
for p in candidates:
    try:
        qrels, zero = load_qrels(p)
        if qrels:
            print(f"File: {p} -> Qrels IDs: {len(qrels)}, Zero: {len(zero)}, Pairs: {sum(len(v) for v in qrels.values())}")
            print(f"Zero sample: {sorted(zero)[:5]}")
            # Invariants المطلوبة: Dev 25, pairs 160, zero 4 في Dev
            # Official baseline 0.0904/0.2260 يجب أن يُقاس بنفس الملف
            break
    except Exception as e:
        print(f"skip {p}: {e}")
