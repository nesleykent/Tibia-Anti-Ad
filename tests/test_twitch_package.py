import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / 'extensions/tibia-anti-ad/extension'


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
        self.assertEqual(manifest['host_permissions'][0], '*://*.twitch.tv/*')
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
        rulesets = {entry['id']: json.loads((EXTENSION / entry['path']).read_text())
                    for entry in json.loads((EXTENSION / 'manifest.json').read_text())['declarative_net_request']['rule_resources']
                    if not entry['id'].startswith('site_')}
        self.assertEqual(set(rulesets), {'twitch_ads', 'twitch_tracking'})
        hosts = []
        for name, rules in rulesets.items():
            with self.subTest(ruleset=name):
                self.assertEqual([rule['id'] for rule in rules], list(range(1, len(rules) + 1)))
                for rule in rules:
                    self.assertEqual(rule['action']['type'], 'block')
                    pattern = rule['condition']['urlFilter']
                    self.assertTrue(pattern.startswith('||') and pattern.endswith('^'))
                    self.assertNotIn(pattern, ['||twitch.tv^', '||gql.twitch.tv^', '||ttvnw.net^', '||usher.ttvnw.net^'])
                    hosts.append(pattern[2:-1])
        # Together the rulesets carry exactly the network rules of the filter list.
        listed = re.findall(r'^\|\|([^\^/$]+)\^', (ROOT / 'filters/twitch/twitch.tv.txt').read_text(), re.M)
        self.assertEqual(len(hosts), 28)
        self.assertEqual(sorted(hosts), sorted(listed))

    def test_settings_page_background_and_bridge(self):
        manifest = json.loads((EXTENSION / 'manifest.json').read_text())
        self.assertTrue((EXTENSION / manifest['options_ui']['page']).is_file())
        self.assertEqual(manifest['options_ui']['page'], manifest['action']['default_popup'])
        self.assertEqual(manifest['background'], {'scripts': ['sites.js', 'settings.js', 'background.js']})
        bridge = next(item for item in manifest['content_scripts'] if 'settings-bridge.js' in item.get('js', []))
        self.assertEqual(bridge['js'], ['sites.js', 'settings.js', 'settings-bridge.js'])
        self.assertEqual(bridge['run_at'], 'document_start')
        self.assertTrue(bridge['all_frames'])
        tibia = next(item for item in manifest['content_scripts'] if 'tibia-filter.js' in item.get('js', []))
        self.assertEqual(tibia['js'][:2], ['sites.js', 'settings.js'])
        overrides = json.loads((ROOT / 'extensions/tibia-anti-ad/chrome/manifest-overrides.json').read_text())
        self.assertEqual(overrides['background'], {'service_worker': 'background.js'})

    def test_every_setting_has_a_switch_and_every_css_rule_a_group(self):
        settings = (EXTENSION / 'settings.js').read_text()
        defaults = re.search(r'const DEFAULTS = Object\.freeze\(\{(.*?)\}\);', settings, re.S).group(1)
        keys = re.findall(r'^\s*(\w+): (?:true|false),$', defaults, re.M)
        popup = (EXTENSION / 'popup.html').read_text()
        switches = re.findall(r'<input type="checkbox" switch role="switch" id="(\w+)" data-setting="\1"', popup)
        self.assertEqual(sorted(switches), sorted(keys))
        self.assertEqual(popup.count('type="checkbox"'), len(keys))
        groups = set(re.findall(r"^\s*\w+: '(\w+)',$", settings.split('const CSS_OPT_OUT')[1].split('const PAGE_KEY')[0], re.M))
        css = (EXTENSION / 'hide.css').read_text()
        rules = [line for line in css.splitlines() if line.endswith('{ display: none !important; }')]
        self.assertEqual(len(rules), 25)
        for rule in rules:
            with self.subTest(rule=rule):
                match = re.match(r'html(?::not\(\[data-tibia-anti-ad-off~="(\w+)"\]\)|\[data-tibia-anti-ad-on~="(\w+)"\]) ', rule)
                self.assertIsNotNone(match)
                self.assertIn(match.group(1) or match.group(2), groups)

    def test_vaft_in_page_script_is_unmodified(self):
        def vaft(path):
            source = path.read_text()
            start = source.index('// ==UserScript==')
            return source[start:source.index('\n})();\n', start) + 5]
        self.assertEqual(vaft(EXTENSION / 'page.js'), vaft(ROOT / 'scripts/twitch/twitch-stopthemadness.js'))

    def test_mit_notice_retained(self):
        for path in [EXTENSION / 'page.js', ROOT / 'scripts/twitch/twitch-stopthemadness.js']:
            source = path.read_text()
            self.assertIn('MIT License', source)
            self.assertIn('Copyright (c) 2020-present TwitchAdSolutions Contributors', source)
