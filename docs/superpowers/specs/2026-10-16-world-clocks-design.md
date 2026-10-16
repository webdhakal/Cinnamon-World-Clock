# World Clocks for Cinnamon

Approved design: a native desktop desklet and bottom-panel applet for Linux Mint Cinnamon. Both read the same user configuration. The desktop lists city, time, date, and UTC offset. The panel shows the first selected city and opens a menu of all clocks. A shared GTK settings window searches the system country/city timezone catalog, adds and removes clocks, reorders them, and selects 12/24-hour format. The first location controls the panel clock. Time calculations use GLib and the system timezone database, including daylight-saving changes. No network services or credentials are needed.

Install and uninstall scripts run as the current user, without sudo. Installation copies files into the user's Cinnamon and application directories; activation is explicit through Cinnamon's desklet/applet settings to preserve existing layouts. Uninstall removes only these files, retaining location preferences. Settings are atomically saved to the XDG config directory; malformed configurations display a visible error and remain untouched. Timers and file monitors are released when widgets are removed.

Validation covers actual GLib timezone formatting (fractional offsets, daylight saving, date boundaries), configuration validation and persistence, staged installation and uninstall, JavaScript syntax, and GTK startup. Live Cinnamon rendering requires a desktop session and is reported separately from automated checks.

## Per-location language extension
Each clock optionally stores a language code. The preferences table exposes a language dropdown and editable location name. New cities suggest a mapped country language (Nepali for Nepal); users choose the appropriate language for multilingual countries. Legacy clocks retain their previous system format. Intl formats language, digits and Gregorian dates using wall-clock fields computed by GLib, preserving system timezone and daylight-saving rules. Both widgets use the same localized row data.

## Clock replacement and display formats
Optional panel/detail templates use {city}, {time}, {weekday}, {date}, {offset}, and {zone}; seconds and 12/24-hour time apply to both widgets. Full dates and weekday names follow each location’s language. Replacement moves the existing World Clocks applet into the stock calendar clock’s position on the same panel and saves both original definitions. Restore merges those definitions with current panel items, avoids duplicate instance IDs, and keeps unrelated layout changes. Uninstall restores the original clock when a backup exists.
