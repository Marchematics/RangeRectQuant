from pathlib import Path
import sys,json,time,hashlib,lzma
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'src'))
from corridor import reconstruct,rectangle_max
root=Path(__file__).parent
rng=np.random.default_rng(20261002)
n=512; ii,jj=np.indices((n,n));rows=[]
fields={
 'uniform_integer':rng.integers(0,10001,size=(n,n),dtype=np.int64),
 'sparse_integer':np.where(rng.random((n,n))<.6,0,rng.integers(1,10001,size=(n,n))).astype(np.int64),
 'smooth_saturated':np.clip(np.rint(10000*(.5+.6*np.sin(ii/11)*np.cos(jj/17))),0,10000).astype(np.int64),
 'checkerboard_extremes':np.where((ii+jj)%2,10000,0).astype(np.int64),
}
reconstruct(np.array([[1]],np.int64),1,2,10000);rectangle_max(np.zeros((1,1),np.int64))
def comp(a):return lzma.compress(np.asarray(a,dtype='<u2').view(np.uint8).reshape(-1,2).T.copy().tobytes(),preset=6)
for name,x in fields.items():
    raw=comp(x)
    for eps,q in [(100,20),(1000,200)]:
        t=time.perf_counter();y,info=reconstruct(x,eps//4,q,10000);enc=time.perf_counter()-t
        t=time.perf_counter();err=int(rectangle_max(y-x));aud=time.perf_counter()-t
        z=comp(y//q);r=comp(y%q)
        row={'synthetic_source':name,'shape':[n,n],'epsilon':eps,'step':q,
             'off_lattice':info['off_lattice'],'changed':info['changed'],'max_abs_prefix':info['max_abs_prefix'],
             'exact_max_rectangle':err,'encoder_seconds_warm':enc,'rectangle_audit_seconds':aud,
             'raw_lossless_payload_bytes':len(raw),'coarse_payload_bytes':len(z),'fine_payload_bytes':len(r),
             'payload_saved_pct':100*(1-(len(z)+len(r))/len(raw)),
             'source_sha256':hashlib.sha256(x.astype('<i8').tobytes()).hexdigest(),
             'reconstruction_sha256':hashlib.sha256(y.astype('<i8').tobytes()).hexdigest()}
        rows.append(row);print(row,flush=True)
        np.savez_compressed(root/'results'/f'scale_{name}_{eps}.npz',x=x,y=y)
(root/'results/scale_screen.json').write_text(json.dumps({'warning':'Synthetic, not geographic; payload only, not BA02 packets. Timing is single-run warm quantizer only, not full codec.','rows':rows},indent=2))
