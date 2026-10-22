import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / 'extension/src'
SOURCES = sorted((ROOT / 'filters/sources/sites').glob('*.txt'))


def sites():
    source = (EXTENSION / 'sites.js').read_text()
    return json.loads(source[source.index('Object.freeze(') + 14:source.rindex(');')])


class ExtensionSitesTests(unittest.TestCase):
    def test_generated_output_is_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for part in ['tools', 'filters/sources/sites', 'extension/src']:
                shutil.copytree(ROOT / part, copy / part)
            subprocess.run([sys.executable, str(copy / 'tools/build_extension_sites.py')], check=True, capture_output=True)
            generated = copy / 'extension/src'
            for path in [generated / 'manifest.json', generated / 'sites.js', *sorted((generated / 'sites').glob('*.*'))]:
                with self.subTest(file=path.name):
                    self.assertEqual(path.read_text(), (EXTENSION / path.relative_to(generated)).read_text())

    def test_every_fansite_is_covered_and_on_by_default(self):
        listed = sites()
        self.assertEqual([s['domain'] for s in listed], [p.stem for p in SOURCES])
        self.assertEqual(len(listed), 15)
        protected = {s['domain'] for s in listed if s['protected']}
        self.assertEqual(protected, {'tibiawiki.com.br', 'tibiopedia.pl'})
        settings = (EXTENSION / 'settings.js').read_text()
        self.assertIn('...fromSites(() => true)', settings)

    def test_rulesets_are_valid_dnr_scoped_to_their_site(self):
        manifest = json.loads((EXTENSION / 'manifest.json').read_text())
        resources = {r['id']: r for r in manifest['declarative_net_request']['rule_resources']}
        for site in sites():
            with self.subTest(site=site['domain']):
                self.assertTrue(resources[site['ruleset']]['enabled'])
                rules = json.loads((EXTENSION / resources[site['ruleset']]['path']).read_text())
                self.assertEqual(len(rules), site['rules'])
                self.assertEqual([r['id'] for r in rules], list(range(1, len(rules) + 1)))
                for rule in rules:
                    condition = rule['condition']
                    self.assertTrue(condition['urlFilter'].startswith('||') and condition['urlFilter'].isascii())
                    self.assertTrue(all(d == site['domain'] or d.endswith('.' + site['domain']) for d in condition['domains']))
                    self.assertIn(rule['action']['type'], ['block', 'allow'])
                    self.assertTrue(set(condition.get('resourceTypes', [])) <= {'script', 'image', 'sub_frame'})
                self.assertIn(f"*://{site['domain']}/*", manifest['host_permissions'])
        # The Ad-Shield bait script on tibiopedia must load, or the site wipes itself.
        tibiopedia = json.loads((EXTENSION / 'sites/tibiopedia.pl.json').read_text())
        allow = [r for r in tibiopedia if r['action']['type'] == 'allow']
        self.assertEqual([r['condition']['urlFilter'] for r in allow], ['||tibiopedia.pl/js/show_ads.js'])
        self.assertGreater(allow[0]['priority'], 1)

    def test_cosmetic_rules_are_gated_by_their_switch(self):
        for site in sites():
            with self.subTest(site=site['domain']):
                css = (EXTENSION / f"sites/{site['domain']}.css").read_text()
                rules = [line for line in css.splitlines() if line.endswith('{ display: none !important; }')]
                self.assertEqual(len(rules), site['selectors'])
                gate = f'html:not([data-tibia-anti-ad-off~="{site["domain"]}"]) '
                self.assertTrue(all(rule.startswith(gate) for rule in rules))
        for fix in (EXTENSION / 'sites/fixes').glob('*.css'):
            with self.subTest(fix=fix.name):
                self.assertIn(f'data-tibia-anti-ad-off~="{fix.stem}"', fix.read_text())

    def test_fixes_honour_the_settings(self):
        for name in ['tibiopedia.pl', 'tibiawiki.com.br']:
            source = (EXTENSION / f'sites/fixes/{name}.js').read_text()
            self.assertIn("localStorage.getItem('tibia-anti-ad:settings')", source)
            self.assertIn(f"settings['site:{name}'] === false", source)
            self.assertIn('settings.enabled === false', source)
        manifest = json.loads((EXTENSION / 'manifest.json').read_text())
        bridge = next(s for s in manifest['content_scripts'] if 'settings-bridge.js' in s.get('js', []))
        for site in sites():
            self.assertIn(f"*://{site['domain']}/*", bridge['matches'])
        for script in manifest['content_scripts']:
            if any(f.startswith('sites/fixes/') and f.endswith('.js') for f in script.get('js', [])):
                main = script.get('world') == 'MAIN'
                self.assertEqual(main, 'sites.js' not in script['js'])
                self.assertEqual(script['run_at'], 'document_start')

    def test_popup_lists_the_sites(self):
        popup = (EXTENSION / 'popup.html').read_text()
        self.assertIn('<div class="children" id="sites" role="group" aria-labelledby="h-sites"></div>', popup)
        self.assertLess(popup.index('sites.js'), popup.index('settings.js'))
        self.assertIn('input.dataset.setting = site.key', (EXTENSION / 'popup.js').read_text())


if __name__ == '__main__':
    unittest.main()
