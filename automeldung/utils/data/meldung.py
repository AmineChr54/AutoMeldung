import pandas as pd
from typing import Optional, Tuple
from openpyxl import load_workbook

import automeldung.config as config
from automeldung.utils.data.data_extractor import create_dataframe_from_excel_table

kontaktdaten = create_dataframe_from_excel_table(config.kontaktdaten_path)

class Meldung:  
    def __init__(self, row):
        # Resolve the Excel fill color of the Nachname cell for this person
        self.color = self.get_color(
            xlsx_path=config.kontaktdaten_path,
            current_cell=row.nachname,
            sheet_name=config.krankmeldungsliste_sheet_name,
        )
        self.nachname = row.nachname.strip()
        self.vorname = row.vorname.strip()
        self.fullname = f"{self.nachname}, {self.vorname}"
        # Parse required dates but be tolerant of missing/invalid values
        self.von_date = pd.to_datetime(row.von, format="%d.%m.%Y", errors="coerce")
        self.bis_date = pd.to_datetime(row.bis, format="%d.%m.%Y", errors="coerce")
        # Only format when not NaT
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
        self.au_von_parsed = self.au_von.strftime("%d.%m.%Y") if pd.notna(self.au_von) else ""
        self.au_bis_parsed = self.au_bis.strftime("%d.%m.%Y") if pd.notna(self.au_bis) else ""
        # Compute ohne ranges only when AU start exists; otherwise fall back to original dates
        if pd.notna(self.au_von):
            # If von_date is NaT, equality check will be False; fall back to existing parsed strings
            self.von_ohne_parsed = "" if (pd.notna(self.von_date) and self.von_date == self.au_von) else self.von_date_parsed
            self.bis_ohne_parsed = (
                ""
                if (pd.notna(self.von_date) and self.von_date == self.au_von)
                else (self.au_von - pd.Timedelta(days=1)).strftime("%d.%m.%Y")
            )
        else:
            self.von_ohne_parsed = self.von_date_parsed
            self.bis_ohne_parsed = ""
        self.PNr = kontaktdaten.loc[
            (kontaktdaten['nachname'] == self.nachname) & (kontaktdaten['vorname'] == self.vorname),
        'persnr'
    ].values[0]

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
    def get_color(
        xlsx_path: str,
        current_cell: str,
        sheet_name: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Return the Excel fill color of the Nachname/Name cell for the row matching 'nachname' only.
        Output is a dict with best-effort normalized values, e.g.:
        {
            'type': 'rgb',
            'argb': 'FFFFE699',   # ARGB hex if available
            'rgb': 'FFE699'       # RGB part if available
        }
        If color cannot be determined, returns None.
        """
        try:
            wb = load_workbook(xlsx_path)
        except Exception:
            return None
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active

        # Build header mapping from the first row
        headers = {str(c.value).strip(): i for i, c in enumerate(ws[1], start=1) if c.value is not None}
        name_col_idx = headers.get("Name") or headers.get("Nachname") or headers.get("nachname")

        target_row_idx: Optional[int] = None
        for r in range(2, ws.max_row + 1):
            if ws.cell(r, name_col_idx).value == current_cell:
                target_row_idx = r
                break
        if not target_row_idx:
            wb.close()
            return None

        cell = ws.cell(target_row_idx, name_col_idx)
        start_color = cell.fill.start_color

        # Normalize color information
        color_info: dict = {}
        try:
            ctype = getattr(start_color, 'type', None)
            if ctype == 'rgb' and start_color.rgb:
                argb = start_color.rgb  # e.g., 'FFFFE699'
                color_info = {
                    'type': 'rgb',
                    'argb': argb,
                    'rgb': argb[-6:] if len(argb) >= 6 else None,
                }
            elif ctype == 'indexed':
                color_info = {
                    'type': 'indexed',
                    'indexed': getattr(start_color, 'indexed', None),
                }
            elif ctype == 'theme':
                color_info = {
                    'type': 'theme',
                    'theme': getattr(start_color, 'theme', None),
                    'tint': getattr(start_color, 'tint', None),
                }
            else:
                # Unknown or no fill
                color_info = None
        except Exception:
            color_info = None

        wb.close()
        return color_info