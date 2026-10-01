import hashlib
import unittest
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
from range_rect_quant.packet import encode,decode,HEADER,unpack_u16,pack_u16


class PacketTests(unittest.TestCase):
    def test_roundtrip_fees_odd_mask_and_zeros(self):
        for shape in ((1,1),(1,5),(5,1),(3,5),(8,9)):
            x=(np.arange(np.prod(shape)).reshape(shape)*139)%10001;x.flat[0]=0
            mask=np.zeros(shape,bool);mask.flat[-1]=True;x[mask]=0
            for step in (20,200):
                for mode in ('lossy','zero-preserve','identity'):
                    packet,body,info=encode(x,mask,step,mode,dict(crs='synthetic'))
                    y,m,meta,zero=decode(packet)
                    np.testing.assert_array_equal(mask,m); self.assertFalse(y[mask].any())
                    self.assertEqual(sum(info['fees'].values()),len(packet))
                    detail=info['body_detail'];self.assertEqual(sum(v for k,v in detail.items() if k.endswith('_bytes')),len(body))
                    if mode=='identity':np.testing.assert_array_equal(x,y)
                    if mode=='zero-preserve':self.assertFalse(y[x==0].any());np.testing.assert_array_equal(zero,(x==0)&~mask)
                    e=(y.astype(np.int64)-x).cumsum(0).cumsum(1)
                    self.assertLessEqual(np.abs(e).max(),meta['band'])

    def test_truncation_tamper_and_stream_canonicality(self):
        x=np.array([[0,2],[10000,7]]);mask=np.zeros_like(x,bool)
        packet,body,_=encode(x,mask,20,'lossy',{})
        for p in (packet[:-1],packet+b'0',packet[:60]+bytes([packet[60]^1])+packet[61:]):
            with self.assertRaises(ValueError):decode(p)
        changed=bytearray(packet[:-32]);changed[0]=0
        with self.assertRaises(ValueError):decode(bytes(changed)+hashlib.sha256(changed).digest())
        with self.assertRaises(ValueError):unpack_u16(pack_u16(x)+b'extra',x.shape,10000)
        with self.assertRaises(ValueError):unpack_u16(pack_u16(np.array([[10001]])),(1,1),10000)
        with self.assertRaises(ValueError):unpack_u16(pack_u16(x), (1,1),10000)

    def test_input_contract_rejection(self):
        for x in (np.array([[1.1]]),np.array([[-1]]),np.array([[10001]]),np.array([[np.nan]])):
            with self.assertRaises(ValueError):encode(x,np.zeros(x.shape,bool),20,'lossy',{})
        with self.assertRaises(ValueError):encode(np.array([[1]]),np.ones((1,1),bool),20,'lossy',{})
        with self.assertRaises(ValueError):encode(np.array([[1]]),np.zeros((1,1),bool),21,'lossy',{})

    def test_cold_source_free_worker(self):
        from built_area_metrics import queries
        root=Path(__file__).resolve().parents[1]
        x=np.array([[0,10000,4],[7,0,50]]);mask=np.zeros(x.shape,bool)
        packet,body,info=encode(x,mask,20,'lossy',dict(crs='synthetic'))
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);(folder/'packet').write_bytes(packet)
            np.save(folder/'queries.npy',queries(x.shape))
            run=subprocess.run([sys.executable,str(root/'experiments/worker.py'),str(folder/'packet'),str(folder/'decoded.npz'),
                str(folder/'report.json'),'--queries',str(folder/'queries.npy')],capture_output=True,text=True,timeout=120,
                env=dict(os.environ,PYTHONPATH=str(root/'src')+os.pathsep+str(root/'experiments')))
            self.assertEqual(run.returncode,0,run.stderr)
            with np.load(folder/'decoded.npz') as z:np.testing.assert_array_equal(z['y'],decode(packet)[0])


if __name__ == '__main__':unittest.main()
