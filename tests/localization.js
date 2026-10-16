const GLib = imports.gi.GLib;
imports.searchPath.unshift(GLib.build_filenamev([GLib.get_current_dir(), 'shared']));
const Clocks = imports.clocks;
function equal(actual, expected) {
    if (actual !== expected) throw new Error(`Expected ${expected}, got ${actual}`);
}
let instant = GLib.DateTime.new_from_iso8601('2026-01-01T00:00:00Z', null);
let nepali = Clocks.clockAt({zone: 'Asia/Kathmandu', label: 'काठमाडौं', language: 'ne-NP'}, true, instant);
equal(nepali.label, 'काठमाडौं');
equal(nepali.time, '०५:४५');
equal(nepali.offset, 'UTC+०५:४५');
if (!nepali.date.includes('जनवरी') || !nepali.date.includes('२०२६')) throw new Error('Nepali date was not localized');
let french = Clocks.clockAt({zone: 'Europe/Paris', label: 'Paris', language: 'fr-FR'}, true, instant);
equal(french.time, '01:00');
if (!french.date.includes('janv.')) throw new Error('French date was not localized');
let before = GLib.DateTime.new_from_iso8601('2026-03-08T06:59:00Z', null);
let after = GLib.DateTime.new_from_iso8601('2026-03-08T07:00:00Z', null);
equal(Clocks.clockAt({zone: 'America/New_York', label: 'NY', language: 'ne-NP'}, true, before).time, '०१:५९');
equal(Clocks.clockAt({zone: 'America/New_York', label: 'NY', language: 'ne-NP'}, true, after).time, '०३:००');
let twelve = Clocks.clockAt({zone: 'Asia/Kathmandu', label: 'Kathmandu', language: 'ne-NP'}, false, instant);
if (!twelve.time.includes('५:४५') || !twelve.time.includes('पूर्वाह्न')) throw new Error('Nepali 12-hour period missing');
let rejected = false;
try { Clocks.validate({version: 1, format24: true, locations: [{zone: 'UTC', label: 'UTC', language: 'zz-ZZ'}]}); }
catch (e) { rejected = true; }
equal(rejected, true);
print('PASS: Nepali digits/date/period/offset, French date, localized DST, unsupported language');
let [loaded, contents] = GLib.file_get_contents(GLib.build_filenamev([GLib.get_current_dir(), 'shared', 'languages.json']));
if (!loaded) throw new Error('Language catalog missing');
const ByteArray = imports.byteArray;
for (let language of JSON.parse(ByteArray.toString(contents))) {
    Clocks.validate({version: 1, format24: true, locations: [{zone: 'UTC', label: 'UTC', language: language.code}]});
    let localized = Clocks.clockAt({zone: 'UTC', label: 'UTC', language: language.code}, true, instant);
    if (!localized.time || !localized.date) throw new Error(`Empty output for ${language.code}`);
}
print('PASS: all language-selector choices supported by the installed runtime');
