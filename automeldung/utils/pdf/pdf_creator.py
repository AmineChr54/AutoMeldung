import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import automeldung.config as config
from .flatten_pdf import flatten_pdf
from automeldung.utils.image.image_converter import _find_au_file_by_prefix
from .merge_pdf import merge_pdfs, ensure_pdf_for_merge
from automeldung.utils.data.meldung import Meldung

os.makedirs(config.export_path, exist_ok=True)

def create_pdf_form_ohne_AU(row):
    meldung = Meldung(row)

    reader = PdfReader(config.vorlage_krankmeldung_ohne_au_path)
    writer = PdfWriter()

    # Copy over all pages
    writer.append_pages_from_reader(reader)

    # Fill the form fields
    writer.update_page_form_field_values(
        writer.pages[0],
        {
            "nachname_vorname": meldung.fullname,
            "pnr": meldung.PNr,
            "von": meldung.von_date_parsed,
            "bis": meldung.bis_date_parsed,
            "wiederaufnahmedatum": meldung.wiederaufnahme_date,
            "zuletzt": meldung.zuletzt_date,
            "datum": meldung.todays_date,
        },
    )
    # Save filled PDF (interactive), then flatten to final output
    # Build a safe date tag for filenames; fallback to today's date if missing
    von_date_formatted = (
        meldung.von_date.strftime("%Y-%m-%d") if pd.notna(meldung.von_date) else pd.Timestamp.now().strftime("%Y-%m-%d")
    )
    interactive_filename = f"{config.export_path}/Meldung_{meldung.nachname}_{von_date_formatted}_interactive.pdf"
    final_filename = f"{config.export_path}/Meldung_{meldung.nachname}_{von_date_formatted}.pdf"
    with open(interactive_filename, "wb") as f:
        writer.write(f)
    # Flatten and cleanup temp
    flatten_pdf(interactive_filename, final_filename)
    config.log(f"Flattened PDF saved to: {final_filename}")
    # Cleanup: remove interactive file
    try:
        if os.path.exists(interactive_filename):
            os.remove(interactive_filename)
    except OSError:
        pass

    # Remove any leftover overlay files (ending with _overlay.pdf) in export dir
    try:
        for fname in os.listdir(config.export_path):
            if fname.endswith("_overlay.pdf"):
                path = os.path.join(config.export_path, fname)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
    except OSError:
        pass

    return final_filename

def create_pdf_form_mit_AU(row):
    # 1) Initialize meldung data
    meldung = Meldung(row)

    # 2) Create Krankmeldung (MitAU) interactive PDF
    krank_reader = PdfReader(config.vorlage_krankmeldung_mit_au_path)
    krank_writer = PdfWriter()
    krank_writer.append_pages_from_reader(krank_reader)
    krank_writer.update_page_form_field_values(
        krank_writer.pages[0],
        {
            "nachname_vorname": meldung.fullname,
            "pnr": meldung.PNr,
            "von_ohne": meldung.von_ohne_parsed,
            "bis_ohne": meldung.bis_ohne_parsed,
            "von_mit": meldung.au_von_parsed,
            "bis_mit": meldung.au_bis_parsed,
            "eAU_checkbox": "/Yes" if meldung.has_eAU else "/Off",
            "AU_checkbox": "/Yes" if meldung.has_AU else "/Off",
            "zuletzt": meldung.zuletzt_date,
            "datum": meldung.todays_date,
        },
    )
    date_tag = (
        meldung.von_date.strftime("%Y-%m-%d") if pd.notna(meldung.von_date) else pd.Timestamp.now().strftime("%Y-%m-%d")
    )
    krank_interactive = f"{config.export_path}/Krankmeldung_{meldung.nachname}_{date_tag}_interactive.pdf"
    with open(krank_interactive, "wb") as f:
        krank_writer.write(f)

    # 3) Resolve optional AU file (image or pdf) when no eAU
    au_pdf = None
    if meldung.has_AU:
        au_candidate = getattr(meldung, "au_file_id", None)
        if au_candidate:
            config.log(f"Resolving AU file for: {au_candidate}")
            # Direct path provided
            if os.path.exists(au_candidate):
                au_path = au_candidate
            else:
                # Search by prefix in ./au_files (case-insensitive)
                au_path = _find_au_file_by_prefix(config.au_files_path, au_candidate)
            if au_path:
                au_pdf = ensure_pdf_for_merge(au_path)

    # 4) Create Gesundmeldung interactive PDF
    gesund_reader = PdfReader(config.vorlage_gesundmeldung_path)
    gesund_writer = PdfWriter()
    gesund_writer.append_pages_from_reader(gesund_reader)
    gesund_writer.update_page_form_field_values(
        gesund_writer.pages[0],
        {
            "nachname_vorname": meldung.fullname,
            "pnr": meldung.PNr,
            "von": meldung.von_date_parsed,
            "bis": meldung.bis_date_parsed,
            "wiederaufnahmedatum": meldung.wiederaufnahme_date,
            "datum": meldung.todays_date,
        },
    )
    gesund_interactive = f"{config.export_path}/Gesundmeldung_{meldung.nachname}_{date_tag}_interactive.pdf"
    with open(gesund_interactive, "wb") as f:
        gesund_writer.write(f)

    # 5) Merge: Krank + optional AU + Gesund -> merged_interactive
    merged_interactive = f"{config.export_path}/Meldung_{meldung.nachname}_{date_tag}_merged_interactive.pdf"
    merge_list = [krank_interactive]
    if au_pdf:
        merge_list.append(au_pdf)
    merge_list.append(gesund_interactive)
    merge_pdfs(merge_list, merged_interactive)

    # 6) Flatten merged to final output, then cleanup temps
    final_filename = f"{config.export_path}/Meldung_{meldung.nachname}_{date_tag}.pdf"
    flatten_pdf(merged_interactive, final_filename)
    config.log(f"Flattened PDF saved to: {final_filename}")

    # Try to remove temp files
    for p in [krank_interactive, gesund_interactive, merged_interactive]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
    # Remove converted AU temp pdf if we created one (heuristic: name endswith _as_pdf.pdf)
    try:
        if au_pdf and au_pdf.endswith("_as_pdf.pdf") and os.path.exists(au_pdf):
            os.remove(au_pdf)
    except OSError:
        pass
    # Remove any leftover overlay files (ending with _overlay.pdf) in export dir
    try:
        export_dir = config.export_path
        for fname in os.listdir(export_dir):
            if fname.endswith("_overlay.pdf"):
                path = os.path.join(export_dir, fname)
                try:
                    os.remove(path)
                except OSError:
                    pass
    except OSError:
        pass

    return final_filename

