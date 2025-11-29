import threading
import importlib
import os
import automeldung.config as config
from gui.utils.settings import save_settings

def setup_runner(page, settings, input_refs, export_refs, status_refs):
    append_log = status_refs["append_log"]
    prog = status_refs["prog"]
    
    def on_run_clicked(e):
        # Extract values
        krankmeldungen_path = input_refs["krankmeldungen_path"]
        krankmeldungen_sheet_name = input_refs["krankmeldungen_sheet_name"]
        krank_ohne_path = input_refs["krank_ohne_path"]
        krank_mit_path = input_refs["krank_mit_path"]
        gesund_path = input_refs["gesund_path"]
        kontaktdaten_path = input_refs["kontaktdaten_path"]
        kontaktdaten_sheet_name = input_refs["kontaktdaten_sheet_name"]
        au_folder = input_refs["au_folder"]
        
        export_folder = export_refs["export_folder"]
        limit_rows = export_refs["limit_rows"]
        creation_date_input = export_refs["creation_date_input"]

        # Apply UI paths to config temporarily (only if provided)
        if krankmeldungen_path.value:
            config.krankmeldungsliste_path = krankmeldungen_path.value
        if krankmeldungen_sheet_name.value.strip():
            config.krankmeldungsliste_sheet_name = krankmeldungen_sheet_name.value.strip()
        if export_folder.value:
            config.export_path = export_folder.value
        if krank_ohne_path.value:
            config.vorlage_krankmeldung_ohne_au_path = krank_ohne_path.value
        if krank_mit_path.value:
            config.vorlage_krankmeldung_mit_au_path = krank_mit_path.value
        if gesund_path.value:
            config.vorlage_gesundmeldung_path = gesund_path.value
        if au_folder.value:
            config.au_files_path = au_folder.value
        if kontaktdaten_path.value:
            config.kontaktdaten_path = kontaktdaten_path.value
        if kontaktdaten_sheet_name.value.strip():
            config.kontaktdaten_sheet_name = kontaktdaten_sheet_name.value.strip()
        
        # Set creation date if provided
        if creation_date_input.value.strip():
            config.creation_date = creation_date_input.value.strip()
        else:
            config.creation_date = None

        # Limit rows
        try:
            limit = int(limit_rows.value.strip()) if limit_rows.value.strip() else 20
        except ValueError:
            limit = 20
        os.environ['AUTOMELDUNG_LIMIT'] = str(limit)

        # Persist current values
        settings.update({
            "krankmeldungen_path": krankmeldungen_path.value,
            "krankmeldungen_sheet_name": krankmeldungen_sheet_name.value,
            "krank_ohne_path": krank_ohne_path.value,
            "krank_mit_path": krank_mit_path.value,
            "gesund_path": gesund_path.value,
            "kontaktdaten_path": kontaktdaten_path.value,
            "kontaktdaten_sheet_name": kontaktdaten_sheet_name.value,
            "au_folder": au_folder.value,
            "export_folder": export_folder.value,
            "limit_rows": limit,
            "creation_date": creation_date_input.value,
        })
        save_settings(settings)

        # Show progress UI
        prog.visible = True
        prog.update()
        append_log("Export started...")

        def worker():
            try:
                # (Re-)set logger so backend logs appear in the UI
                try:
                    config.set_logger(lambda m: append_log(str(m)))
                except Exception:
                    pass
                # Re-import exporter to ensure it sees updated config
                importlib.reload(config)
                try:
                    config.set_logger(lambda m: append_log(str(m)))
                except Exception:
                    pass
                # Run existing exporter (iterates over head(20) inside)
                from automeldung.main_exporter import main_exporter as run_exporter
                run_exporter()
                append_log("Export finished.")
            except Exception as ex:
                append_log(f"Error: {ex}")
            finally:
                prog.visible = False
                page.update()

        threading.Thread(target=worker, daemon=True).start()

    def on_cancel_clicked(e):
        append_log("Operation cancelled.")
        prog.visible = False
        prog.update()

    # Attach handlers
    status_refs["run_btn"].on_click = on_run_clicked
    status_refs["cancel_btn"].on_click = on_cancel_clicked
