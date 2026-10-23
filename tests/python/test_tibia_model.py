"""Independent fitting/calibration/test groups and honest probability metrics."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import train_tibia_model as model
from twitch_evidence import Evidence,EVIDENCE


class ModelValidationTests(unittest.TestCase):
    def test_partition_and_export_prevent_holdout_refit(self):
        rows=model.observations();data=json.loads(EVIDENCE.read_text())
        self.assertEqual(len(rows),456)
        fit=set(data['training']['fit_ids']);cal=set(data['training']['calibration_ids'])
        test={r['id'] for r in rows if r['split']=='test'}
        self.assertFalse(fit&cal or fit&test or cal&test)
        self.assertEqual(fit,{r['id'] for r in rows if r['split']=='train' and r['label'] is not None})
        seen={}
        for r in rows:
            self.assertEqual(seen.setdefault(r['channel'],r['split']),r['split'])
            signature=(r['title'],tuple(sorted(r['tags'])))
            self.assertEqual(seen.setdefault(signature,r['split']),r['split'])

    def test_held_out_safety_and_calibration_report(self):
        rows=[r for r in model.observations() if r['split']=='test' and r['label'] is not None]
        result=model.metrics(rows,Evidence(json.loads(EVIDENCE.read_text())))
        stored=json.loads((model.DIRECTORY/'evaluation.json').read_text())['held_out']
        self.assertEqual(result,stored)
        self.assertEqual(result['hidden_official'],0)
        self.assertGreater(result['hidden_other'],0)
        self.assertGreater(result['abstained'],0)
        self.assertGreater(result['hidden_official_rate_wilson95'][1],0)
        self.assertGreaterEqual(result['brier'],0)

    def test_logistic_fit_learns_from_supervision(self):
        rows=[([1,1],1),([1,1],1),([1,-1],0),([1,-1],0)]
        fitted=model.optimize(rows,2,0.1)
        reversed_fit=model.optimize([(x,1-y) for x,y in rows],2,0.1)
        self.assertGreater(fitted[1],0)
        self.assertLess(reversed_fit[1],0)

    def test_audit_overlay_records_every_label_change(self):
        audit=json.loads((model.DIRECTORY/'label-audit.json').read_text())['rows']
        for r in audit:
            self.assertEqual(r['disagreement'],r['label']!=r['original_label'])
            self.assertTrue(r['reason'])
        corrected=next(r for r in audit if r['row']==448)
        self.assertEqual(corrected['label'],0)
        self.assertTrue(corrected['disagreement'])
