const Desklet = imports.ui.desklet;
const St = imports.gi.St;
const Clocks = require('./clocks');

class WorldClocksDesklet extends Desklet.Desklet {
    constructor(metadata, instanceId) {
        super(metadata, instanceId);
        this.setHeader('World Clocks');
        this._box = new St.BoxLayout({vertical: true, style_class: 'world-clocks-card'});
        this.setContent(this._box);
        this._menu.addAction('Locations & time format…', () => Clocks.openSettings(metadata.path));
        this._controller = new Clocks.ClockController((rows, error, display) => this._render(rows, error, display));
    }

    _render(rows, error, display = {detailFormat: '{weekday}, {date}  ·  {offset}'}) {
        let structure = JSON.stringify([rows.map(row => [row.label, row.zone]), error]);
        if (structure === this._structure && this._clockLabels) {
            rows.forEach((row, index) => {
                this._clockLabels[index].time.set_text(row.time);
                this._clockLabels[index].detail.set_text(Clocks.formatRow(row, display.detailFormat));
            });
            return;
        }
        this._structure = structure;
        this._clockLabels = [];
        this._box.destroy_all_children();
        let heading = new St.BoxLayout({style_class: 'world-clocks-heading'});
        heading.add_actor(new St.Label({text: 'WORLD CLOCKS', style_class: 'world-clocks-eyebrow', x_expand: true}));
        let settings = new St.Button({label: 'Locations +', style_class: 'world-clocks-settings', can_focus: true});
        settings.connect('clicked', () => Clocks.openSettings(this.metadata.path));
        heading.add_actor(settings);
        this._box.add_actor(heading);
        if (error || !rows.length) {
            this._box.add_actor(new St.Label({text: error ? 'Settings error. Open Locations to fix.' : 'Add your first location using Locations +.'}));
            return;
        }
        for (let row of rows) {
            let box = new St.BoxLayout({vertical: true, style_class: 'world-clocks-location'});
            let line = new St.BoxLayout();
            line.add_actor(new St.Label({text: row.label, style_class: 'world-clocks-city', x_expand: true}));
            let timeLabel = new St.Label({text: row.time, style_class: 'world-clocks-time'});
            line.add_actor(timeLabel);
            box.add_actor(line);
            let detailLabel = new St.Label({text: Clocks.formatRow(row, display.detailFormat), style_class: 'world-clocks-detail'});
            box.add_actor(detailLabel);
            this._clockLabels.push({time: timeLabel, detail: detailLabel});
            this._box.add_actor(box);
        }
    }

    on_desklet_removed() {
        if (this._controller) this._controller.destroy();
    }
}

function main(metadata, instanceId) {
    return new WorldClocksDesklet(metadata, instanceId);
}
