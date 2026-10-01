import tempfile
import unittest
from pathlib import Path

import numpy as np

from experiments.decode_delivered import decode_file
from controls import research_packet, water_packet
from built_area_discrete_packet import encode as encode_native


class DeliveryDecoder(unittest.TestCase):
    def test_three_carriers_and_no_overwrite(self):
        x = np.array([[0, 17, 100], [9, 45, 81]], np.int64)
        mask = np.zeros(x.shape, bool)
        blobs = [research_packet.encode(x, mask, 5, 100, {}, {})[0],
                 water_packet.encode(x, mask, {'backend':'u8-lzma', 'predictor':'raw', 'preset':6}, {}, [])[0]]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            body = folder / 'native.body'
            blobs.append(encode_native(x, mask, {'backend':'integer-lzma','predictor':'raw',
                'shuffle':False,'preset':6,'transform':'direct'}, {}, body, [])[0])
            for i, blob in enumerate(blobs):
                packet, output = folder / f'{i}.packet', folder / f'{i}.npz'
                packet.write_bytes(blob)
                receipt = decode_file(packet, output)
                self.assertFalse(receipt['source_provided'])
                with np.load(output) as z:
                    np.testing.assert_array_equal(z['y'], x)
                with self.assertRaises(ValueError):
                    decode_file(packet, output)
                packet.write_bytes(blob[:-1] + bytes([blob[-1] ^ 1]))
                with self.assertRaises(ValueError):
                    decode_file(packet, folder / f'bad{i}.npz')
