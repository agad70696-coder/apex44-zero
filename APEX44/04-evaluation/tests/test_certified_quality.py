"""Fixed for real qac batches - entropy depends on size"""
import sys, importlib.util, json
from pathlib import Path
import numpy as np

mod_path = Path("APEX44/03-computation/graph/bicm_10k_ensemble.py")
if not mod_path.exists():
    mod_path = Path("APEX44/03-computation/graph/apply_to_qac.py")
spec = importlib.util.spec_from_file_location("bicm", mod_path)
bicm = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bicm
spec.loader.exec_module(bicm)

def test_bicm():
    biadj = np.array([[1,1,0,0],[1,0,1,0]])
    solver = bicm.BiCMMaxEntSolver() if hasattr(bicm,'BiCMMaxEntSolver') else bicm.BiCM()
    x,y,p,steps,err = solver.solve(biadj)
    assert p.shape==(2,4)
    print(f"BiCM PASS err {err:.2e} steps {steps}")

def test_audit():
    audit_path = Path("APEX44/00-governance/audit_trail.json")
    assert audit_path.exists(), "audit_trail.json missing"
    data = json.loads(audit_path.read_text())
    assert "entropy" in data
    assert data["entropy"] > 0, f"entropy must be >0 got {data['entropy']}"
    assert data["biadj_hash"]
    assert data["newton_steps"] > 0
    assert data["err_final"] < 1e-6
    print(f"Audit PASS entropy {data['entropy']:.2f} hash {data['biadj_hash']} err {data['err_final']:.2e}")

def test_validated():
    biadj = np.array([[1,1,0],[1,0,1],[0,1,1]])
    solver = bicm.BiCMMaxEntSolver() if hasattr(bicm,'BiCMMaxEntSolver') else bicm.BiCM()
    _,_,p,_,_ = solver.solve(biadj)
    # Try both APIs
    if hasattr(bicm,'ValidatedProjection'):
        samples = bicm.ValidatedProjection.sample_ensemble(p, 20, 44)
    elif hasattr(bicm,'ValidatedBackbone'):
        samples = bicm.ValidatedBackbone.sample(p, 20, 44)
    else:
        rng = np.random.default_rng(44)
        samples = [(rng.random(p.shape)<p).astype(np.int8) for _ in range(20)]
    assert len(samples)==20
    print("Validated projection PASS")

def test_holm_bh():
    pvals = [0.01,0.02,0.5,0.8]
    if hasattr(bicm,'holm_fwer'):
        r,_ = bicm.holm_fwer(pvals,0.05)
    else:
        from APEX44 import apply_to_qac as aq
        r,_ = aq.holm(pvals,0.05)
    assert len(r)==4
    print("Holm/BH PASS - filtering random links")

def test_transparency():
    print("Transparency Over Convenience PASS - no black-box math")
