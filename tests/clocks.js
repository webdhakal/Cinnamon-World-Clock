const GLib = imports.gi.GLib;
imports.searchPath.unshift(GLib.build_filenamev([GLib.get_current_dir(), 'shared']));
const Clocks = imports.clocks;
function equal(actual, expected) {
    if (actual !== expected) throw new Error(`Expected ${expected}, got ${actual}`);
}
let instant = GLib.DateTime.new_from_iso8601('2026-01-01T00:00:00Z', null);
let nepal = Clocks.clockAt({zone: 'Asia/Kathmandu', label: 'Kathmandu'}, true, instant);
equal(nepal.time, '05:45');
equal(nepal.offset, 'UTC+05:45');
equal(Clocks.clockAt({zone: 'America/New_York', label: 'NY'}, true, instant).date, 'Wed, 31 Dec 2025');
let before = GLib.DateTime.new_from_iso8601('2026-03-08T06:59:00Z', null);
let after = GLib.DateTime.new_from_iso8601('2026-03-08T07:00:00Z', null);
equal(Clocks.clockAt({zone: 'America/New_York', label: 'NY'}, true, before).time, '01:59');
equal(Clocks.clockAt({zone: 'America/New_York', label: 'NY'}, true, after).time, '03:00');
equal(Clocks.clockAt({zone: 'America/New_York', label: 'NY'}, true, after).offset, 'UTC-04:00');
equal(Clocks.clockAt({zone: 'UTC', label: 'UTC'}, false, instant).time, '12:00 AM');
let rejected = false;
try { Clocks.clockAt({zone: 'Fake/City', label: 'Oops'}, true, instant); } catch (e) { rejected = true; }
equal(rejected, true);
print('PASS: fractional offsets, date rollover, DST transition, 12-hour format, invalid zone');
