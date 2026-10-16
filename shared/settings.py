#!/usr/bin/python3
"""Shared GTK preferences for the desklet and panel applet."""
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib
from preferences import (LANGUAGE_NAMES, DEFAULT_PANEL_FORMAT, DEFAULT_DETAIL_FORMAT,
                         catalog, config_path, load_config, save_config)
from panel import change_system_clock


class PreferencesWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title='World Clocks · Locations')
        self.set_default_size(920, 640)
        self.set_border_width(20)
        self.blocked = False
        try:
            config = load_config()
        except (ValueError, OSError) as exc:
            config = {'format24': True, 'locations': []}
            self.blocked = True
            error = f'{exc}\nFix or move {config_path()}, then reopen settings.'
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(outer)
        title = Gtk.Label(label='Your places. Their time.', xalign=0)
        title.get_style_context().add_class('title')
        outer.pack_start(title, False, False, 0)
        outer.pack_start(Gtk.Label(label='The first location appears in the panel. Both widgets share this list.', xalign=0), False, False, 0)
        self.status = Gtk.Label(xalign=0, wrap=True, selectable=True)
        outer.pack_start(self.status, False, False, 0)
        if self.blocked:
            self.status.set_text(error)
        root_box = outer
        notebook = Gtk.Notebook()
        root_box.pack_start(notebook, True, True, 0)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=12)
        notebook.append_page(outer, Gtk.Label(label='Locations'))
        self.build_display_page(notebook, config)
        self.selected = Gtk.ListStore(str, str, str, str)
        for row in config['locations']:
            language = row.get('language', '')
            self.selected.append([row['label'], row['zone'], language,
                                  LANGUAGE_NAMES.get(language, 'System default')])
        selected_view = self.tree(self.selected, [('Location', 0), ('Timezone', 1)])
        label_renderer = selected_view.get_column(0).get_cells()[0]
        label_renderer.set_property('editable', True)
        label_renderer.connect('edited', self.edit_label)
        self.language_model = Gtk.ListStore(str, str)
        self.language_model.append(['System default', ''])
        for code, name in LANGUAGE_NAMES.items():
            self.language_model.append([name, code])
        language_renderer = Gtk.CellRendererCombo()
        language_renderer.set_property('editable', True)
        language_renderer.set_property('has-entry', False)
        language_renderer.set_property('model', self.language_model)
        language_renderer.set_property('text-column', 0)
        language_renderer.connect('changed', self.change_language)
        selected_view.append_column(Gtk.TreeViewColumn('Language', language_renderer, text=3))
        outer.pack_start(self.scroll(selected_view, 160), True, True, 0)
        actions = Gtk.Box(spacing=8)
        for label, callback in [('Move up', lambda _: self.move(selected_view, -1)),
                                ('Move down', lambda _: self.move(selected_view, 1)),
                                ('Remove', lambda _: self.remove(selected_view))]:
            button = Gtk.Button(label=label)
            button.connect('clicked', callback)
            actions.pack_start(button, False, False, 0)
        self.format24 = Gtk.CheckButton(label='Use 24-hour time')
        self.format24.set_active(config['format24'])
        self.display_page.pack_start(self.format24, False, False, 0)
        outer.pack_start(actions, False, False, 0)
        outer.pack_start(Gtk.Label(label='Click a clock’s Language cell to choose its language. Click its name to edit it.', xalign=0), False, False, 0)
        self.search = Gtk.SearchEntry(placeholder_text='Search country, city, or timezone…')
        self.search.set_tooltip_text('Try Nepal, United States, London, or Asia')
        outer.pack_start(self.search, False, False, 0)
        available = Gtk.ListStore(str, str, str, str)
        try:
            for row in catalog():
                available.append([row['country'], row['city'], row['zone'], row['language']])
        except OSError as exc:
            self.status.set_text(f'Cannot load the system timezone catalog: {exc}')
        self.filtered = available.filter_new()
        self.filtered.set_visible_func(self.matches)
        self.search.connect('search-changed', lambda _: self.filtered.refilter())
        available_view = self.tree(self.filtered, [('Country', 0), ('City', 1), ('Timezone', 2)])
        available_view.connect('row-activated', lambda *_: self.add_location(available_view))
        outer.pack_start(self.scroll(available_view, 180), True, True, 0)
        bottom = Gtk.Box(spacing=8)
        add = Gtk.Button(label='Add selected location')
        add.connect('clicked', lambda _: self.add_location(available_view))
        outer.pack_start(add, False, False, 0)
        save = Gtk.Button(label='Save changes')
        save.get_style_context().add_class('suggested-action')
        save.set_sensitive(not self.blocked)
        save.connect('clicked', self.save)
        bottom.pack_end(save, False, False, 0)
        root_box.pack_start(bottom, False, False, 0)

    def build_display_page(self, notebook, config):
        self.display_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=16)
        notebook.append_page(self.display_page, Gtk.Label(label='Display & panel'))
        self.display_page.pack_start(Gtk.Label(label='Panel clock format', xalign=0), False, False, 0)
        presets = {
            '{city}  {time}': 'City and time',
            '{time}': 'Time only',
            '{weekday}  {time}': 'Weekday and time',
            '{weekday}, {date}  ·  {time}': 'Full weekday, date and time',
            '{date}  {time}': 'Date and time',
        }
        self.panel_format = Gtk.Entry(text=config.get('panelFormat', DEFAULT_PANEL_FORMAT))
        self.presets = Gtk.ComboBoxText()
        for template, label in presets.items():
            self.presets.append(template, label)
        self.presets.append('custom', 'Custom')
        self.presets.set_active_id(self.panel_format.get_text() if self.panel_format.get_text() in presets else 'custom')
        def choose_preset(combo):
            template = combo.get_active_id()
            if template and template != 'custom' and self.panel_format.get_text() != template:
                self.panel_format.set_text(template)
        self.presets.connect('changed', choose_preset)
        self.panel_format.connect('changed', lambda entry: self.presets.set_active_id(
            entry.get_text() if entry.get_text() in presets else 'custom'))
        self.display_page.pack_start(self.presets, False, False, 0)
        self.display_page.pack_start(self.panel_format, False, False, 0)
        self.display_page.pack_start(Gtk.Label(label='Desktop detail format', xalign=0), False, False, 0)
        self.detail_format = Gtk.Entry(text=config.get('detailFormat', DEFAULT_DETAIL_FORMAT))
        self.display_page.pack_start(self.detail_format, False, False, 0)
        self.display_page.pack_start(Gtk.Label(
            label='Fields: {city}  {time}  {weekday}  {date}  {offset}  {zone}\nDate and weekday follow each clock’s language.',
            xalign=0, wrap=True), False, False, 0)
        self.show_seconds = Gtk.CheckButton(label='Show seconds')
        self.show_seconds.set_active(config.get('showSeconds', False))
        self.display_page.pack_start(self.show_seconds, False, False, 0)
        self.display_page.pack_start(Gtk.Separator(), False, False, 6)
        self.display_page.pack_start(Gtk.Label(label='Use World Clocks as your system panel clock', xalign=0), False, False, 0)
        note = Gtk.Label(label='Replacement takes effect immediately. Restore brings back the original clock and its calendar menu.', xalign=0, wrap=True)
        self.display_page.pack_start(note, False, False, 0)
        buttons = Gtk.Box(spacing=8)
        for label, replace in [('Replace system clock', True), ('Restore system clock', False)]:
            button = Gtk.Button(label=label)
            button.connect('clicked', lambda _button, flag=replace: self.change_panel(flag))
            buttons.pack_start(button, False, False, 0)
        self.display_page.pack_start(buttons, False, False, 0)

    def change_panel(self, replace):
        try:
            self.status.set_text(change_system_clock(replace))
        except (ValueError, OSError, GLib.Error) as exc:
            self.status.set_text(str(exc))

    @staticmethod
    def tree(model, columns):
        view = Gtk.TreeView(model=model)
        view.set_headers_visible(True)
        for title, index in columns:
            column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=index)
            column.set_expand(True)
            view.append_column(column)
        return view

    @staticmethod
    def scroll(child, height):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(height)
        scroll.add(child)
        return scroll

    def matches(self, model, iterator, _data=None):
        haystack = ' '.join(model[iterator]).casefold()
        return all(word in haystack for word in self.search.get_text().casefold().split())

    def add_location(self, view):
        model, iterator = view.get_selection().get_selected()
        if iterator is None:
            return
        country, city, zone, language = model[iterator]
        if any(row[1] == zone for row in self.selected):
            self.status.set_text(f'{city} is already in your clocks.')
            return
        self.selected.append([city, zone, language, LANGUAGE_NAMES[language]])
        self.status.set_text(f'Added {city}, {country}. Click Save changes to apply.')

    def edit_label(self, _renderer, path, name):
        self.selected[path][0] = name

    def change_language(self, _renderer, path, iterator):
        name, code = self.language_model[iterator]
        self.selected[path][2] = code
        self.selected[path][3] = name

    def remove(self, view):
        model, iterator = view.get_selection().get_selected()
        if iterator is not None:
            model.remove(iterator)

    def move(self, view, delta):
        model, iterator = view.get_selection().get_selected()
        if iterator is None:
            return
        target = model.get_path(iterator).get_indices()[0] + delta
        if 0 <= target < len(model):
            model.swap(iterator, model.get_iter(Gtk.TreePath.new_from_indices([target])))

    def save(self, _button):
        if self.blocked:
            return
        config = {'version': 1, 'format24': self.format24.get_active(),
                  'panelFormat': self.panel_format.get_text(), 'detailFormat': self.detail_format.get_text(),
                  'showSeconds': self.show_seconds.get_active(),
                  'locations': [dict(label=row[0], zone=row[1], **({'language': row[2]} if row[2] else {}))
                                for row in self.selected]}
        try:
            # If a previously valid file was externally corrupted, preserve it.
            load_config()
            save_config(config)
            self.status.set_text('Saved. Your desktop and panel clocks update automatically.')
        except (ValueError, OSError) as exc:
            self.status.set_text(str(exc))


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.worldclocks.Preferences', flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            window = PreferencesWindow(self)
        window.show_all()
        window.present()
        if '--smoke-test' in sys.argv:
            GLib.timeout_add(800, self.quit)


if __name__ == '__main__':
    app = Application()
    app.run([arg for arg in sys.argv if arg != '--smoke-test'])
