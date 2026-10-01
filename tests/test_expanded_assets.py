import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExpandedAssets(unittest.TestCase):
    def test_frozen_geography(self):
        data = json.loads((ROOT/'integration/expanded_assets_20261002.json').read_text())
        sites = data['sites']
        self.assertEqual(len(sites),40)
        self.assertEqual(len({s['site'] for s in sites}),40)
        self.assertTrue(data['no_pixel_data_inspected'])
        self.assertEqual(data['sizes'],[256,512,1024])
        self.assertEqual(len(data['budgets']),8)
        self.assertFalse({s['site'] for s in sites} &
                         {'paris','tokyo','lagos','sao_paulo','cairo','delhi','new_york','jakarta'})
        for s in sites:
            self.assertGreater(s['geonameid'],0)
            self.assertTrue(s['url'].startswith('https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/'))
            w=s['window']
            self.assertEqual((w['height'],w['width']),(1024,1024))
            self.assertTrue(0<=w['row_off']<=8976 and 0<=w['col_off']<=8976)

    def test_no_new_location_overlap(self):
        sites=json.loads((ROOT/'integration/expanded_assets_20261002.json').read_text())['sites']
        for i,a in enumerate(sites):
            for b in sites[i+1:]:
                if a['tile']!=b['tile']:
                    continue
                wa,wb=a['window'],b['window']
                overlap=(abs(wa['row_off']-wb['row_off'])<1024 and
                         abs(wa['col_off']-wb['col_off'])<1024)
                self.assertFalse(overlap,(a['site'],b['site']))
