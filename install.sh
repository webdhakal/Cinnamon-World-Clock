#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export WORLD_CLOCKS_SOURCE="$source_dir"
/usr/bin/python3 - <<'PY'
import os
from pathlib import Path
import shutil
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    ZoneInfo('Asia/Kathmandu')
    if not Path('/usr/share/cinnamon').is_dir():
        raise RuntimeError('Cinnamon desktop is required.')
    for name in ('zone.tab', 'iso3166.tab'):
        if not (Path('/usr/share/zoneinfo') / name).is_file():
            raise RuntimeError('System timezone catalog is missing.')
except (ImportError, ValueError, RuntimeError, ZoneInfoNotFoundError) as exc:
    sys.exit(f'Missing Cinnamon/GTK/timezone support: {exc}\nOn Linux Mint: sudo apt install cinnamon python3-gi gir1.2-gtk-3.0 tzdata')

source = Path(os.environ['WORLD_CLOCKS_SOURCE'])
data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
if not data.is_absolute():
    sys.exit('XDG_DATA_HOME must be an absolute path.')
for kind, uuid, entry in [('desklets', 'world-clocks-desklet@local', 'desklet'),
                          ('applets', 'world-clocks-panel@local', 'applet')]:
    target = data / 'cinnamon' / kind / uuid
    target.mkdir(parents=True, exist_ok=True)
    files = list((source / entry).glob('*')) + list((source / 'shared').glob('*.py')) + [source / 'shared/clocks.js', source / 'shared/languages.json']
    for file in files:
        if file.is_file():
            shutil.copy2(file, target / file.name)
app = data / 'world-clocks'
app.mkdir(parents=True, exist_ok=True)
for name in ('settings.py', 'preferences.py', 'panel.py', 'languages.json'):
    shutil.copy2(source / 'shared' / name, app / name)
shutil.copy2(source / 'uninstall.sh', app / 'uninstall.sh')
applications = data / 'applications'
applications.mkdir(parents=True, exist_ok=True)
# Desktop Entry quoting has its own escaping rules, independent of shell quoting.
def quote(argument):
    escaped = str(argument).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    return '"' + escaped + '"'
exec_arg = quote(app / 'settings.py').replace('\\', '\\\\')
(applications / 'world-clocks.desktop').write_text(
    '[Desktop Entry]\nType=Application\nName=World Clocks Locations\n'
    'Comment=Choose locations for your desktop and panel clocks\n'
    f'Exec=/usr/bin/python3 {exec_arg}\n'
    'Icon=preferences-system-time\nTerminal=false\nCategories=Utility;Clock;\n', encoding='utf-8')
print(f'World Clocks installed in {data}.')
print('Add World Clocks using Cinnamon Settings → Desklets and Settings → Applets.')
print('Commands: cinnamon-settings desklets    and    cinnamon-settings applets')
print('Open Locations + on the desktop widget to choose countries and cities.')
print('After an upgrade, reload active widgets to clear Cinnamon’s cached formatter:')
print('gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon --method org.Cinnamon.ReloadXlet world-clocks-panel@local APPLET')
print('gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon --method org.Cinnamon.ReloadXlet world-clocks-desklet@local DESKLET')
PY
