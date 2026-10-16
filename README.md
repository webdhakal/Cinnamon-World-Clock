# World Clocks for Linux Mint Cinnamon

A desktop clock widget and a compact panel clock with one shared location list. Search countries and cities, add several timezones, reorder them, and switch between 12-hour and 24-hour time. Uses the system timezone database, works offline, and follows daylight-saving changes automatically.

Designed for Cinnamon on Linux Mint 22.3. GNOME, KDE, and other desktop environments are not supported.

## Install

From this project folder:

```bash
cd /home/dhakal/sites/timezone-widgets
./install.sh
cinnamon-settings desklets
```

Select **World Clocks** in the Installed tab and click **+** to add it to your desktop. You can drag it to your preferred position; unlock desklet positioning in Cinnamon settings if necessary.

Then add the bottom-panel clock:

```bash
cinnamon-settings applets
```

Select **World Clocks** in the Installed tab and click **+**. Cinnamon uses your selected panel; if you have several panels, select your bottom panel first. Use panel edit mode to move the applet.

No sudo is needed. The installer checks for Cinnamon, Python 3, GTK 3 and timezone data, which are included in standard Linux Mint Cinnamon installations. There is no remote download command until this project is published; these commands install the local source.

## Choose your locations

Click **Locations +** on the desktop widget, or **Locations & time format…** in the panel clock menu. You can also launch **World Clocks Locations** from the application menu.

1. Search a country, city, or timezone, such as `Nepal`, `United States`, or `London`.
2. Select a result and click **Add selected location** (or double-click it).
3. Use **Move up**, **Move down**, or **Remove** to edit your list.
4. Click a clock’s **Language** cell to choose its display language, for example **नेपाली (Nepali)** for Nepal. New locations suggest a country language where available; you can override it for multilingual countries. Existing clocks keep **System default** until you choose a language.
5. Click its **Location** name to enter a native name, such as `काठमाडौं`.
6. Choose **Use 24-hour time** or turn it off for 12-hour time.
7. Click **Save changes**. Both widgets update automatically.

The first location appears in the panel. Click it to view every selected city's time, date and UTC offset. The desktop displays the entire list. Defaults are Kathmandu, London, and New York. Countries with multiple timezones have multiple city choices; the list comes from the system catalog and does not include every city in the world.

Language applies separately to each clock in both widgets, including weekday/month names, digits, AM/PM text, and UTC-offset digits. For example, Kathmandu can display `०५:४५` while London remains in English. The language selector offers 40 languages/variants. Location names are editable rather than automatically translated. Dates use the Gregorian calendar; Nepali language does not convert dates to Bikram Sambat.

Preferences are saved to `${XDG_CONFIG_HOME:-$HOME/.config}/world-clocks/clocks.json`. Widget files and the preferences launcher use `${XDG_DATA_HOME:-$HOME/.local/share}`. A damaged settings file is preserved and reported; fix or move it, then reopen settings. Up to 100 locations are supported; smaller lists fit the desktop and panel menu best.

## Panel formats and replacing the system clock

Open **Locations & time format… → Display & panel**. Choose a panel preset (time only, city and time, weekday and time, full weekday/date/time, or date and time), or edit the format directly. The desktop detail line has its own format. **Show seconds** and **Use 24-hour time** apply to both widgets. Click **Save changes** to apply display settings.

Available fields:

| Field | Shows |
| --- | --- |
| `{city}` | Your location name |
| `{time}` | Local time in your selected language and 12/24-hour format |
| `{weekday}` | Full weekday name |
| `{date}` | Full Gregorian date with month name and year |
| `{offset}` | UTC offset |
| `{zone}` | Timezone identifier |

Example: `{weekday}, {date} · {time}` displays the full day, date and time in each clock’s language, including Nepali digits.

Click **Replace system clock** to move World Clocks into the original clock’s position on the same panel. Other panel items stay in place. This takes effect immediately; the original position is saved in `world-clocks/system-clock-backup.json` under your config directory. **Restore system clock** restores the original clock and calendar menu, and returns World Clocks to its previous position. Uninstall also restores a clock that was replaced through this feature.

## Update and uninstall

Run `./install.sh` again to update. Cinnamon can keep an older formatter in memory even after files are replaced. Reload active widgets to load the updated code without changing their positions:

```bash
gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon --method org.Cinnamon.ReloadXlet world-clocks-panel@local APPLET
gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon --method org.Cinnamon.ReloadXlet world-clocks-desklet@local DESKLET
```

If a clock still shows English after choosing Nepali, use the reload command above for that widget.

```bash
./uninstall.sh
```

Uninstall removes both widget registrations and installed files while retaining your saved locations. It is also available after deleting the source folder:

```bash
bash "${XDG_DATA_HOME:-$HOME/.local/share}/world-clocks/uninstall.sh"
```

## Verification

```bash
/usr/bin/python3 -m unittest discover -s tests -v
LC_ALL=C cjs tests/clocks.js
LC_ALL=C cjs tests/controller.js
LC_ALL=C cjs tests/localization.js
LC_ALL=C cjs tests/formats.js
node --check shared/clocks.js
node --check desklet/desklet.js
node --check applet/applet.js
bash -n install.sh uninstall.sh
```

Tests cover country lookup, configuration validation and atomic persistence, preserving malformed settings, real GLib fractional offsets and daylight-saving transitions, and installation/update/uninstallation in temporary XDG directories. Node is needed only for optional syntax checks, not to run the widgets.

For a settings-window startup check in a graphical session:

```bash
/usr/bin/python3 shared/settings.py --smoke-test
```

For live verification, add both widgets in Cinnamon, save a different list/order/time format, verify both update, then remove them. Rendering and panel placement must be checked in the running Cinnamon session.

To exercise the settings controls with temporary preferences in a graphical session:

```bash
task_config=$(mktemp -d)
XDG_CONFIG_HOME="$task_config" /usr/bin/python3 tests/ui_smoke.py
```

`/usr/bin/python3 tests/native_smoke.py` constructs and destroys staged widgets inside the running Cinnamon shell through its D-Bus test interface, without adding them to your layouts.
