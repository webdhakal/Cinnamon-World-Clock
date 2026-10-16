from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class InstallTests(unittest.TestCase):
    def test_install_upgrade_uninstall_keeps_unrelated_files_and_preferences(self):
        self.assertTrue((ROOT / 'install.sh').exists(), 'Installer is missing')
        with tempfile.TemporaryDirectory(prefix='world clocks ') as tmp:
            data = Path(tmp) / 'data'
            config = Path(tmp) / 'config'
            config.mkdir()
            (config / 'world-clocks').mkdir()
            preferences = config / 'world-clocks/clocks.json'
            preferences.write_text('{"version":1,"format24":true,"locations":[]}')
            data.mkdir()
            (data / 'keep.txt').write_text('unrelated')
            env = dict(os.environ, XDG_DATA_HOME=str(data), XDG_CONFIG_HOME=str(config), GSETTINGS_BACKEND='memory')
            for _ in range(2):
                subprocess.run(['bash', str(ROOT / 'install.sh')], env=env, check=True, capture_output=True)
            for kind, uuid, entry in [('desklets', 'world-clocks-desklet@local', 'desklet.js'),
                                      ('applets', 'world-clocks-panel@local', 'applet.js')]:
                folder = data / 'cinnamon' / kind / uuid
                for name in [entry, 'clocks.js', 'preferences.py', 'settings.py', 'metadata.json', 'languages.json']:
                    self.assertTrue((folder / name).is_file(), name)
            desktop = (data / 'applications/world-clocks.desktop').read_text()
            self.assertIn('Exec=/usr/bin/python3 "', desktop)
            if __import__('shutil').which('desktop-file-validate'):
                subprocess.run(['desktop-file-validate', str(data / 'applications/world-clocks.desktop')], check=True)
            subprocess.run(['bash', str(ROOT / 'uninstall.sh')], env=env, check=True, capture_output=True)
            self.assertFalse((data / 'cinnamon/desklets/world-clocks-desklet@local').exists())
            self.assertFalse((data / 'cinnamon/applets/world-clocks-panel@local').exists())
            self.assertFalse((data / 'applications/world-clocks.desktop').exists())
            self.assertEqual(preferences.read_text(), '{"version":1,"format24":true,"locations":[]}')
            self.assertEqual((data / 'keep.txt').read_text(), 'unrelated')

if __name__ == '__main__':
    unittest.main()
