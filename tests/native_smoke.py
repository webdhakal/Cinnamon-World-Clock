"""Construct and destroy staged widgets in Cinnamon, without adding them to layouts."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from gi.repository import Gio, GLib

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='world-clocks-native-') as tmp:
    data = Path(tmp) / 'data'
    env = dict(os.environ, XDG_DATA_HOME=str(data))
    subprocess.run(['bash', str(root / 'install.sh')], env=env, check=True, capture_output=True)
    desk_path = data / 'cinnamon/desklets/world-clocks-desklet@local'
    applet_path = data / 'cinnamon/applets/world-clocks-panel@local'
    desk_meta = json.loads((desk_path / 'metadata.json').read_text())
    desk_meta['path'] = str(desk_path)
    app_meta = json.loads((applet_path / 'metadata.json').read_text())
    app_meta['path'] = str(applet_path)
    code = '''(() => {
        const FileUtils = imports.misc.fileUtils;
        const Main = imports.ui.main;
        const St = imports.gi.St;
        const dm = DESK_META;
        const am = APP_META;
        let desk = null, applet = null;
        try {
            const d = FileUtils.requireModule('desklet.js', dm.path, dm, 'desklet');
            desk = d.main(dm, 987654);
            if (desk._box.get_n_children() < 2) throw new Error('Desklet content missing');
            const a = FileUtils.requireModule('applet.js', am.path, am, 'applet');
            const definitions = Main.AppletManager.getDefinitions();
            if (!definitions.length) throw new Error('No existing panel instance for test');
            applet = a.main(am, St.Side.BOTTOM, 40, definitions[0].applet_id);
            const clocks = FileUtils.requireModule('clocks.js', am.path, am, 'applet');
            const instant = imports.gi.GLib.DateTime.new_from_iso8601('2026-01-01T00:00:00Z', null);
            const row = clocks.clockAt({zone:'Asia/Kathmandu',label:'काठमाडौं',language:'ne-NP'}, true, instant);
            applet._render([row], null);
            if (applet._applet_label.get_text() !== 'काठमाडौं  ०५:४५') throw new Error('Nepali panel text incorrect');
            desk._render([row], null);
            const desktopTime = desk._box.get_children()[1].get_children()[0].get_children()[1].get_text();
            if (desktopTime !== '०५:४५') throw new Error('Nepali desktop text incorrect');
            applet._render([row], null, {panelFormat:'{weekday}, {date} · {time}'});
            if (applet._applet_label.get_text() !== `${row.weekday}, ${row.fullDate} · ${row.time}`) throw new Error('Full panel date format incorrect');
            if (applet.menu.numMenuItems < 2) throw new Error('Panel menu missing');
            return 'PASS: native Cinnamon desklet and applet construction, Nepali rendering, and cleanup';
        } catch (error) {
            return 'FAIL: ' + error.message + '\\n' + error.stack;
        } finally {
            if (desk) {
                desk.on_desklet_removed();
                desk._menu.destroy();
                desk.actor.destroy();
            }
            if (applet) {
                applet.on_applet_removed_from_panel();
                global.settings.disconnect(applet._panelEditModeChangedId);
                applet._applet_context_menu.destroy();
                applet._applet_tooltip.destroy();
                applet.actor.destroy();
            }
        }
    })()'''.replace('DESK_META', json.dumps(desk_meta)).replace('APP_META', json.dumps(app_meta))
    result = Gio.bus_get_sync(Gio.BusType.SESSION, None).call_sync('org.Cinnamon', '/org/Cinnamon', 'org.Cinnamon', 'Eval',
        GLib.Variant('(s)', (code,)), GLib.VariantType('(bs)'), Gio.DBusCallFlags.NONE, 10000, None)
    success, response = result.unpack()
    print(response)
    if not success or 'PASS:' not in response:
        raise SystemExit(1)
