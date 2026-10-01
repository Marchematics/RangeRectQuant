"""Only packets are accepted by this source-free percentage decoder."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from controls.research_packet import decode
from controls.water_packet import decode as decode_native


for line in sys.stdin:
    try:
        request=json.loads(line); started=time.perf_counter(); commands=[]
        blob=Path(request['packet']).read_bytes()
        y,m,p,meta=decode_native(blob,commands) if blob[:4]==b'RWS1' else decode(blob)
        elapsed=time.perf_counter()-started
        target=Path(request['output'])
        if target.exists(): raise ValueError('Refuse overwrite decoded source')
        np.savez(target,y=y,mask=m,protected=p)
        result=dict(status='DECODED',source_provided=False,meta=meta,decode_seconds=elapsed,
                    numerator_sha256=hashlib.sha256(y.astype('<i8').tobytes()).hexdigest(),native_commands=commands)
    except Exception as e: result=dict(status='FAIL',error=str(e))
    print(json.dumps(result,allow_nan=False),flush=True)
