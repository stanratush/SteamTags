# random weighted graphs, random partitions of very unequal sizes: is γ̂ <= γ_max(K) (K = groups with strength > 0)?
import math, numpy as np
from functools import lru_cache
from scipy.optimize import minimize_scalar
@lru_cache(None)
def gK(K):
    f=lambda wo: -((K-(K-1)*wo)-wo)/(math.log(K-(K-1)*wo)-math.log(wo))
    return -minimize_scalar(f,bounds=(1e-12,1-1e-12),method='bounded',options={'xatol':1e-12}).fun
rng=np.random.default_rng(0); n_ok=n_v=0; worst=0
for t in range(3000):
    n=rng.integers(6,60); W=rng.exponential(1,(n,n))*(rng.random((n,n))<rng.uniform(0.05,0.9)); W=np.triu(W,1); W=W+W.T
    k=W.sum(1); m2=k.sum()
    if m2==0: continue
    K0=rng.integers(2,n+1); p=rng.dirichlet(np.full(K0,rng.uniform(0.05,3))); memb=rng.choice(K0,n,p=p)
    # sometimes make it assortative by a planted structure
    if rng.random()<0.5:
        mask=memb[:,None]==memb[None,:]; W2=W*np.where(mask,rng.uniform(2,20),1.0); W=W2; k=W.sum(1); m2=k.sum()
    A=(W*(memb[:,None]==memb[None,:])).sum(); P=(np.bincount(memb,k)**2).sum()/m2
    K=len(np.unique(memb[k>0]))
    if K<2 or A<=P or A>=m2: continue
    wi=A/P; wo=(m2-A)/(m2-P); gh=(wi-wo)/(math.log(wi)-math.log(wo)); r=gh/gK(K); worst=max(worst,r); n_ok+=1; n_v+= r>1+1e-9
print('checked',n_ok,'violations',n_v,'max ratio',worst)
