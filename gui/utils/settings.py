import os
import json
import sys

def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # gui/utils/settings.py -> ../../ -> root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SETTINGS_PATH = os.path.join(get_project_root(), "app_settings.json")

def get_default_settings() -> dict:
    """
    Returns the default app_settings.json template with placeholders.
    Uses the executable path as the base for all relative paths.
    """
    base_path = get_project_root()
    return {
        "creation_date": "",
        "krankmeldungen_path": os.path.join(base_path, "tables", "Krankmeldungsliste.xlsx"),
        "krankmeldungen_sheet_name": "Sheet1",
        "kontaktdaten_sheet_name": "Sheet1",
        "kontaktdaten_path": os.path.join(base_path, "tables", "Kontaktdaten.xlsx"),
        "krank_ohne_path": os.path.join(base_path, "templates", "Vorlage_Krankmeldung_OhneAU.pdf"),
        "krank_mit_path": os.path.join(base_path, "templates", "Vorlage_Krankmeldung_MitAU.pdf"),
        "gesund_path": os.path.join(base_path, "templates", "Vorlage_Gesundmeldung.pdf"),
        "au_folder": os.path.join(base_path, "au_files"),
        "export_folder": os.path.join(base_path, "export"),
        "limit_rows": 15
    }

def create_default_settings_if_missing() -> bool:
    """
    Creates the default app_settings.json file if it doesn't exist.
    Returns True if file was created, False if it already existed.
    """
    if not os.path.exists(SETTINGS_PATH):
        default_settings = get_default_settings()
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=2)
            return True
        except Exception:
            return False
    return False

def load_settings() -> dict:
    # Ensure default settings file exists before loading
    create_default_settings_if_missing()
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return get_default_settings()

def save_settings(settings: dict):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass
