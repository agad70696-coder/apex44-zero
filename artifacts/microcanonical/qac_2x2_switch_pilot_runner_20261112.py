#!/usr/bin/env python3
import json,hashlib,time
from pathlib import Path
import numpy as np, scipy.sparse as sp
H=Path.home(); SRC=H/"apex44-zero/artifacts/audit_workspace/DQ-QAC-ROOT-ONLY-002/B_root_only_6236x1642.npz"; OUT=H/"qac-repair-20261112-realdata-v4"
OBS=2427533; SEEDS=[2026111201,2026111202,2026111203,2026111204]; PROPOSALS=500000; BURN=100000; EVERY=50000
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stat(rows,nr,nc):
 rr=[];cc=[]
 for i,js in enumerate(rows):
  for j in js:rr.append(i);cc.append(j)
 B=sp.csr_matrix((np.ones(len(rr),dtype=np.int64),(rr,cc)),shape=(nr,nc),dtype=np.int64)
 W=(B.T@B).tocsr();W.setdiag(0);W.eliminate_zeros();u=sp.triu(W,k=1).tocoo()
 return int(sum(int(x)*(int(x)-1)//2 for x in u.data)),int(B.nnz),int(W.nnz),int(W.data.max()) if W.nnz else 0
def chain(B,seed):
 rng=np.random.default_rng(seed);nr,nc=B.shape
 rows=[set(B.indices[B.indptr[i]:B.indptr[i+1]].tolist()) for i in range(nr)]
 edges=np.column_stack(B.nonzero()).astype(np.int32)
 accepted=samerow=blocked=0;trace=[];t=time.time()
 for step in range(1,PROPOSALS+1):
  a=int(rng.integers(len(edges)));b=int(rng.integers(len(edges)-1))
  if b>=a:b+=1
  i,j=map(int,edges[a]);k,l=map(int,edges[b])
  if i==k or j==l:samerow+=1
  elif l in rows[i] or j in rows[k]:blocked+=1
  else:
   rows[i].remove(j);rows[k].remove(l);rows[i].add(l);rows[k].add(j)
   edges[a,1]=l;edges[b,1]=j;accepted+=1
  if step>=BURN and (step-BURN)%EVERY==0:
   c,e,w,m=stat(rows,nr,nc);trace.append({"proposal":step,"accepted":accepted,"acceptance_rate":accepted/step,"c4":c,"delta":c-OBS,"edges":e,"projection_nnz":w,"projection_max":m,"elapsed_sec":round(time.time()-t,2)})
   print(f"seed={seed} step={step} accepted={accepted} C4={c}",flush=True)
 rd=np.array([len(x) for x in rows]);cd=np.zeros(nc,dtype=np.int64)
 for x in rows:
  for j in x:cd[j]+=1
 assert np.array_equal(rd,np.asarray(B.sum(1)).ravel()) and np.array_equal(cd,np.asarray(B.sum(0)).ravel())
 return {"seed":seed,"proposals":PROPOSALS,"burn_in":BURN,"accepted":accepted,"same_row_col_reject":samerow,"occupied_cross_reject":blocked,"acceptance_rate":accepted/PROPOSALS,"trace":trace,"exact_degrees_preserved":True}
def main():
 target=OUT/"microcanonical_2x2_pilot.json"
 if target.exists():raise FileExistsError(target)
 raw=sp.load_npz(SRC).tocsr();raw.sum_duplicates();raw.eliminate_zeros();raw.sort_indices()
 if raw.shape!=(6236,1642) or raw.nnz!=44431 or not np.all(raw.data==1):raise RuntimeError("SOURCE_CONTRACT_FAILED")
 B=raw.astype(np.int64);rows=[set(B.indices[B.indptr[i]:B.indptr[i+1]].tolist()) for i in range(B.shape[0])]
 obs,e,w,m=stat(rows,*B.shape)
 if (obs,e,w,m)!=(OBS,44431,148370,514):raise RuntimeError(f"OBSERVED_REPLAY_MISMATCH:{obs,e,w,m}")
 results=[chain(B,s) for s in SEEDS]
 out={"schema":"qac-realdata-fixed-degree-switch-pilot-v1","source_matrix_sha256":sha(SRC),"source_corpus_sha256":"a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46","shape":list(B.shape),"nnz":int(B.nnz),"observed_c4":obs,"projection_nnz":w,"projection_max":m,"null":"Uniform over simple bipartite graphs with exact observed row/column degrees, conditional on irreducibility and symmetric kernel.","kernel":"Uniformly select two distinct edges; switch to the opposite cross-pair iff both new edges are absent; otherwise stay.","chains":results,"interpretation":"PILOT_ONLY: no p-value. Mixing, ESS, burn-in adequacy and tail convergence remain unestablished."}
 target.write_text(json.dumps(out,indent=2)+"\n");print("SAVED",target,"SHA256",sha(target),flush=True)
if __name__=="__main__":main()
