"""Packet-only decoder with the declared denser native setting allowlist."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from controls.dense_native import decode

for line in sys.stdin:
    try:
        request=json.loads(line);blob=Path(request['packet']).read_bytes();commands=[]
        start=time.perf_counter();y,m,meta,_=decode(blob,commands);y=y.astype(np.int64)
        target=Path(request['output'])
        if target.exists():raise ValueError('Output exists')
        np.savez(target,y=y,mask=m,protected=m)
        info=dict(status='DECODED',source_provided=False,meta=meta,
                  packet_sha256=hashlib.sha256(blob).hexdigest(),
                  numerator_sha256=hashlib.sha256(y.astype('<i8').tobytes()).hexdigest(),
                  native_commands=commands,decode_seconds=time.perf_counter()-start)
    except Exception as error:info=dict(status='FAIL',error=type(error).__name__+': '+str(error))
    print(json.dumps(info,allow_nan=False),flush=True)
