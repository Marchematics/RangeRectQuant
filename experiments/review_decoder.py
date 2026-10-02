"""Cold packet-only endpoint for the additional review experiments."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from controls.review_packet import decode as review_decode
from controls.research_packet import decode as rrq_decode


def main():
    for line in sys.stdin:
        try:
            request=json.loads(line);blob=Path(request['packet']).read_bytes();commands=[]
            start=time.perf_counter()
            if blob[:4]==b'RRA3':y,m,p,meta=review_decode(blob)
            elif blob[:4]==b'RRF2':y,m,p,meta=rrq_decode(blob)
            elif blob[:4]==b'BA02':
                from built_area_discrete_packet import decode
                y,m,meta,_=decode(blob,commands);p=m.copy();y=y.astype(np.int64)
            else:raise ValueError('File carrier')
            target=Path(request['output'])
            if target.exists():raise ValueError('Output exists')
            np.savez(target,y=y,mask=m,protected=p)
            info=dict(status='DECODED',source_provided=False,meta=meta,
                      packet_sha256=hashlib.sha256(blob).hexdigest(),
                      numerator_sha256=hashlib.sha256(y.astype('<i8').tobytes()).hexdigest(),
                      native_commands=commands,decode_seconds=time.perf_counter()-start)
        except Exception as error:info=dict(status='FAIL',error=type(error).__name__+': '+str(error))
        print(json.dumps(info,allow_nan=False),flush=True)


if __name__=='__main__':main()
