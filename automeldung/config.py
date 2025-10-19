# --- Load overrides from persisted app settings (if present) ---
# This lets the backend pick up values saved by the GUI without modifying code elsewhere.
import os
import json
from typing import Any, Dict

def _project_root() -> str:
       # This file is in <project>/automeldung/config.py -> go one level up
       return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_APP_SETTINGS_PATH = os.path.join(_project_root(), "app_settings.json")

def _load_settings(path: str) -> Dict[str, Any]:
       try:
              if os.path.exists(path):
                     with open(path, "r", encoding="utf-8") as f:
                            return json.load(f)
       except Exception:
              pass
       return {}

def _apply_settings(settings: Dict[str, Any]):
       if not settings:
              return

       def _strval(key: str):
              v = settings.get(key)
              if isinstance(v, str):
                     v = v.strip()
              return v if v not in (None, "") else None

       # Direct mappings from settings keys to config variable names
       direct_map = {
              # current keys
              "krankmeldungen_path": "krankmeldungsliste_path",
              "krankmeldungen_sheet_name": "krankmeldungsliste_sheet_name",
              "kontaktdaten_path": "kontaktdaten_path",
              "kontaktdaten_sheet_name": "kontaktdaten_sheet_name",
              "krank_ohne_path": "vorlage_krankmeldung_ohne_au_path",
              "krank_mit_path": "vorlage_krankmeldung_mit_au_path",
              "gesund_path": "vorlage_gesundmeldung_path",
              "au_folder": "au_files_path",
              "export_folder": "export_path",
              "limit_rows": "limit_rows",
       }

       for s_key, cfg_name in direct_map.items():
              val = _strval(s_key)
              if val:
                     globals()[cfg_name] = val

       # Legacy keys compatibility (from early UI versions)
       excel_path = _strval("excel_path")
       if excel_path:
              globals()["krankmeldungsliste_path"] = excel_path

       krank_path = _strval("krank_path")
       if krank_path:
              # If specific ones weren't set by current keys, set both to legacy value
              if not _strval("krank_ohne_path"):
                     globals()["vorlage_krankmeldung_ohne_au_path"] = krank_path
              if not _strval("krank_mit_path"):
                     globals()["vorlage_krankmeldung_mit_au_path"] = krank_path

       gesund_legacy = _strval("gesund_path")
       if gesund_legacy:
              globals()["vorlage_gesundmeldung_path"] = gesund_legacy

# Apply settings on import (safe no-op if file is missing)
_apply_settings(_load_settings(_APP_SETTINGS_PATH))

# --- Simple logging hook so GUI can receive logs ---
from typing import Callable, Optional

_log_fn: Optional[Callable[[str], None]] = None

def set_logger(fn: Callable[[str], None]):
       """Set a callable to receive log messages (e.g., GUI's append_log)."""
       global _log_fn
       _log_fn = fn

def log(msg: str):
       """Log to GUI if available, else print to stdout."""
       try:
              if _log_fn:
                     _log_fn(str(msg))
              else:
                     print(msg)
       except Exception:
              try:
                     print(msg)
              except Exception:
                     pass