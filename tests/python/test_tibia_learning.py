"""The scheduled learner fails closed and never fits its newest test inputs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import tibia_learning as learning
from tibia_spans import SpanModel,candidates,span_features,LANGUAGES,augmentations
from train_tibia_spans import SEED,MODEL,probability


class IdentifierTests(unittest.TestCase):
    def test_active_acceptance(self):
        from train_tibia_spans import evaluate
        self.assertTrue(all(evaluate()['checks'].values()))

    def test_supervision_has_no_raw_metadata_or_alias_inventory(self):
        pack=json.loads(SEED.read_text())
        self.assertEqual(pack['export_count'],399)
        self.assertEqual(len(pack['rows']),pack['historical_count']+399)
        for row in pack['rows']:
            self.assertNotIn('title',row);self.assertNotIn('tags',row);self.assertNotIn('channel',row)
            for candidate in row['candidates']:
                self.assertNotIn('text',candidate)
                self.assertTrue(all(k.isdigit() or k.startswith('s:') for k in candidate['features']))
        data=json.loads(MODEL.read_text())
        self.assertNotIn('references',data)
        self.assertNotIn('aliases',data)

    def test_span_features_ignore_surrounding_gameplay_and_language(self):
        a=next(c for c in candidates('Poke Alliance') if c['text']=='poke alliance')
        b=next(c for c in candidates('hunt bosses Poke Alliance farm quest', ['Português']) if c['text']=='poke alliance')
        self.assertEqual(span_features(a),span_features(b))
        model=SpanModel.load(MODEL)
        for title in ['hunt bosses','farm 24h','Medicina e Tibia','Perdi o loot, !loot !pix !hunt','shoot robot']:
            self.assertEqual(model.predict(title)['private_probability'],.01)
        for title in ['REDOT','feruots.eu','LOL IDLE NOVO LANÇAMENTO','huntera.com.br','Arinar Online','Poke Alliance']:
            self.assertGreater(model.predict(title)['private_probability'],.5)
            expected=model.predict(title)['private_probability']
            for language in LANGUAGES:
                self.assertEqual(model.predict(title,[language])['private_probability'],expected)

    def test_domain_identifiers_also_work_without_transport(self):
        model=SpanModel.load(MODEL)
        for title in ['Feruots','Retronic','playing Feruots & Retronic']:
            self.assertGreater(model.predict(title)['private_probability'],.5)
        for title in ['TSBot','dashcoins','Perdi o loot, !loot !pix !hunt']:
            self.assertEqual(model.predict(title)['private_probability'],.01)
        for source,brand in [('https://examplegame.com.br/path','examplegame'),('examplegame.online','examplegame')]:
            span=next(c for c in candidates(source) if c['kind'] in {'domain','command'})
            expected=span_features(dict(span,kind='name',text=brand))
            self.assertIn(expected,augmentations(span))

    def test_all_labelled_export_rows_remain_acceptance_controls(self):
        pack=json.loads(SEED.read_text());model=json.loads(MODEL.read_text())
        for row in pack['rows'][pack['historical_count']:]:
            p=probability(row,model)
            if row['private']:self.assertGreater(p,.5)
            else:self.assertEqual(p,.01)

    def test_feature_replay_matches_live_inference(self):
        # Raw public acceptance metadata exercises the same context reducer used
        # by retained hashed captures, including sponsor and mixed controls.
        model=SpanModel.load(MODEL)
        for filename in ['tibia-private-context-acceptance.json','tibia-mixed-context-acceptance.json','tibia-span-heldout-acceptance.json']:
            for row in json.loads((ROOT/'tests/data'/filename).read_text())['cases']:
                cs=candidates(row['title'],row['tags'])
                from tibia_spans import context
                packet={'candidates':[{'features':span_features(c),'kind':c['kind'],'field':c['field'],'start':c['start'],'context':context(row['title'],[c])} for c in cs]}
                self.assertAlmostEqual(probability(packet,model.data),model.predict(row['title'],row['tags'])['private_probability'],places=14)

    def test_server_holdout_has_all_mandatory_cases(self):
        report=json.loads((ROOT/'research/twitch/model/span-holdout.json').read_text())
        self.assertEqual(len(report['mandatory']),6)
        self.assertTrue(all(c['flagged'] for c in report['mandatory']))
        self.assertGreater(len(report['folds']),6)
        expected={g for r in json.loads(SEED.read_text())['rows'][json.loads(SEED.read_text())['historical_count']:] if r['private'] for g in r['groups']}
        self.assertEqual({f['server'] for f in report['folds']},expected)


class PipelineTests(unittest.TestCase):
    def test_twitch_pagination_keeps_only_metadata(self):
        responses=[{'access_token':'sentinel-token'}, {'data':[{'id':'509975'}]},
            {'data':[{'id':'1','game_id':'509975','title':'First','tags':['a'],'user_name':'excluded'}],'pagination':{'cursor':'next'}},
            {'data':[{'id':'2','game_id':'509975','title':'Second','tags':[]}],'pagination':{}}]
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)),patch.dict('os.environ',{'TWITCH_CLIENT_ID':'sentinel-client','TWITCH_CLIENT_SECRET':'sentinel-secret'}),patch.object(learning,'request_json',side_effect=responses) as req:
            learning.capture()
            result=json.loads((Path(directory)/'capture.json').read_text())
            self.assertEqual(len(result['streams']),2)
            self.assertEqual(set(result['streams'][0]),{'title','tags'})
            self.assertIn('after=next',req.call_args_list[-1].args[0])
            self.assertNotIn('sentinel',json.dumps(result))

    def test_strict_llm_contract_no_channels_tools_or_images(self):
        row={'title':'REDOT','tags':['English']}
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'labels':[{'id':learning.input_id(row),'private':True,'identifiers':[{'candidate':0,'server':'redot'}]}]})}]}]}
        with patch.dict('os.environ',{'OPENAI_API_KEY':'sentinel'}),patch.object(learning,'request_json',return_value=response) as req:
            result=learning.label_batch([row])
            self.assertTrue(result[0]['private'])
            payload=req.call_args.kwargs['payload']
            self.assertFalse(payload['store']);self.assertTrue(payload['text']['format']['strict'])
            self.assertNotIn('tools',payload)
            inputs=json.loads(payload['input'])
            self.assertEqual(set(inputs[0]),{'id','title','tags','candidates'})
            self.assertNotIn('title',result[0])

    def test_bad_llm_coverage_and_missing_spans_fail(self):
        row={'title':'REDOT','tags':[]}
        for labels in [[],[{'id':learning.input_id(row),'private':True,'identifiers':[]}],[{'id':'wrong','private':False,'identifiers':[]}]]:
            response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'labels':labels})}]}]}
            with patch.dict('os.environ',{'OPENAI_API_KEY':'sentinel'}),patch.object(learning,'request_json',return_value=response),self.assertRaises(learning.StageError):learning.label_batch([row])

    def test_history_augmentation_migration_preserves_labels_and_provenance(self):
        from tibia_spans import context
        raw={'title':'Examplegame.online','tags':[]}
        span=next(c for c in candidates(raw['title'],raw['tags']) if c['kind']=='domain')
        candidate={'features':span_features(span),'positive':True,'augmentations':[]}
        row={'id':learning.input_id(raw),'private':True,'groups':['unchanged'],'candidates':[candidate]}
        history={'rows':[row]}
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)):
            learning.save(Path(directory)/'captures/first.json',{'streams':[raw]})
            learning.refresh_augmentations(history)
        self.assertEqual(history['augmentation_revision'],2)
        self.assertEqual(row['id'],learning.input_id(raw));self.assertTrue(row['private'])
        self.assertEqual(row['groups'],['unchanged'])
        self.assertTrue(candidate['augmentations'])

    def test_newest_failure_does_not_replace_model(self):
        packet={'id':'new-input','private':True,'candidates':[]}
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);learning.save(p/'history.json',{'rows':[packet],'decisions_sha256':'rules'});learning.save(p/'newest.json',{'rows':[packet]})
            before=MODEL.read_bytes()
            with patch.object(learning,'WORK',p),patch.object(learning,'fit',return_value={}) as fitted,patch.object(learning,'probability',return_value=.01),self.assertRaises(learning.StageError):learning.prepare()
            self.assertEqual(before,MODEL.read_bytes())
            self.assertNotIn(packet,fitted.call_args.args[0])
            self.assertEqual(json.loads((p/'gate.json').read_text())['newest_errors'],1)

    def test_api_failure_does_not_expose_body_or_credentials(self):
        import urllib.error
        import io
        error=urllib.error.HTTPError('https://api.openai.com/v1/responses',401,'denied',{},io.BytesIO(b'sentinel-secret'))
        with patch('urllib.request.urlopen',side_effect=error),self.assertRaises(learning.StageError) as caught:
            learning.request_json('https://api.openai.com/v1/responses',{'Authorization':'Bearer sentinel-secret'})
        self.assertEqual(str(caught.exception),'API request failed (HTTP 401)')
        self.assertNotIn('sentinel',str(caught.exception))

    def test_publication_rejects_concurrent_main_before_writing_objects(self):
        import publish_tibia_model as publisher
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);staging=root/'local/publication'
            for name in publisher.FILES:
                path=staging/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
            (staging/'base-sha').write_text('a'*40)
            with patch.object(publisher,'ROOT',root),patch.dict('os.environ',{'MODEL_PUBLISH_TOKEN':'sentinel','GITHUB_REPOSITORY':'owner/repo'}),patch.object(publisher,'request_json',return_value={'object':{'sha':'b'*40}}) as request,self.assertRaises(learning.StageError):
                publisher.publish()
            self.assertEqual(request.call_count,1)

    def test_publication_only_after_learning_success(self):
        text=(ROOT/'.github/workflows/learn-tibia.yml').read_text()
        self.assertIn('needs: learn',text)
        self.assertIn("cron: '17 5,17 * * *'",text)
        self.assertEqual(text.count('secrets.MODEL_PUBLISH_TOKEN'),1)
        self.assertNotIn('continue-on-error',text)
        self.assertIn('force\':False',(ROOT/'tools/publish_tibia_model.py').read_text())

if __name__=='__main__':unittest.main()
