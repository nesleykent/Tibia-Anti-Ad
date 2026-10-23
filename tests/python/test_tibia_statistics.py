"""Reject incompatible models; identity evidence cannot be diluted or repeated."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from twitch_evidence import Evidence,EVIDENCE


class StatisticalDecisionTests(unittest.TestCase):
    def test_legacy_and_nonfinite_models_fail_closed(self):
        data=json.loads(EVIDENCE.read_text())
        for value in ('joint-text-logistic-v1','piracy-presence-logit-v1'):
            bad=copy.deepcopy(data);bad['model']['format']=value
            with self.assertRaises(ValueError):Evidence(bad)
        for value in (float('nan'),float('inf')):
            bad=copy.deepcopy(data);bad['model']['weights']['other_server_title']=value
            with self.assertRaises(ValueError):Evidence(bad)

    def test_repeated_names_do_not_accumulate_confidence(self):
        ev=Evidence(json.loads(EVIDENCE.read_text()))
        a=ev.classify('RubinOT',[])
        self.assertEqual(a,ev.classify('RubinOT '*20,[]))

    def test_subword_and_partial_tag_matches_are_impossible(self):
        ev=Evidence(json.loads(EVIDENCE.read_text()))
        for title,tags in [('xrubinotz',[]),('', ['rubinotfan']),('xxanticaxx',[])]:
            self.assertEqual(ev.classify(title,tags)[2]['signals'],[])
