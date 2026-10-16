const GLib = imports.gi.GLib;
const Gio = imports.gi.Gio;
const temp = GLib.dir_make_tmp('world-clocks-controller-XXXXXX');
GLib.setenv('XDG_CONFIG_HOME', temp, true);
imports.searchPath.unshift(GLib.build_filenamev([GLib.get_current_dir(), 'shared']));
const Clocks = imports.clocks;
function assert(value, message) { if (!value) throw new Error(message); }
let events = [];
let controller = new Clocks.ClockController((rows, error) => events.push({rows, error}));
let path = GLib.build_filenamev([temp, 'world-clocks', 'clocks.json']);
function last() { return events[events.length - 1]; }
function waitFor(predicate) {
    let loop = new GLib.MainLoop(null, false);
    let attempts = 0;
    let success = false;
    GLib.timeout_add(GLib.PRIORITY_DEFAULT, 10, () => {
        success = predicate();
        if (success || attempts++ > 300) {
            loop.quit();
            return GLib.SOURCE_REMOVE;
        }
        return GLib.SOURCE_CONTINUE;
    });
    loop.run();
    assert(success, 'Timed out waiting for settings monitor');
}
try {
    assert(last().rows[0].label === 'Kathmandu', 'Default clocks not loaded');
    // Gio replacement mirrors the atomic saves used by the preferences window.
    Gio.File.new_for_path(path).replace_contents(JSON.stringify({version: 1, format24: false,
        locations: [{zone: 'UTC', label: 'Test UTC'}]}), null, false, Gio.FileCreateFlags.NONE, null);
    waitFor(() => last().rows.length === 1 && last().rows[0].label === 'Test UTC');
    GLib.file_set_contents(path, '{broken');
    waitFor(() => !!last().error);
    assert(last().rows.length === 0, 'Invalid configuration should show an error');
    GLib.file_set_contents(path, JSON.stringify({version: 1, format24: true, locations: []}));
    waitFor(() => !last().error && last().rows.length === 0);
    GLib.unlink(path);
    waitFor(() => last().rows.length === 3);
    controller.destroy();
    assert(controller._timer === 0 && controller._monitor === null, 'Controller leaked resources');
    print('PASS: live file monitoring, malformed config, recovery, deletion, resource cleanup');
} finally {
    controller.destroy();
    GLib.unlink(path);
    GLib.rmdir(GLib.path_get_dirname(path));
    GLib.rmdir(temp);
}
