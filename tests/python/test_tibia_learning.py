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
    def test_pokemon_project_and_tags(self):
        model=SpanModel.load(MODEL)
        for title,tags in [('Padventures - Event Halloween',['PAD','PadventuresDiamond','Español']),
                           ('Padventures',[]),('PAdventures Diamond',[]),('PadventuresDiamond',[])]:
            self.assertGreater(model.predict(title,tags)['private_probability'],.5)
        for title in ['Gamepad','Sketchpad','Diamond painting','Event Halloween']:
            self.assertEqual(model.predict(title)['private_probability'],.01)

    def test_project_game_descriptor_and_protocol(self):
        model=SpanModel.load(MODEL)
        for title in ['Olympic Tibia 7.4', 'Olympic 7.4', 'olympic tibia 7.4',
                      'OLYMPIC TIBIA 7.4']:
            with self.subTest(title=title):
                self.assertGreater(model.predict(title,['Gaming4Fun','VenezuelaStreamer'])['private_probability'],.5)
        for title in ['Tibia 7.4', 'Hunt Tibia 7.4', 'Global Tibia 7.4',
                      'Tibia 8.60', 'OBS 8.60', 'Hunt 7.4', 'Level 8.60',
                      'Hunt 8.60', 'Hunt Tibia 8.60', 'Global Tibia 8.60']:
            with self.subTest(title=title):
                self.assertEqual(model.predict(title)['private_probability'],.01)
        for source in ['Examplegame74.com','Examplegame74.com.br','Examplegame74']:
            span=next(c for c in candidates(source) if c['kind']!='protocol')
            for variant in ['examplegame 7.4','examplegame tibia 7.4']:
                expected=span_features(dict(span,text=variant,kind='name',protocol_context=True))
                self.assertIn(expected,augmentations(span))
                self.assertIn(expected,augmentations(span,positive=False))

    def test_protocol_project_regressions_and_hosting_control(self):
        model=SpanModel.load(MODEL)
        for title in ['Trimera 7.4 | True Vanilla | LAUNCH SOON',
                      'DARKORIA 8.60 | OPEN BETA OCT 24', 'Olympic74.com']:
            with self.subTest(title=title):
                self.assertGreater(model.predict(title)['private_probability'],.5)
        for title in ['!Ts /!moedaz !pix !exitlag #tsxhost.com',
                      'Tibia 15.00 update launch soon', 'OBS 8.60 open beta']:
            with self.subTest(title=title):
                self.assertEqual(model.predict(title)['private_probability'],.01)
        for title in ['Examplegame74.com','Examplegame74.com.br']:
            domain=next(c for c in candidates(title) if c['kind']=='domain')
            self.assertIn('s:protocol_suffix:domain',span_features(domain))

    def test_private_inputs_cannot_calibrate_negative_identifier_cutoffs(self):
        from tibia_spans import FEATURES,context
        from train_tibia_spans import fit
        span=candidates('Fixture')[0]
        candidate={'features':span_features(span),'positive':False,'kind':span['kind'],
                   'field':'title','start':0,'context':context('Fixture',[span])}
        row={'private':True,'target':.99,'supervision':'private','candidates':[candidate]}
        with patch('train_tibia_spans.fit_identifier',return_value={}),patch('train_tibia_spans.fit_weights',return_value=dict.fromkeys(FEATURES,0.0)):
            self.assertEqual(fit([row])['identifier_cutoffs'],{})

    def test_calibration_preserves_signed_boundary_for_supervised_shapes(self):
        from tibia_spans import FEATURES,context,accepted
        from train_tibia_spans import fit
        def row(title,positive):
            span=candidates(title)[0]
            features=span_features(span)
            if positive:features['s:test_positive']=1.0
            candidate=dict(features=features,positive=positive,kind=span['kind'],
                           field='title',start=0,context=context(title,[span]))
            return dict(private=positive,target=.99 if positive else .01,
                        supervision='private' if positive else 'no_private_server_evidence',candidates=[candidate])
        yes,no,protocol=row('examplegame.com',True),row('exampletool.com',False),row('7.4',False)
        with patch('train_tibia_spans.fit_identifier',return_value={'s:bias':-1.,'s:kind:domain':.5,'s:test_positive':2.}),patch('train_tibia_spans.fit_weights',return_value=dict.fromkeys(FEATURES,0.)):
            model=fit([yes,no,protocol])
        self.assertAlmostEqual(model['identifier_cutoffs']['domain'],-.5+1e-8)
        self.assertEqual(model['identifier_cutoffs']['protocol'],0.)
        self.assertFalse(accepted(no['candidates'][0]['features'],'domain',model))
        self.assertTrue(accepted(yes['candidates'][0]['features'],'domain',model))

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
            for suffix in ('.com','.com.br'):
                expected=span_features(dict(span,kind='domain',text=brand+suffix))
                if span['text'].split('/')[0]!=brand+suffix:
                    self.assertIn(expected,augmentations(span))
                    self.assertIn(expected,augmentations(span,positive=False))

    def test_all_labelled_export_rows_remain_acceptance_controls(self):
        pack=json.loads(SEED.read_text());model=json.loads(MODEL.read_text())
        for row in pack['rows'][pack['historical_count']:]:
            p=probability(row,model)
            if row['private']:self.assertGreater(p,.5)
            else:self.assertEqual(p,.01)

    def test_supplemental_capture_and_protocol_controls(self):
        pack=json.loads(SEED.read_text());model=json.loads(MODEL.read_text())
        end=pack['historical_count'];start=end-pack['supplemental_count']
        for row in pack['rows'][start:end]:
            with self.subTest(input_id=row['id']):
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
    def test_structural_feature_migration_keeps_original_annotations(self):
        raw={'title':'Examplegame 8.60 OPEN BETA','tags':[]}
        span=next(c for c in candidates(raw['title']) if c['text']=='examplegame')
        features=span_features(span)
        legacy={k:v for k,v in features.items() if not k.startswith(('s:protocol_adjacent:', 's:launch:protocol_adjacent:', 's:launch:protocol_length:', 's:protocol_suffix', 's:brand_tail:poke', 's:compound_stem_length:'))}
        candidate={'features':legacy,'positive':True,'augmentations':[]}
        row={'id':learning.input_id(raw),'private':True,'groups':['original'],'label_provenance':{'source':'original'},'candidates':[candidate]}
        history={'rows':[row],'augmentation_revision':2}
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)):
            learning.save(Path(directory)/'captures/source.json',{'streams':[raw]})
            learning.refresh_augmentations(history)
        self.assertEqual(candidate['features'],features)
        self.assertEqual(row['groups'],['original'])
        self.assertEqual(row['label_provenance'],{'source':'original'})
        self.assertTrue(candidate['positive']);self.assertTrue(row['private'])

    def test_repeated_identifier_migration_preserves_span_positions(self):
        raw={'title':'Examplegame 8.60 OPEN BETA / Examplegame','tags':[]}
        spans=[c for c in candidates(raw['title']) if c['text']=='examplegame']
        self.assertEqual(len(spans),2)
        cs=[]
        for span in spans:
            fs={k:v for k,v in span_features(span).items() if not k.startswith(('s:protocol_adjacent:', 's:launch:protocol_adjacent:', 's:launch:protocol_length:', 's:protocol_suffix', 's:brand_tail:poke', 's:compound_stem_length:'))}
            cs.append(dict(features=fs,positive=True,augmentations=[],**{k:span[k] for k in ('kind','field','start')}))
        history={'rows':[{'id':learning.input_id(raw),'candidates':cs}],'augmentation_revision':2}
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)):
            learning.save(Path(directory)/'captures/source.json',{'streams':[raw]})
            learning.refresh_augmentations(history)
        self.assertEqual([c['features'] for c in cs],[span_features(span) for span in spans])

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
        response={'done':True,'done_reason':'stop','response':json.dumps({'labels':[{'id':learning.input_id(row),'private':True,'identifiers':[{'candidate':0,'server':'redot'}]}]})}
        with patch.dict('os.environ',{},clear=True),patch.object(learning,'request_json',return_value=response) as req:
            result=learning.label_batch([row])
            self.assertTrue(result[0]['private'])
            payload=req.call_args.kwargs['payload']
            self.assertFalse(payload['stream']);self.assertFalse(payload['format']['additionalProperties'])
            self.assertEqual(req.call_args.args[0],'http://127.0.0.1:11434/api/generate')
            self.assertNotIn('headers',req.call_args.kwargs)
            self.assertNotIn('tools',payload)
            inputs=json.loads(payload['prompt'])
            self.assertEqual(set(inputs[0]),{'id','title','tags','candidates'})
            self.assertNotIn('title',result[0])

    def test_bad_llm_coverage_and_missing_spans_fail(self):
        row={'title':'REDOT','tags':[]}
        for labels in [[],[{'id':learning.input_id(row),'private':True,'identifiers':[]}],[{'id':'wrong','private':False,'identifiers':[]}]]:
            response={'done':True,'done_reason':'stop','response':json.dumps({'labels':labels})}
            with patch.object(learning,'request_json',return_value=response),self.assertRaises(learning.StageError):learning.label_batch([row])

    def test_local_model_digest_and_incomplete_generation_fail_closed(self):
        with patch.object(learning,'request_json',return_value={'models':[{'name':learning.MODEL_NAME,'digest':'changed'}]}),self.assertRaises(learning.StageError):
            learning.verify_labeller()
        with patch.object(learning,'request_json',return_value={'done':True,'done_reason':'length','response':'{}'}),self.assertRaises(learning.StageError):
            learning.label_batch([{'title':'REDOT','tags':[]}])

    def test_runtime_checksum_failure_never_executes_download(self):
        import io
        import start_tibia_labeller as runtime
        with tempfile.TemporaryDirectory() as directory,patch.object(runtime,'WORK',Path(directory)),patch.object(runtime.urllib.request,'urlopen',return_value=io.BytesIO(b'wrong archive')),patch.object(runtime.subprocess,'run') as run,self.assertRaises(learning.StageError):
            runtime.start()
        run.assert_not_called()

    def test_completed_label_batches_survive_a_later_failure(self):
        rows=[{'title':f'Fixture {i}','tags':[]} for i in range(5)]
        completed=[{'id':learning.input_id(r),'private':False} for r in rows[:4]]
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)),patch.object(learning,'verify_labeller'),patch.object(learning,'label_batch',side_effect=[completed,learning.StageError('incomplete')]):
            path=Path(directory)
            learning.save(path/'capture.json',{'streams':rows})
            with self.assertRaises(learning.StageError):learning.label()
            self.assertEqual(json.loads((path/'history.json').read_text())['rows'],completed)
            self.assertFalse((path/'newest.json').exists())

    def test_local_provider_policy_migration_preserves_labels(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)),patch.object(learning,'verify_labeller') as verify:
            path=Path(directory)
            learning.save(path/'capture.json',{'streams':[]})
            learning.save(path/'history.json',{'rows':[],'decisions_sha256':learning.LEGACY_DECISIONS_SHA256})
            learning.label()
            history=json.loads((path/'history.json').read_text())
            self.assertEqual(history['rows'],[])
            self.assertEqual(history['decision_migrations'][0]['from'],learning.LEGACY_DECISIONS_SHA256)
            self.assertEqual(history['decisions_sha256'],hashlib.sha256((ROOT/'DECISIONS.md').read_bytes()).hexdigest())
            verify.assert_not_called()
            history['decisions_sha256']=learning.LEGACY_DECISIONS_SHA256
            learning.save(path/'history.json',history)
            with patch.object(learning,'CLASSIFICATION_SHA256','changed'),self.assertRaises(learning.StageError):
                learning.label()

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
        self.assertEqual(history['augmentation_revision'],4)
        self.assertEqual(row['id'],learning.input_id(raw));self.assertTrue(row['private'])
        self.assertEqual(row['groups'],['unchanged'])
        self.assertTrue(candidate['augmentations'])

    def test_protocol_proposal_migration_retains_prior_project_span(self):
        from tibia_spans import LEGACY_PROJECT
        raw={'title':'Examplegame Tibia 7.4','tags':[]}
        span=next(c for c in candidates(raw['title'],project_pattern=LEGACY_PROJECT) if c['text']=='examplegame tibia')
        candidate={'features':span_features(span),'positive':True,'augmentations':[],
                   **{k:span[k] for k in ('kind','field','start')}}
        original=dict(candidate['features'])
        row={'id':learning.input_id(raw),'private':True,'groups':['retained'],'candidates':[candidate]}
        history={'rows':[row],'augmentation_revision':3}
        with tempfile.TemporaryDirectory() as directory,patch.object(learning,'WORK',Path(directory)):
            learning.save(Path(directory)/'captures/first.json',{'streams':[raw]})
            learning.refresh_augmentations(history)
        self.assertEqual(candidate['features'],original)
        self.assertTrue(candidate['positive'])
        self.assertEqual(row['groups'],['retained'])
        self.assertEqual(history['augmentation_revision'],4)

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
        error=urllib.error.HTTPError('https://example.invalid/api',401,'denied',{},io.BytesIO(b'sentinel-secret'))
        with patch('urllib.request.urlopen',side_effect=error),self.assertRaises(learning.StageError) as caught:
            learning.request_json('https://example.invalid/api',{'Authorization':'Bearer sentinel-secret'})
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
        self.assertNotIn('OPENAI_API_KEY',text)
        self.assertIn('tools/start_tibia_labeller.py',text)
        self.assertIn('force\':False',(ROOT/'tools/publish_tibia_model.py').read_text())

if __name__=='__main__':unittest.main()
