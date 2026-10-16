"""World Clocks preferences and the system's country/timezone catalog."""
import json
import os
import re
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LANGUAGES = json.loads(Path(__file__).with_name('languages.json').read_text(encoding='utf-8'))
LANGUAGE_NAMES = {item['code']: item['name'] for item in LANGUAGES}
COUNTRY_LANGUAGES = {country: item['code'] for item in LANGUAGES for country in item['countries']}


def config_path():
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'world-clocks/clocks.json'


def defaults():
    return {'version': 1, 'format24': True, 'locations': [
        {'zone': 'Asia/Kathmandu', 'label': 'Kathmandu'},
        {'zone': 'Europe/London', 'label': 'London'},
        {'zone': 'America/New_York', 'label': 'New York'}]}


FORMAT_FIELDS = {'city', 'time', 'date', 'weekday', 'offset', 'zone'}
DEFAULT_PANEL_FORMAT = '{city}  {time}'
DEFAULT_DETAIL_FORMAT = '{weekday}, {date}  ·  {offset}'


def validate_format(template):
    if not isinstance(template, str) or not template.strip() or len(template) > 200 or any(ord(c) < 32 for c in template):
        raise ValueError('Display format must contain 1–200 printable characters.')
    fields = re.findall(r'\{([^{}]*)\}', template)
    remainder = re.sub(r'\{[^{}]*\}', '', template)
    if '{' in remainder or '}' in remainder or any(field not in FORMAT_FIELDS for field in fields):
        raise ValueError('Use only {city}, {time}, {date}, {weekday}, {offset}, and {zone}.')
    return template


def validate(config):
    if not isinstance(config, dict) or config.get('version') != 1:
        raise ValueError('Unsupported settings file version.')
    if type(config.get('format24')) is not bool or not isinstance(config.get('locations'), list):
        raise ValueError('Invalid clock settings.')
    if len(config['locations']) > 100:
        raise ValueError('Choose at most 100 locations.')
    if 'showSeconds' in config and type(config['showSeconds']) is not bool:
        raise ValueError('Show seconds must be enabled or disabled.')
    for key in ('panelFormat', 'detailFormat'):
        if key in config:
            validate_format(config[key])
    seen = set()
    for row in config['locations']:
        if not isinstance(row, dict):
            raise ValueError('Invalid location.')
        zone, label = row.get('zone'), row.get('label')
        if not isinstance(zone, str) or not zone or zone.startswith('/') or '..' in zone.split('/'):
            raise ValueError('Invalid timezone identifier.')
        try:
            ZoneInfo(zone)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError(f'Unknown timezone: {zone}') from exc
        if zone in seen:
            raise ValueError(f'Duplicate timezone: {zone}')
        if not isinstance(label, str) or not label.strip() or len(label) > 100 or any(ord(c) < 32 for c in label):
            raise ValueError('Location names must contain 1–100 printable characters.')
        if 'language' in row and (not isinstance(row['language'], str) or row['language'] not in LANGUAGE_NAMES):
            raise ValueError('Choose a supported clock language.')
        seen.add(zone)
    return config


def load_config(path=None):
    path = Path(path) if path is not None else config_path()
    try:
        return validate(json.loads(path.read_text(encoding='utf-8')))
    except FileNotFoundError:
        return defaults()
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f'Cannot read settings: {path}. The file has been preserved.') from exc


def save_config(config, path=None):
    validate(config)
    path = Path(path) if path is not None else config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(config, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def catalog():
    countries = {}
    root = Path('/usr/share/zoneinfo')
    for line in (root / 'iso3166.tab').read_text().splitlines():
        if line and not line.startswith('#'):
            code, name = line.split('\t', 1)
            countries[code] = name
    rows = [{'country': 'Universal', 'city': 'UTC', 'zone': 'UTC', 'language': 'en-GB'}]
    # zone.tab keeps a separate entry for each country, including linked zones.
    for line in (root / 'zone.tab').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        fields = line.split('\t')
        zone = fields[2]
        city = zone.rsplit('/', 1)[-1].replace('_', ' ')
        rows.append({'country': countries.get(fields[0], fields[0]), 'city': city, 'zone': zone,
                     'language': COUNTRY_LANGUAGES.get(fields[0], 'en-GB')})
    return sorted(rows, key=lambda row: (row['country'], row['city']))
