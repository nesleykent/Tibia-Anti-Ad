import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / 'extensions/twitch-clean/extension'


class TwitchPackageTests(unittest.TestCase):
    def test_imported_files_match_supplied_archive_hashes(self):
        provenance = json.loads((ROOT / 'research/twitch/source-manifest.json').read_text())
        self.assertEqual(len(provenance['files']) + len(provenance['modified_after_import']), 17)
        for name, digest in provenance['files'].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_manifest_references_existing_resources_and_early_page_world(self):
        manifest = json.loads((EXTENSION / 'manifest.json').read_text())
        self.assertEqual(manifest['manifest_version'], 3)
        self.assertEqual(manifest['host_permissions'], ['*://*.twitch.tv/*'])
        self.assertEqual(manifest['permissions'], ['declarativeNetRequest', 'storage'])
        for resource in manifest['icons'].values():
            self.assertTrue((EXTENSION / resource).is_file())
        self.assertTrue((EXTENSION / manifest['action']['default_popup']).is_file())
        for script in manifest['content_scripts']:
            for resource in script.get('js', []) + script.get('css', []):
                self.assertTrue((EXTENSION / resource).is_file())
        page = next(item for item in manifest['content_scripts'] if 'page.js' in item.get('js', []))
        self.assertEqual(page['world'], 'MAIN')
        self.assertEqual(page['run_at'], 'document_start')
        for entry in manifest['declarative_net_request']['rule_resources']:
            self.assertTrue((EXTENSION / entry['path']).is_file())

    def test_dnr_ids_actions_and_essential_video_hosts(self):
        rules = json.loads((EXTENSION / 'rules.json').read_text())
        self.assertEqual(len(rules), 28)
        self.assertEqual(len({rule['id'] for rule in rules}), len(rules))
        for rule in rules:
            self.assertEqual(rule['action']['type'], 'block')
            pattern = rule['condition']['urlFilter']
            self.assertTrue(pattern.startswith('||') and pattern.endswith('^'))
            self.assertNotIn(pattern, ['||twitch.tv^', '||gql.twitch.tv^', '||ttvnw.net^', '||usher.ttvnw.net^'])

    def test_mit_notice_retained(self):
        for path in [EXTENSION / 'page.js', ROOT / 'scripts/twitch/twitch-stopthemadness.js']:
            source = path.read_text()
            self.assertIn('MIT License', source)
            self.assertIn('Copyright (c) 2020-present TwitchAdSolutions Contributors', source)
