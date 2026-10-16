import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'shared/preferences.py'

class PreferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert MODULE.exists(), 'Shared preferences implementation is missing'
        spec = importlib.util.spec_from_file_location('preferences', MODULE)
        cls.p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.p)

    def test_catalog_has_countries_and_multiple_us_zones(self):
        catalog = self.p.catalog()
        self.assertTrue(any('Nepal' in row['country'] and row['zone'] == 'Asia/Kathmandu' for row in catalog))
        self.assertGreater(len([r for r in catalog if r['country'] == 'United States']), 1)

    def test_save_round_trip_preserves_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'clocks.json'
            config = {'version': 1, 'format24': False, 'locations': [
                {'zone': 'Asia/Kathmandu', 'label': 'Kathmandu'},
                {'zone': 'America/New_York', 'label': 'New York'}]}
            self.p.save_config(config, path)
            self.assertEqual(self.p.load_config(path), config)

    def test_invalid_zone_and_duplicates_are_rejected(self):
        for locations in [[{'zone': '../etc/passwd', 'label': 'Bad'}],
                          [{'zone': 'Fake/City', 'label': 'Bad'}],
                          [{'zone': 'UTC', 'label': 'A'}, {'zone': 'UTC', 'label': 'B'}]]:
            with self.assertRaises(ValueError):
                self.p.validate({'version': 1, 'format24': True, 'locations': locations})

    def test_corrupt_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'clocks.json'
            path.write_text('{broken')
            with self.assertRaises(ValueError):
                self.p.load_config(path)
            self.assertEqual(path.read_text(), '{broken')

    def test_per_location_languages_round_trip_and_legacy_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'clocks.json'
            config = {'version': 1, 'format24': True, 'locations': [
                {'zone': 'Asia/Kathmandu', 'label': 'काठमाडौं', 'language': 'ne-NP'},
                {'zone': 'Europe/Paris', 'label': 'Paris', 'language': 'fr-FR'}]}
            self.p.save_config(config, path)
            self.assertEqual(self.p.load_config(path), config)
        legacy = {'version': 1, 'format24': True, 'locations': [{'zone': 'UTC', 'label': 'UTC'}]}
        self.assertEqual(self.p.validate(legacy), legacy)
        for language in ['zz-ZZ', 123, '', None]:
            with self.assertRaises(ValueError):
                self.p.validate({'version': 1, 'format24': True, 'locations': [
                    {'zone': 'UTC', 'label': 'UTC', 'language': language}]})

    def test_display_format_settings(self):
        config = {'version':1, 'format24':True, 'locations':[], 'showSeconds':True,
                  'panelFormat':'{weekday}, {date} · {time}', 'detailFormat':'{date} · {offset}'}
        self.assertEqual(self.p.validate(config), config)
        for key, value in [('showSeconds', 'yes'), ('panelFormat', '{unknown}'),
                           ('panelFormat', '{time'), ('detailFormat', ''), ('detailFormat', '{time}\n')]:
            with self.assertRaises(ValueError):
                self.p.validate(dict(config, **{key:value}))

    def test_nepal_catalog_suggests_nepali(self):
        nepal = next(row for row in self.p.catalog() if row['zone'] == 'Asia/Kathmandu')
        self.assertEqual(nepal['language'], 'ne-NP')

    def test_missing_config_has_defaults_and_empty_selection_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertGreater(len(self.p.load_config(Path(tmp) / 'none')['locations']), 0)
        self.p.validate({'version': 1, 'format24': True, 'locations': []})

if __name__ == '__main__':
    unittest.main()
