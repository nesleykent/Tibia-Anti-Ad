import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from twitch_evidence import EVIDENCE, EXTENSION_DATA, AUDIT, Evidence, extension_data
from tibia_text import feature_fields
DATA=json.loads(EVIDENCE.read_text())
EV=Evidence(DATA)


class EvidenceTests(unittest.TestCase):
    def test_explanations_name_actual_identity_and_field(self):
        verdict,_,found=EV.classify('RubinOT hunt bosses',['Português','rubinot'])
        self.assertEqual(verdict,'other')
        self.assertTrue(found['signals'])
        self.assertEqual({s['text'] for s in found['signals']},{'rubinot'})
        self.assertEqual({s['source'] for s in found['signals']},{'title','tags'})
        self.assertAlmostEqual(found['model']['logit'],found['model']['bias']+found['model']['title']+found['model']['tags'],places=5)

    def test_neutral_unseen_and_command_only_inputs_abstain(self):
        for title in ('','hunt bosses','DROPS ON SHINY CATCH EVENT','qxzvkjqzzq','!RubinOT !deusot !pix','R U B I N O T','rub1n0t','Kalante'):
            result=EV.classify(title,['Português','pokemon','Tibia','MMORPG'])
            self.assertEqual(result[0],'undetermined',title)
            self.assertEqual(result[2]['signals'],[],title)

    def test_conflicting_and_comparative_inputs_stay_visible(self):
        for title,tags in [('Tibia Global Antica RubinOT',[]),('RubinOT',['tibiaglobal']),('nao jogo RubinOT',[]),('ex-rubinot',[]),('RubinOT vs PokeAlliance',[])]:
            self.assertEqual(EV.classify(title,tags)[0],'undetermined',title)

    def test_tag_order_duplicates_and_neutral_suffix_are_inert(self):
        a=EV.classify('RubinOT',['rubinot'])
        self.assertEqual(a,EV.classify('RubinOT',['English','rubinot','rubinot','Português']))
        self.assertEqual(EV.classify('Antica',[]),EV.classify('Antica hunt bosses !rubinot',['English']))

    def test_official_world_label_error_is_repaired(self):
        self.assertNotEqual(EV.classify('COBRA BASTION DUO - Tibia - Kalanta',[])[0],'other')
        self.assertTrue(any('kalanta' in s['text'] for s in EV.classify('Kalanta',[])[2]['signals']))

    def test_python_browser_full_result_parity(self):
        rows=[]
        for row in json.loads(AUDIT.read_text())['classificacao']:
            rows.append([row['titulo_original'],[t.strip() for t in row['tags_originais'].split('|') if t.strip()]])
        for capture in ('live-2015','live-2115'):
            rows.extend([r['title'],r.get('tags',[])] for r in json.loads((AUDIT.parent.parent/capture/'streams.json').read_text()))
        rows.extend([r['title'],r.get('tags',[])] for r in json.loads((ROOT/'tests/data/tibia-classify-cases.json').read_text())['cases'])
        rows.extend([s,['Português']] for s in ('❗️rubinot','𝐓𝐢𝐛𝐢𝐚 𝐆𝐥𝐨𝐛𝐚𝐥','é ! RÚBINOT','İstanbul','Antica !rubinot','rubinot!pix'))
        js=json.loads(subprocess.run(['node',str(ROOT/'tests/javascript/twitch-classify.cjs')],input=json.dumps(rows),capture_output=True,text=True,check=True).stdout)
        for (title,tags),result in zip(rows,js,strict=True):
            verdict,reason,found=EV.classify(title,tags)
            self.assertEqual(result,{'verdict':verdict,'reason':reason,'score':found['score'],'found':found},title)

    def test_feature_fields_match_browser(self):
        rows=[['𝐓𝐢𝐛𝐢𝐚 Global Antica !rubinot',['Português','rubinot']],['RubinOT boss',['rubinot','Antica']],['',[]]]
        script="require('./extension/src/tibia-evidence.js');require('./extension/src/tibia-classify.js');console.log(JSON.stringify("+json.dumps(rows)+".map(([t,g])=>TwitchCleanTibiaClassify.featureFields(t,g,TWITCH_CLEAN_TIBIA_EVIDENCE.extractor))));"
        js=json.loads(subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,check=True).stdout)
        self.assertEqual(js,[list(feature_fields(t,g,DATA['extractor'])) for t,g in rows])

    def test_generated_source_is_current(self):
        self.assertEqual(EXTENSION_DATA.read_text(),extension_data(DATA))
