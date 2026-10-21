import importlib.util
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
builder = load('build_filters')
classifier = load('classify_streams')

class FilterTests(unittest.TestCase):

    def test_network_scope(self):
        self.assertEqual(builder.scope_rule('||ads.example^$3p', 'site.example'), '||ads.example^$3p,domain=site.example')
        self.assertEqual(builder.scope_rule('@@||site.example/test$script,1p', 'site.example'), '@@||site.example/test$script,1p,domain=site.example')
        with self.assertRaises(ValueError):
            builder.scope_rule('||ads.example^$domain=other.example', 'site.example')
        with self.assertRaises(ValueError):
            builder.scope_rule('other.example##body', 'site.example')

    def test_bundle_scope_and_exclusions(self):
        for extended in (False, True):
            bundle = builder.build(extended)
            domain = None
            count = 0
            for line in bundle.splitlines():
                if line.startswith('! Source: '):
                    domain = line.split(';', 1)[0].removeprefix('! Source: ')
                    self.assertNotIn(domain, builder.EXCLUDED)
                elif line.startswith(('||', '@@||')):
                    self.assertIn(f'domain={domain}', line.split('$', 1)[1].split(','))
                    count += 1
                elif '##' in line and (not line.startswith('!')):
                    self.assertTrue(all((d == domain or d.endswith('.' + domain) for d in line.split('##', 1)[0].split(','))))
            self.assertGreater(count, 100)

    def test_portable_and_extended_differ(self):
        self.assertNotIn(':has(', builder.build())
        self.assertIn(':has(', builder.build(True))
        for operator in ('+js(', ':style(', ':remove(', ':has-text('):
            self.assertNotIn(operator, builder.build())

    def test_committed_artifacts_match_build(self):
        for extended, name in [(False, 'anti-ad-tibia.txt'), (True, 'anti-ad-tibia-extended.txt')]:
            self.assertEqual((ROOT / 'filters' / name).read_text(), builder.build(extended))

    def test_inventory_is_complete(self):
        sources = sorted((ROOT / 'filters/sites').glob('*.txt'))
        self.assertEqual(len(sources), 15)
        inventory = (ROOT / 'docs/WEBSITES.md').read_text()
        for source in sources:
            self.assertIn(source.name.removesuffix('.txt'), inventory)

class ClassificationTests(unittest.TestCase):

    def test_matching_declarations(self):
        self.assertEqual(classifier.classify({'title': ' OTSERV ', 'tags': ['Open Tibia']})['classification'], 'OTServ')
        self.assertEqual(classifier.classify({'title': 'Official Tibia', 'tags': ['Tibia Global']})['classification'], 'Tibia')

    def test_never_hides_any_label(self):
        for title in ['OTServ', 'Official Tibia', 'unknown']:
            self.assertFalse(classifier.classify({'title': title, 'tags': [title]})['hide'])

    def test_bad_input_rejected(self):
        for stream in [None, [], {'title': 123}, {'title': 0}, {'tags': 0}, {'tags': 'OTServ'}, {'tags': [3]}]:
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                classifier.classify(stream)
if __name__ == '__main__':
    unittest.main()
