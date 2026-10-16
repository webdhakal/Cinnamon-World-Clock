"""Run in a graphical session with isolated XDG_CONFIG_HOME."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'shared'))
from settings import Application, PreferencesWindow
from preferences import load_config
from gi.repository import Gtk

app = Application()
app.register(None)
window = PreferencesWindow(app)
window.show_all()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
window.search.set_text('Nepal')
window.filtered.refilter()
assert len(window.filtered) == 1, 'Country search failed'
window.search.set_text('New York')
window.filtered.refilter()
assert len(window.filtered) == 1, 'City search failed'
window.selected.clear()
window.selected.append(['New York', 'America/New_York', '', 'System default'])
window.selected.append(['Kathmandu', 'Asia/Kathmandu', '', 'System default'])
view = window.tree(window.selected, [('Location', 0)])
view.get_selection().select_path(Gtk.TreePath.new_from_indices([1]))
window.move(view, -1)
assert window.selected[0][0] == 'Kathmandu'
nepali_iter = next(row.iter for row in window.language_model if row[1] == 'ne-NP')
window.change_language(None, '0', nepali_iter)
window.edit_label(None, '0', 'काठमाडौं')
window.format24.set_active(False)
window.presets.set_active_id('{weekday}, {date}  ·  {time}')
window.detail_format.set_text('{date} · {offset}')
window.show_seconds.set_active(True)
window.save(None)
assert load_config()['locations'][0]['zone'] == 'Asia/Kathmandu'
assert load_config()['format24'] is False
assert load_config()['panelFormat'] == '{weekday}, {date}  ·  {time}'
assert load_config()['detailFormat'] == '{date} · {offset}'
assert load_config()['showSeconds'] is True
assert load_config()['locations'][0]['language'] == 'ne-NP'
assert load_config()['locations'][0]['label'] == 'काठमाडौं'
view.get_selection().select_path(Gtk.TreePath.new_from_indices([1]))
window.remove(view)
assert len(window.selected) == 1
window.destroy()
print('PASS: GTK construction, country/city search, reorder, language and native-name editing, format selection, save, remove')
