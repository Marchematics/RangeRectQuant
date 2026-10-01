import unittest
from unittest.mock import patch

from experiments.run_heldout import configurations, summarize


class HeldoutTests(unittest.TestCase):
    def test_unchanged_strong_grid_and_primary(self):
        rows = configurations()
        self.assertEqual(len(rows), 45)
        self.assertEqual(sum(r['family'] == 'baseline' for r in rows), 38)
        self.assertEqual([r['step'] for r in rows if r['family'] == 'greedy'], [20, 200])
        self.assertEqual([r['mode'] for r in rows if r['family'] == 'fiber'], [0, 25, 250])

    def test_complete_legal_nontrivial_paired_gate(self):
        rows = []
        for site in ('cairo', 'delhi', 'new_york', 'jakarta'):
            for i, cfg in enumerate(configurations()):
                main = cfg['family'] == 'greedy'
                rows.append(dict(id=f'{site}-{i}', site=site, configuration=cfg,
                                 status='DECODED_AND_AUDITED', packet_bytes=80 if main else 100,
                                 contracts={str(e): dict(status='LEGAL', changed_values=1 if main else 0)
                                            for e in (100, 1000)}))
        manifest = dict(rows=[dict(site=s) for s in ('cairo', 'delhi', 'new_york', 'jakarta')])
        with patch('experiments.run_heldout.read', return_value=manifest):
            self.assertTrue(all(g['passed'] for g in summarize(rows, 0)['gates']))
            self.assertFalse(any(g['passed'] for g in summarize(rows[:-1], 0)['gates']))
            for row in rows:
                if row['configuration']['family'] == 'greedy':
                    row['contracts']['100']['changed_values'] = 0
            self.assertFalse(summarize(rows, 0)['gates'][0]['passed'])
            self.assertTrue(summarize(rows, 0)['gates'][1]['passed'])


if __name__ == '__main__':
    unittest.main()
