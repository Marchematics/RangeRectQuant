"""Source-free persistent decoder. Requests name packets, never source fields."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np
from controls.research_packet import decode


def main():
    for line in sys.stdin:
        try:
            request=json.loads(line); started=time.perf_counter()
            packet=Path(request['packet']).read_bytes(); commands=[]
            if packet[:4]==b'BA02':
                from built_area_discrete_packet import decode as native_decode
                y,mask,meta,_=native_decode(packet,commands)
                y=y.astype(np.int64); protected=mask.copy()
            else:
                y,mask,protected,meta=decode(packet)
            seconds=time.perf_counter()-started
            target=Path(request['output'])
            if target.exists():
                raise ValueError('Refuse overwrite decoded field')
            np.savez(target,y=y,mask=mask,protected=protected)
            result=dict(status='DECODED',source_provided=False,meta=meta,
                packet_sha256=hashlib.sha256(packet).hexdigest(),
                numerator_sha256=hashlib.sha256(y.astype('<i8').tobytes()).hexdigest(),
                decode_seconds=seconds,native_commands=commands,
                process_peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                rss_scope='macOS peak bytes; persistent source-free decoder')
        except Exception as e:
            result=dict(status='FAIL',error=type(e).__name__+': '+str(e))
        print(json.dumps(result,allow_nan=False),flush=True)


if __name__=='__main__':
    main()
