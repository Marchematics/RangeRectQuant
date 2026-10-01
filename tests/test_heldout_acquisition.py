import copy
import json
import unittest

from experiments.acquire_heldout import ASSETS, validate_assets


class HeldoutAcquisitionTests(unittest.TestCase):
    def test_fixed_new_metadata_only_windows(self):
        assets = json.loads(ASSETS.read_text())['sites']
        validate_assets(assets)
        self.assertTrue(all(a['tile'] not in ('R4_C19', 'R5_C31', 'R9_C19', 'R12_C14') for a in assets))
        for key, value in (('longitude', 0), ('name', 'replacement')):
            bad = copy.deepcopy(assets); bad[0][key] = value
            with self.assertRaises(ValueError):
                validate_assets(bad)
        bad = copy.deepcopy(assets); bad[0]['window']['col_off'] += 1
        with self.assertRaises(ValueError):
            validate_assets(bad)
        bad = copy.deepcopy(assets); bad[0]['url'] = 'https://example.com/field.zip'
        with self.assertRaises(ValueError):
            validate_assets(bad)


if __name__ == '__main__':
    unittest.main()
