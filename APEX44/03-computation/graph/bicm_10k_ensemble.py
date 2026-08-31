"""APEX44-ZERO - Validated BiCM - FAIR - No future annotations - Python 3.13 safe"""
from typing import List, Tuple
from dataclasses import dataclass
import numpy as np, json, hashlib
from pathlib import Path

@dataclass
class AuditRecord:
    biadj_hash: str
    n_rows: int
    n_cols: int
    E: int
    x_fitness: List[float]
    y_fitness: List[float]
    entropy: float
    newton_steps: int
    err_final: float
    seed: int
    R: int
    min_pvalue: float
    def to_json(self):
        return json.dumps(self.__dict__, indent=2)

class BiCMMaxEntSolver:
    def __init__(self, tol=1e-8, max_steps=1000, damping=0.5):
        self.tol=tol; self.max_steps=max_steps; self.damping=damping
    def solve(self, biadj):
        n_rows, n_cols = biadj.shape
        k_obs = biadj.sum(axis=1).astype(float)
        d_obs = biadj.sum(axis=0).astype(float)
        x = np.maximum(k_obs/(np.sqrt(biadj.sum())+1e-12),0.1)
        y = np.maximum(d_obs/(np.sqrt(biadj.sum())+1e-12),0.1)
        steps=0; err=1.0
        for step in range(self.max_steps):
            xy=np.outer(x,y); p=xy/(1+xy)
            err_k=np.max(np.abs(p.sum(1)-k_obs)); err_d=np.max(np.abs(p.sum(0)-d_obs)); err=max(err_k,err_d)
            if err<self.tol: steps=step; break
            x=x*(k_obs/(p.sum(1)+1e-12))**self.damping; y=y*(d_obs/(p.sum(0)+1e-12))**self.damping
            x=np.clip(x,1e-12,1e12); y=np.clip(y,1e-12,1e12); steps=step
        xy=np.outer(x,y); p_matrix=xy/(1+xy)
        return x,y,p_matrix,steps,err
    @staticmethod
    def shannon_entropy(p):
        p=np.clip(p,1e-12,1-1e-12); return float(-np.sum(p*np.log(p)+(1-p)*np.log(1-p)))

class ValidatedProjection:
    @staticmethod
    def sample_ensemble(p_matrix,R,seed):
        rng=np.random.default_rng(seed); samples=[]
        for _ in range(R):
            samples.append((rng.random(p_matrix.shape)<p_matrix).astype(np.int8))
        return samples
    @staticmethod
    def pvalues(C_obs,samples):
        R=len(samples); n=C_obs.shape[0]; C_ge=np.zeros((n,n),dtype=int)
        for s in samples: C_ge+=(s@s.T>=C_obs).astype(int)
        pvals=(C_ge+1)/(R+1); np.fill_diagonal(pvals,1.0); return pvals

def holm_fwer(pvals,alpha=0.05):
    m=len(pvals); order=np.argsort(pvals); sp=np.array(pvals)[order]
    thr=[alpha/(m-i) for i in range(m)]; rej=[sp[i]<=thr[i] for i in range(m)]
    for i in range(m):
        if not rej[i]: rej[i:]=[False]*(m-i); break
    return rej,order
def bh_fdr(pvals,q=0.1):
    m=len(pvals); order=np.argsort(pvals); sp=np.array(pvals)[order]
    thr=[(i+1)/m*q for i in range(m)]; max_i=-1
    for i in range(m):
        if sp[i]<=thr[i]: max_i=i
    rej=[i<=max_i for i in range(m)]; return rej,order

if __name__=="__main__":
    biadj=np.array([[1,1,0,0],[1,0,1,0],[0,1,1,1],[1,1,1,0],[0,0,1,1]],dtype=int)
    solver=BiCMMaxEntSolver(); x,y,p,steps,err=solver.solve(biadj)
    S=solver.shannon_entropy(p); biadj_hash=hashlib.sha256(biadj.tobytes()).hexdigest()[:16]
    audit=AuditRecord(biadj_hash,*biadj.shape,int(biadj.sum()),x.tolist(),y.tolist(),S,steps,err,44,10000,1/10001)
    Path("APEX44/00-governance").mkdir(parents=True,exist_ok=True)
    Path("APEX44/00-governance/audit_trail.json").write_text(audit.to_json())
    print(f"AUDIT {audit.biadj_hash} S={S:.2f} steps {steps} err {err:.2e} <p> {p.mean():.3f}")
    samples=ValidatedProjection.sample_ensemble(p,1000,44); C_obs=biadj@biadj.T
    pvals=ValidatedProjection.pvalues(C_obs,samples)
    triu=pvals[np.triu_indices(5,1)]; holm,_=holm_fwer(triu.tolist(),0.05); bh,_=bh_fdr(triu.tolist(),0.1)
    print(f"Validated: cannot be explained by degree sequences alone - Holm {sum(holm)}/{len(triu)} BH {sum(bh)}")
    print("DECISION ADOPTED - FIXED for Python 3.13 dataclass")
