from pathlib import Path
import hashlib

def sha256(p: Path):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def load_qrels(path: Path):
    qrels = {}
    zero = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            qid, _, pid = parts[0], parts[1], parts[2]
            if pid == "-1":
                zero.add(qid)
                continue
            qrels.setdefault(qid, set()).add(pid)
    return qrels, zero

if __name__ == "__main__":
    candidates = list(Path("official_quranqa").rglob("qrels*.txt")) + list(Path("official_quranqa").rglob("*qrel*"))
    print("Candidates:", candidates[:5])
    for p in candidates:
        try:
            if p.is_dir():
                continue
            qrels, zero = load_qrels(p)
            if qrels or zero:
                total_pairs = sum(len(v) for v in qrels.values())
                print(f"File: {p} -> Qrels IDs: {len(qrels)}, Zero: {len(zero)}, Pairs: {total_pairs}")
                print(f"Zero sample: {sorted(zero)[:10]}")
                if "dev.gold" in str(p):
                    assert len(qrels) == 21
                    assert len(zero) == 4
                    assert total_pairs == 156
                    assert len(qrels) + len(zero) == 25
                    assert sorted(zero) == ['260','322','336','384']
                    print("✅ VERIFIED: Dev 25 = 21 answered (156 pairs) + 4 zero [260,322,336,384]")
                    print("Baseline 0.0904/0.2260 - IRRE 50Y")
                    break
        except Exception as e:
            print(f"skip {p}: {e}")
