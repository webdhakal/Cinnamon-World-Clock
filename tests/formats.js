const GLib = imports.gi.GLib;
imports.searchPath.unshift(GLib.build_filenamev([GLib.get_current_dir(), 'shared']));
const Clocks = imports.clocks;
function equal(actual, expected) { if (actual !== expected) throw new Error(`Expected ${expected}, got ${actual}`); }
let instant = GLib.DateTime.new_from_iso8601('2026-01-01T00:00:07Z', null);
let row = Clocks.clockAt({zone:'Asia/Kathmandu',label:'काठमाडौं',language:'ne-NP'}, true, instant, true);
equal(row.time, '०५:४५:०७');
equal(row.weekday, 'बिहिबार');
if (!row.fullDate.includes('जनवरी') || !row.fullDate.includes('२०२६')) throw new Error('Full date missing');
equal(Clocks.formatRow(row, '{weekday} · {date} · {time}'), `${row.weekday} · ${row.fullDate} · ${row.time}`);
equal(Clocks.formatRow(row, '{city} {city} {offset}'), `काठमाडौं काठमाडौं ${row.offset}`);
equal(Clocks.formatRow(row, '{zone}'), 'Asia/Kathmandu');
let legacy = Clocks.clockAt({zone:'UTC',label:'UTC'}, true, instant, true);
equal(legacy.time, '00:00:07');
equal(legacy.weekday, 'Thursday');
equal(legacy.fullDate, '01 January 2026');
for (let format of ['', '{invalid}', '{time', '{time}\n', 12]) {
    let rejected = false;
    try { Clocks.validate({version:1, format24:true, locations:[], panelFormat:format}); } catch (e) { rejected = true; }
    equal(rejected, true);
}
print('PASS: localized full weekday/date, seconds, custom format, invalid templates');
