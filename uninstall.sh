#!/usr/bin/env bash
set -euo pipefail
/usr/bin/python3 - <<'PY'
import os
from pathlib import Path
import shutil
import sys
import gi
from gi.repository import Gio

data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
if not data.is_absolute():
    sys.exit('XDG_DATA_HOME must be an absolute path.')
# Restore the original clock before removing our replacement, if requested earlier.
helper = data / 'world-clocks'
if (helper / 'panel.py').is_file():
    sys.path.insert(0, str(helper))
    from panel import change_system_clock, backup_path
    if backup_path().exists():
        print(change_system_clock(False))
# Remove only our registrations, leaving all other panel/desktop items in place.
schema = Gio.SettingsSchemaSource.get_default().lookup('org.cinnamon', True)
if schema:
    settings = Gio.Settings.new('org.cinnamon')
    for key, uuid in [('enabled-desklets', 'world-clocks-desklet@local'),
                      ('enabled-applets', 'world-clocks-panel@local')]:
        old = settings.get_strv(key)
        remaining = [row for row in old if uuid not in row.split(':')]
        if remaining != old and not settings.set_strv(key, remaining):
            sys.exit(f'Cannot disable {uuid}. Remove it through Cinnamon Settings, then retry.')
    Gio.Settings.sync()
for target in (data / 'cinnamon/desklets/world-clocks-desklet@local',
               data / 'cinnamon/applets/world-clocks-panel@local', data / 'world-clocks'):
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
(data / 'applications/world-clocks.desktop').unlink(missing_ok=True)
print('World Clocks uninstalled. Your saved locations are retained in the world-clocks config directory.')
PY
