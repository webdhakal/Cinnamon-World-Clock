# World Clocks Implementation Plan

**Goal:** Install native desktop and panel world clocks for Cinnamon.
**Architecture:** Two small Cinnamon entry points share a copied JavaScript clock/configuration module and a Python GTK preferences application. JSON preferences are monitored by both widgets.
**Tech stack:** Cinnamon JavaScript, GLib/Gio/St, Python 3, GTK 3, shell.

## Constraints
- Linux Mint Cinnamon; per-user install; no sudo, network service, or npm packages.
- One shared ordered city list, 12/24-hour format, automatic daylight saving.
- Preserve malformed settings and existing panel/desktop layouts.

## Tasks
- [x] Add tests for configuration persistence, country lookup, invalid zones, real GLib timezone conversions, and staged installer lifecycle. Run before implementation and confirm missing-feature failures.
- [x] Implement `shared/preferences.py` for validated atomic persistence and country/city catalog, then `shared/settings.py` for searchable GTK preferences with add/remove/reorder and time format controls. Run Python tests and GTK startup checks.
- [x] Implement `shared/clocks.js` for formatting, monitored configuration, cleanup and settings launch. Add `desklet/desklet.js`, `applet/applet.js`, metadata and styles. Run real GLib tests with `cjs` and JavaScript syntax checks.
- [x] Implement per-user `install.sh` and `uninstall.sh`, provide launcher and README. Run staged lifecycle test and shell syntax checks. Document Cinnamon activation and live-session verification limits.

## Verification result
All automated checks passed, including real GTK controls and native Cinnamon widget construction. Placement remains an explicit user action through Cinnamon Settings. No Git commit was made because this directory is not a Git repository.

## Per-location language extension
- [x] Verify failing tests for Nepali digits/dates, optional persisted language, unsupported-language rejection, and Nepal's suggested language.
- [x] Add the shared language catalog, per-row language selector and editable location names, preserving legacy clock formats.
- [x] Localize GLib-computed wall times through Intl; verify Nepali and French formats, localized DST, all offered languages, installer packaging, GTK controls, and native Cinnamon construction.

## Clock replacement and display formats
- [x] Add failing format validation, localized full-date/weekday/seconds, and panel replace/restore tests.
- [x] Implement optional templates, seconds, Display & panel controls, and saved replacement/restore positions.
- [x] Verify 13 Python tests, all timezone/localization/format checks, GTK controls, native rendering, and the live installed panel label.
