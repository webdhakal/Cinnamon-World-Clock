/* Shared by both Cinnamon widgets. Time calculations use the system tzdata. */
const GLib = imports.gi.GLib;
const Gio = imports.gi.Gio;
const ByteArray = imports.byteArray;

function defaults() {
    return {version: 1, format24: true, locations: [
        {zone: 'Asia/Kathmandu', label: 'Kathmandu'},
        {zone: 'Europe/London', label: 'London'},
        {zone: 'America/New_York', label: 'New York'}]};
}

function timezone(identifier) {
    if (typeof identifier !== 'string' || !identifier || identifier.startsWith('/') ||
        identifier.split('/').includes('..') ||
        !GLib.file_test(`/usr/share/zoneinfo/${identifier}`, GLib.FileTest.IS_REGULAR))
        throw new Error(`Unknown timezone: ${identifier}`);
    let zone = GLib.TimeZone.new_identifier(identifier);
    if (!zone) throw new Error(`Unknown timezone: ${identifier}`);
    return zone;
}

function validate(config) {
    if (!config || config.version !== 1 || typeof config.format24 !== 'boolean' ||
        !Array.isArray(config.locations) || config.locations.length > 100)
        throw new Error('Invalid clock settings. Open Locations to inspect your configuration.');
    if ('showSeconds' in config && typeof config.showSeconds !== 'boolean')
        throw new Error('Invalid seconds setting.');
    for (let key of ['panelFormat', 'detailFormat'])
        if (key in config) validateFormat(config[key]);
    let seen = new Set();
    for (let location of config.locations) {
        if (!location || typeof location.label !== 'string' || !location.label.trim() ||
            location.label.length > 100 || /[\x00-\x1f]/.test(location.label))
            throw new Error('Invalid location name.');
        timezone(location.zone);
        if ('language' in location) checkLanguage(location.language);
        if (seen.has(location.zone)) throw new Error(`Duplicate timezone: ${location.zone}`);
        seen.add(location.zone);
    }
    return config;
}

function checkLanguage(language) {
    if (typeof language !== 'string' || !language ||
        Intl.DateTimeFormat.supportedLocalesOf([language]).length !== 1)
        throw new Error('Unsupported clock language.');
}

function validateFormat(template) {
    if (typeof template !== 'string' || !template.trim() || template.length > 200 || /[\x00-\x1f]/.test(template))
        throw new Error('Display format must contain 1–200 printable characters.');
    let allowed = ['city', 'time', 'date', 'weekday', 'offset', 'zone'];
    let remainder = template.replace(/\{([^{}]*)\}/g, (_match, key) => {
        if (!allowed.includes(key)) throw new Error(`Unknown format field: ${key}`);
        return '';
    });
    if (/[{}]/.test(remainder)) throw new Error('Unclosed format field.');
    return template;
}

function formatRow(row, template) {
    validateFormat(template);
    let values = {city: row.label, time: row.time, date: row.fullDate,
        weekday: row.weekday, offset: row.offset, zone: row.zone};
    return template.replace(/\{([^{}]*)\}/g, (_match, key) => values[key]);
}

function clockAt(location, format24, instant = null, showSeconds = false) {
    let date = (instant || GLib.DateTime.new_now_utc()).to_timezone(timezone(location.zone));
    let offset = date.format('%z');
    let timeFormat = format24 ? '%H:%M' : '%I:%M';
    if (showSeconds) timeFormat += ':%S';
    if (!format24) timeFormat += ' %p';
    let result = {label: location.label, zone: location.zone,
        time: date.format(timeFormat),
        weekday: date.format('%A'), fullDate: date.format('%d %B %Y'),
        date: date.format('%a, %d %b %Y'),
        offset: `UTC${offset.slice(0, 3)}:${offset.slice(3, 5)}`};
    if (location.language) {
        checkLanguage(location.language);
        // GLib supplies local wall time from system tzdata. Format those fields
        // in UTC so Intl's own timezone database cannot change the calculation.
        let wallTime = new Date(Date.UTC(date.get_year(), date.get_month() - 1,
            date.get_day_of_month(), date.get_hour(), date.get_minute(), date.get_second()));
        let options = {timeZone: 'UTC', calendar: 'gregory'};
        result.time = new Intl.DateTimeFormat(location.language, Object.assign({}, options,
            Object.assign({hour: '2-digit', minute: '2-digit', hourCycle: format24 ? 'h23' : 'h12'},
                showSeconds ? {second: '2-digit'} : {}))).format(wallTime);
        result.date = new Intl.DateTimeFormat(location.language, Object.assign({}, options,
            {weekday: 'short', day: '2-digit', month: 'short', year: 'numeric'})).format(wallTime);
        result.weekday = new Intl.DateTimeFormat(location.language, Object.assign({}, options, {weekday: 'long'})).format(wallTime);
        result.fullDate = new Intl.DateTimeFormat(location.language, Object.assign({}, options,
            {day: '2-digit', month: 'long', year: 'numeric'})).format(wallTime);
        let number = new Intl.NumberFormat(location.language, {useGrouping: false, minimumIntegerDigits: 2});
        result.offset = `UTC${offset[0]}${number.format(Number(offset.slice(1, 3)))}:${number.format(Number(offset.slice(3, 5)))}`;
    }
    return result;
}

function openSettings(path) {
    Gio.Subprocess.new(['/usr/bin/python3', GLib.build_filenamev([path, 'settings.py'])],
        Gio.SubprocessFlags.NONE);
}

var ClockController = class ClockController {
    constructor(onUpdate) {
        this._onUpdate = onUpdate;
        this._signature = null;
        this._config = defaults();
        this._error = null;
        this._path = GLib.build_filenamev([GLib.get_user_config_dir(), 'world-clocks', 'clocks.json']);
        let directory = GLib.path_get_dirname(this._path);
        GLib.mkdir_with_parents(directory, 0o700);
        this._monitor = Gio.File.new_for_path(directory).monitor_directory(Gio.FileMonitorFlags.NONE, null);
        this._monitor.connect('changed', (_monitor, file, other) => {
            if ((file && file.get_basename() === 'clocks.json') ||
                (other && other.get_basename() === 'clocks.json')) this._load();
        });
        this._load();
        this._timer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 1, () => {
            this._tick();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _load() {
        try {
            if (GLib.file_test(this._path, GLib.FileTest.EXISTS)) {
                let [ok, contents] = GLib.file_get_contents(this._path);
                if (!ok) throw new Error('Cannot read clock settings.');
                this._config = validate(JSON.parse(ByteArray.toString(contents)));
            } else {
                this._config = defaults();
            }
            this._error = null;
        } catch (error) {
            this._error = `Settings error: ${error.message}`;
        }
        this._tick();
    }

    _tick() {
        let rows = [];
        let error = this._error;
        try {
            if (!error) {
                let now = GLib.DateTime.new_now_utc();
                rows = this._config.locations.map(location => clockAt(location, this._config.format24, now, !!this._config.showSeconds));
            }
        } catch (exception) {
            error = exception.message;
        }
        let display = {panelFormat: this._config.panelFormat || '{city}  {time}',
            detailFormat: this._config.detailFormat || '{weekday}, {date}  ·  {offset}'};
        let signature = JSON.stringify([rows, error, display]);
        if (signature !== this._signature) {
            this._signature = signature;
            this._onUpdate(rows, error, display);
        }
    }

    destroy() {
        if (this._timer) GLib.source_remove(this._timer);
        if (this._monitor) this._monitor.cancel();
        this._timer = 0;
        this._monitor = null;
    }
};
