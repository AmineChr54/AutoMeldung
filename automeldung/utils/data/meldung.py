import pandas as pd
from typing import Optional, Tuple
from openpyxl import load_workbook

import automeldung.config as config
from automeldung.utils.data.data_extractor import create_dataframe_from_excel_table

kontaktdaten = create_dataframe_from_excel_table(config.kontaktdaten_path)

class Meldung:  
    def __init__(self, row):
        # Resolve the Excel fill color of the Nachname cell for this person
        self.nachname = row.nachname.strip()
        self.vorname = row.vorname.strip()
        self.fullname = f"{self.nachname}, {self.vorname}"
        # Parse required dates but be tolerant of missing/invalid values
        self.von_date = pd.to_datetime(row.von, format="%d.%m.%Y", errors="coerce")
        self.bis_date = pd.to_datetime(row.bis, format="%d.%m.%Y", errors="coerce")
        # TODO else please release an error because this is crucial
        self.von_date_parsed = self.von_date.strftime("%d.%m.%Y") if pd.notna(self.von_date) else ""
        self.bis_date_parsed = self.bis_date.strftime("%d.%m.%Y") if pd.notna(self.bis_date) else ""
        self.wiederaufnahme_date = (
            (self.bis_date + pd.Timedelta(days=1)).strftime("%d.%m.%Y")
            if pd.notna(self.bis_date)
            else ""
        )
        self.zuletzt_date = (
            (self.von_date - pd.Timedelta(days=1)).strftime("%d.%m.%Y")
            if pd.notna(self.von_date)
            else ""
        )
        self.todays_date = pd.Timestamp.now().strftime("%d.%m.%Y")
        self.has_AU = getattr(row, "au", False)
        self.has_eAU = getattr(row, "eau", False)
        self.au_file_id = row.au_file_id
        # Parse optional AU dates safely; coerce invalid/missing to NaT
        self.au_von = pd.to_datetime(getattr(row, "au_von", None), format="%d.%m.%Y", errors="coerce")
        self.au_bis = pd.to_datetime(getattr(row, "au_bis", None), format="%d.%m.%Y", errors="coerce")
        # Only strftime when the value is a valid Timestamp (not NaT)
        self.au_von_parsed = self.au_von.strftime("%d.%m.%Y") if pd.notna(self.au_von) else self.von_date_parsed
        self.au_bis_parsed = self.au_bis.strftime("%d.%m.%Y") if pd.notna(self.au_bis) else self.bis_date_parsed

        # Compute ohne ranges only when AU start exists; otherwise fall back to original dates
        if pd.notna(self.au_von):
            self.von_ohne_parsed = "" if (self.von_date_parsed == self.au_von_parsed) else self.von_date_parsed
            self.bis_ohne_parsed = ("" if (self.von_date_parsed == self.au_von_parsed) else (self.au_von - pd.Timedelta(days=1)).strftime("%d.%m.%Y"))
        else:
            self.von_ohne_parsed = ""
            self.bis_ohne_parsed = ""

        self.PNr = kontaktdaten.loc[(kontaktdaten['nachname'] == self.nachname) & (kontaktdaten['vorname'] == self.vorname),'persnr'].values[0]

    def get_values(self):
        return (
            self.fullname,
            self.von_date,
            self.bis_date,
            self.wiederaufnahme_date,
            self.zuletzt_date,
            self.todays_date,
            self.PNr
        )

    @staticmethod
    def check_info_validity(row) -> Tuple[bool, str]:
        def _is_empty(val) -> bool:
            if val is None:
                return True
            try:
                if pd.isna(val):
                    return True
            except Exception:
                pass
            if isinstance(val, str) and val.strip() == "":
                return True
            return False

        # Consider the row empty if all key fields are empty
        key_fields = [
            "nachname", "vorname", "von", "bis", "au_file_id",
        ]
        if all(_is_empty(getattr(row, f, None)) for f in key_fields):
            return False, "Line is empty."

        errors = []

        nachname = getattr(row, "nachname", None)
        vorname = getattr(row, "vorname", None)

        # 1 - Nachname and Vorname check
        if _is_empty(nachname):
            errors.append("Missing 'nachname'")
        if _is_empty(vorname):
            errors.append("Missing 'vorname'")

        if not errors:
            nn = (nachname or "").strip()
            vn = (vorname or "").strip()
            try:
                has_last = kontaktdaten['nachname'].eq(nn).any()
                has_first = kontaktdaten['vorname'].eq(vn).any()
                vertrag_in_fachbereich = kontaktdaten.loc[(kontaktdaten['vorname'].str.startswith(vorname) & kontaktdaten['nachname'].str.startswith(nachname)),"vertrag_im"].eq('FB').item()
                if vertrag_in_fachbereich:
                    errors.append("Vertrag im Fachbereich, Meldung wird nicht erstellt.")
                if not has_last:
                    errors.append("Unknown 'nachname' in kontaktdaten")
                if not has_first:
                    errors.append("Unknown 'vorname' in kontaktdaten")
                if has_last and has_first:
                    pair_exists = ((kontaktdaten['nachname'] == nn) & (kontaktdaten['vorname'] == vn)).any()
                    if not pair_exists:
                        errors.append("Name combination not found in kontaktdaten")
            except Exception as e:
                # If kontaktdaten is unavailable or columns missing, mark as error
                errors.append(f"kontaktdaten lookup failed with error {e}")

        # 2 - AU aber kein AU_file
        au_flag = bool(getattr(row, "au", False))
        au_file_id = getattr(row, "au_file_id", None)
        if au_flag and _is_empty(au_file_id):
            errors.append("'au' is true but 'au_file_id' is empty")

        # 3 - au_von and au_bis fields check
        if row.eau or row.au:
            au_von = getattr(row, "au_von", None)
            au_bis = getattr(row, "au_bis", None)
            if not (_is_empty(au_von) or _is_empty(au_bis)):
                if not (row.von <= au_von <= au_bis and au_bis == row.bis):
                    errors.append("'au_von' and 'au_bis' must be between 'von' and 'bis")
            elif not _is_empty(au_von):
                if not (row.von <= au_von):
                    errors.append("'au_von' must be between 'von' and 'bis'")
            elif not _is_empty(au_bis):
                if not (row.von <= au_bis and au_bis == row.bis):
                    errors.append("'au_bis' must be between 'von' and 'bis'")

        # 4 - case where eau and au boxes are not checked, but need to
        if (not (row.eau or row.au)) and Meldung.get_days_sum(row) > 3:
            errors.append("days sick > 3, but eAU or AU boxes are not")


        # Endcheck
        if errors:
            # Provide a short context with name if available
            name_ctx = ", ".join([s for s in [(nachname or "").strip(), (vorname or "").strip()] if s]) or "Unknown"
            return False, f"error: {name_ctx}: " + "; ".join(errors)

        return True, ""
    
    @staticmethod
    def get_days_sum(row) -> int:
        if row.summe_der_tage and row.summe_der_tage > 0:
            return row.summe_der_tage
        try:
            von_date = pd.to_datetime(row.von, format="%d.%m.%Y", errors="coerce")
            bis_date = pd.to_datetime(row.bis, format="%d.%m.%Y", errors="coerce")
            if pd.notna(von_date) and pd.notna(bis_date):
                delta = (bis_date - von_date).days + 1
                return max(delta, 0)
        except Exception:
            pass
        return 0
    