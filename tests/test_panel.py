import importlib.util
from pathlib import Path
import unittest
import os
import subprocess
import tempfile

PATH = Path(__file__).resolve().parents[1] / 'shared/panel.py'

class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert PATH.exists(), 'Panel replacement implementation is missing'
        spec = importlib.util.spec_from_file_location('panel', PATH)
        cls.p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.p)

    def test_replace_and_restore_preserve_other_items(self):
        entries = ['panel1:left:0:menu@cinnamon.org:0',
                   'panel1:right:0:world-clocks-panel@local:16',
                   'panel1:right:12:calendar@cinnamon.org:13',
                   'panel2:right:2:calendar@cinnamon.org:20']
        updated, backup = self.p.replace_plan(entries)
        self.assertIn('panel1:right:12:world-clocks-panel@local:16', updated)
        self.assertNotIn(entries[2], updated)
        self.assertIn(entries[0], updated)
        self.assertIn(entries[3], updated)
        changed = updated + ['panel1:left:5:extra@local:24']
        restored = self.p.restore_plan(changed, backup)
        self.assertEqual(set(restored), set(entries + ['panel1:left:5:extra@local:24']))

    def test_replace_requires_running_widget_and_is_idempotent(self):
        with self.assertRaises(ValueError):
            self.p.replace_plan(['panel1:right:12:calendar@cinnamon.org:13'])
        entries = ['panel1:right:12:world-clocks-panel@local:16']
        updated, backup = self.p.replace_plan(entries)
        self.assertEqual(updated, entries)
        self.assertIsNone(backup)

    def test_replacement_and_restore_with_settings_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from gi.repository import Gio
from panel import change_system_clock, backup_path
settings = Gio.Settings.new('org.cinnamon')
entries = ['panel1:right:0:world-clocks-panel@local:16', 'panel1:right:12:calendar@cinnamon.org:13', 'panel1:left:0:menu@cinnamon.org:0']
settings.set_strv('enabled-applets', entries)
change_system_clock(True)
assert backup_path().is_file()
assert 'panel1:right:12:world-clocks-panel@local:16' in settings.get_strv('enabled-applets')
change_system_clock(False)
assert set(settings.get_strv('enabled-applets')) == set(entries)
assert not backup_path().exists()
'''
            env = dict(os.environ, GSETTINGS_BACKEND='memory', XDG_CONFIG_HOME=tmp)
            subprocess.run(['/usr/bin/python3', '-c', code, str(PATH.parent)], env=env, check=True)

    def test_restore_avoids_duplicate_or_colliding_calendar_ids(self):
        entries = ['panel1:right:0:world-clocks-panel@local:16', 'panel1:right:12:calendar@cinnamon.org:13']
        updated, backup = self.p.replace_plan(entries)
        restored = self.p.restore_plan(updated + ['panel1:left:0:extra@local:13'], backup)
        ids = [row.split(':')[-1] for row in restored]
        self.assertEqual(len(ids), len(set(ids)))
        restored = self.p.restore_plan(updated + ['panel1:right:9:calendar@cinnamon.org:25'], backup)
        self.assertEqual(sum('calendar@cinnamon.org' in row for row in restored), 1)

if __name__ == '__main__':
    unittest.main()
