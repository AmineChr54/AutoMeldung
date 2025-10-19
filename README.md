Automeldung — PDF Automation
============================

Automeldung creates filled PDFs for Krankmeldungen and Gesundmeldungen from an Excel table, optionally merging an AU attachment. It includes a simple Flet-based GUI and a backend pipeline that handles form filling, merging, and flattening.

Features
--------
- Read data from an Excel Krankmeldungsliste and optional Kontaktdaten.
- Generate two kinds of forms:
	- Krankmeldung (Ohne AU / Mit AU)
	- Gesundmeldung
- Merge Krank + optional AU + Gesund into a single PDF per row.
- Convert AU images (e.g., JPG/PNG/WebP) to A4 PDF automatically.
- Flatten final PDFs so filled values are printed correctly and fields are removed.
- GUI with file/folder pickers, sheet name inputs, row limit, collapsible sections, and a scrolling status log.
- Settings persist to app_settings.json and are auto-loaded by the backend (no code changes needed).

Project structure (high level)
------------------------------
- `gui/app.py` — Flet desktop UI.
- `automeldung/main_exporter.py` — Orchestrates row processing and PDF creation.
- `automeldung/config.py` — Central configuration and settings loader; also exposes a simple logger for the GUI.
- `automeldung/utils/` — Implementation details for data, PDF merging/flattening, and image conversion.
- `templates/` — PDF templates (Krankmeldung ohne/mit AU, Gesundmeldung).
- `tables/` — Example Excel files.
- `au_files/` — AU attachments (images or PDFs).
- `export/` — Output PDFs.

Requirements
------------
- Python 3.10+ recommended
- Dependencies listed in `requirements.txt` (pandas, openpyxl, pikepdf, reportlab, PyPDF2, flet)

Setup
-----
1. Create a virtual environment and install dependencies:
	 - Windows (PowerShell):
		 - `python -m venv .venv`
		 - `.venv\\Scripts\\Activate` (or use VS Code Python interpreter picker)
		 - `pip install -r requirements.txt`
2. Ensure your templates and data exist (see Configuration below).

Run the GUI
-----------
- From the project root:
	- `python gui/app.py`

What the GUI provides:
- Input Files section (collapsible):
	- Krankmeldungen (.xlsx) + Sheet Name
	- Kontaktdaten (.xlsx) + Sheet Name
	- Krankmeldung templates (Ohne AU, Mit AU) and Gesundmeldung template
	- AU Files folder
- Export Options (collapsible):
	- Export folder
	- Limit rows (processes only the first N rows)
- Status panel: shows live logs from the backend.

Run from CLI (optional)
-----------------------
You can also run the exporter directly without the GUI:

- `python -c "from automeldung.main_exporter import main_exporter as run; run()"`

Note: The backend reads `app_settings.json` automatically via `automeldung.config`, so any paths you picked in the GUI are used by the CLI too. If a setting is missing, config defaults are used.

Configuration
-------------
Defaults live in `automeldung/config.py`. When present, `app_settings.json` overrides these at import time. Relevant keys:
- `krankmeldungen_path` → `config.krankmeldungsliste_path`
- `krankmeldungen_sheet_name` → `config.krankmeldungsliste_sheet_name`
- `kontaktdaten_path` → `config.kontaktdaten_path`
- `kontaktdaten_sheet_name` → `config.kontaktdaten_sheet_name`
- `krank_ohne_path` → `config.vorlage_krankmeldung_ohne_au_path`
- `krank_mit_path` → `config.vorlage_krankmeldung_mit_au_path`
- `gesund_path` → `config.vorlage_gesundmeldung_path`
- `au_folder` → `config.au_files_path`
- `export_folder` → `config.export_path`
- `limit_rows` → `config.limit_rows` (default 20)

Settings persistence
--------------------
- The GUI stores selections in `app_settings.json` in the project root.
- The backend loads and applies these settings automatically when `automeldung.config` is imported.
- You can delete `app_settings.json` to reset saved values.

How it works (brief)
--------------------
1. Read rows from the Excel Krankmeldungsliste (sheet name selectable in UI).
2. For each selected row:
	 - If `summe_der_tage` ≤ 3: create Krankmeldung Ohne AU + Gesundmeldung.
	 - Else: create Krankmeldung Mit AU (+ optional AU attachment) + Gesundmeldung.
3. Merge PDFs (Krank + optional AU + Gesund) and flatten to final output.

Packaging the GUI (optional)
----------------------------
You can build a desktop executable with Flet’s pack command:
- From `gui/`: `flet pack app.py`
The output bundle will be created in a `dist/` folder.

Troubleshooting
---------------
- No output PDFs: verify template paths and the export folder in the GUI.
- Missing Excel columns: ensure your Excel file matches expected column names (see `INDEX_KM`/`INDEX_KD` in `config.py`).
- AU not found: filenames in `au_files/` should start with the `au_file_id` (case-insensitive). Images will be converted to PDF automatically.
- Blue highlight in forms: final PDFs are flattened to remove form fields and appearance issues.
