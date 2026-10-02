import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from controls.dense_native import core,added_grid,ORIGINAL
from experiments.run_review_revision import dense_grid
from experiments.run_review_dense import DenseDecoder
from research_common import environment
import built_area_discrete_packet


class DenseReview(unittest.TestCase):
    def test_isolated_allowlist_preserves_original_adapter(self):
        self.assertEqual(added_grid(),dense_grid())
        self.assertEqual(core.grid(),ORIGINAL+added_grid())
        self.assertEqual(built_area_discrete_packet.grid(),ORIGINAL)
        self.assertEqual(len(added_grid()),106)

    def test_paid_cold_decoder_with_no_source(self):
        x=np.arange(64,dtype=np.int64).reshape(8,8);mask=np.zeros(x.shape,bool)
        cfg=next(c for c in ORIGINAL if c['backend']=='integer-lzma')
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,environment()):
            folder=Path(t);blob,fees=core.encode(x,mask,cfg,{},folder/'body',[])
            packet=folder/'field.packet';packet.write_bytes(blob);decoder=DenseDecoder(folder/'decoder')
            try:y,m,p,info=decoder.decode(packet)
            finally:decoder.close()
            np.testing.assert_array_equal(y,x);np.testing.assert_array_equal(m,mask)
            np.testing.assert_array_equal(p,mask)
            self.assertFalse(info['source_provided'])
            self.assertEqual(sum(v for k,v in fees.items() if k.endswith('_bytes')),len(blob))
