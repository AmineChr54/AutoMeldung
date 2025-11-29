import os
import json
import sys

def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # gui/utils/settings.py -> ../../ -> root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SETTINGS_PATH = os.path.join(get_project_root(), "app_settings.json")

def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(settings: dict):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass
