"""Replace/restore just the original clock, preserving other panel items."""
import json
from pathlib import Path

WORLD = 'world-clocks-panel@local'
CALENDAR = 'calendar@cinnamon.org'


def parts(row):
    values = row.split(':')
    return values if len(values) == 5 else None


def replace_plan(entries):
    world = next((row for row in entries if parts(row) and parts(row)[3] == WORLD), None)
    if not world:
        raise ValueError('Add World Clocks to your panel first, then replace the system clock.')
    wp = parts(world)
    original = next((row for row in entries if parts(row) and parts(row)[3] == CALENDAR
                     and parts(row)[0] == wp[0]), None)
    if not original:
        return list(entries), None
    replacement = ':'.join(parts(original)[:3] + [WORLD, wp[4]])
    return [replacement if row == original else row for row in entries if row != world], {
        'calendar': original, 'world': world}


def restore_plan(entries, backup):
    original, previous_world = backup['calendar'], backup['world']
    if not parts(original) or parts(original)[3] != CALENDAR or not parts(previous_world) or parts(previous_world)[3] != WORLD:
        raise ValueError('Invalid saved clock position.')
    panel_id = parts(original)[0]
    world = next((row for row in entries if parts(row) and parts(row)[3] == WORLD and parts(row)[0] == panel_id), None)
    restored = list(entries)
    if world:
        old_position = ':'.join(parts(previous_world)[:4] + [parts(world)[4]])
        restored = [old_position if row == world else row for row in restored]
    if not any(parts(row) and parts(row)[0] == panel_id and parts(row)[3] == CALENDAR for row in restored):
        used = {parts(row)[4] for row in restored if parts(row)}
        if parts(original)[4] in used:
            next_id = max((int(value) for value in used if value.isdigit()), default=0) + 1
            original = ':'.join(parts(original)[:4] + [str(next_id)])
        restored.append(original)
    return restored


def backup_path():
    from preferences import config_path
    return config_path().with_name('system-clock-backup.json')


def change_system_clock(replace=True):
    from gi.repository import Gio
    settings = Gio.Settings.new('org.cinnamon')
    entries = settings.get_strv('enabled-applets')
    path = backup_path()
    if replace:
        updated, backup = replace_plan(entries)
        if backup is None:
            return 'World Clocks is already the only clock on its panel.'
        # Do not overwrite the original restore point on repeated replacements.
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open('x', encoding='utf-8') as stream:
                json.dump(backup, stream)
    else:
        if not path.exists():
            return 'No saved system-clock position to restore.'
        updated = restore_plan(entries, json.loads(path.read_text(encoding='utf-8')))
    # Preserve unique instance IDs even if another applet reused a removed ID.
    next_id = max((int(parts(row)[4]) for row in updated if parts(row) and parts(row)[4].isdigit()), default=0) + 1
    if settings.get_int('next-applet-id') < next_id:
        settings.set_int('next-applet-id', next_id)
    if not settings.set_strv('enabled-applets', updated):
        raise ValueError('Cinnamon could not update the panel. Your restore point is retained.')
    Gio.Settings.sync()
    if not replace:
        path.unlink()
    return 'System clock replaced with World Clocks.' if replace else 'Original system clock restored.'
