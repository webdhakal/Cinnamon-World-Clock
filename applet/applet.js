const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Clocks = require('./clocks');

class WorldClocksApplet extends Applet.TextApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this._path = metadata.path;
        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);
        this._applet_context_menu.addAction('Locations & time format…', () => Clocks.openSettings(this._path));
        this._controller = new Clocks.ClockController((rows, error, display) => this._render(rows, error, display));
    }

    _render(rows, error, display = {panelFormat: '{city}  {time}'}) {
        this.set_applet_label(error ? 'Clocks ⚠' : rows.length ? Clocks.formatRow(rows[0], display.panelFormat) : 'World Clocks');
        this.set_applet_tooltip(error || rows.map(row => `${row.label}: ${row.time} · ${row.offset}`).join('\n') || 'Choose your locations');
        if (this.menu.isOpen && this._lastError === error && this._menuRows && this._menuRows.length === rows.length) {
            for (let i = 0; i < rows.length; i++) this._menuRows[i].label.set_text(`${rows[i].label}    ${rows[i].time}\n${rows[i].date}  ·  ${rows[i].offset}`);
            return;
        }
        this._lastError = error;
        this._menuRows = [];
        this.menu.removeAll();
        if (error || !rows.length) {
            this.menu.addMenuItem(new PopupMenu.PopupMenuItem(error ? 'Settings error. Open Locations to fix.' : 'No locations selected', {reactive: false}));
        }
        for (let row of rows) {
            let item = new PopupMenu.PopupMenuItem(`${row.label}    ${row.time}\n${row.date}  ·  ${row.offset}`, {reactive: false});
            this._menuRows.push(item);
            this.menu.addMenuItem(item);
        }
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this.menu.addAction('Locations & time format…', () => Clocks.openSettings(this._path));
    }

    on_applet_clicked() {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        if (this._controller) this._controller.destroy();
        if (this.menu) this.menu.destroy();
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new WorldClocksApplet(metadata, orientation, panelHeight, instanceId);
}
