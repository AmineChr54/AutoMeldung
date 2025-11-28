import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import automeldung.config as config
from .flatten_pdf import flatten_pdf
from automeldung.utils.image.image_converter import _find_au_file_by_prefix
from .merge_pdf import merge_pdfs, ensure_pdf_for_merge
from automeldung.utils.data.meldung import Meldung

os.makedirs(config.export_path, exist_ok=True)

def _get_date_tag(meldung):
    """Generate a date tag for filenames."""
    return (
        meldung.von_date.strftime("%Y-%m-%d") 
        if pd.notna(meldung.von_date) 
        else pd.Timestamp.now().strftime("%Y-%m-%d")
    )

def _fill_pdf_form(template_path, field_data, output_path):
    """Fills a PDF form with given data and saves it."""
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.update_page_form_field_values(writer.pages[0], field_data)
    
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path

def _cleanup_files(file_list):
    """Removes files if they exist."""
    for p in file_list:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass

def _cleanup_overlays(directory):
    """Removes any leftover overlay files in the directory."""
    try:
        for fname in os.listdir(directory):
            if fname.endswith("_overlay.pdf"):
                path = os.path.join(directory, fname)
                _cleanup_files([path])
    except OSError:
        pass

def _resolve_au_file(meldung):
    """Finds and prepares the AU file (PDF or Image) for merging."""
    if not meldung.has_AU:
        return None
        
    au_candidate = getattr(meldung, "au_file_id", None)
    if not au_candidate:
        return None

    config.log(f"Resolving AU file for: {au_candidate}")
    
    # Direct path provided
    if os.path.exists(au_candidate):
        au_path = au_candidate
    else:
        # Search by prefix in ./au_files (case-insensitive)
        au_path = _find_au_file_by_prefix(config.au_files_path, au_candidate)
    
    if au_path:
        return ensure_pdf_for_merge(au_path)
    return None

def create_pdf_form_ohne_AU(row, creation_date):
    meldung = Meldung(row)
    date_tag = _get_date_tag(meldung)
    
    # Define filenames
    interactive_filename = os.path.join(config.export_path, f"Meldung_{meldung.nachname}_{date_tag}_interactive.pdf")
    final_filename = os.path.join(config.export_path, f"Meldung_{meldung.nachname}_{date_tag}.pdf")

    # Prepare data
    field_data = {
        "nachname_vorname": meldung.fullname,
        "pnr": meldung.PNr,
        "von": meldung.von_date_parsed,
        "bis": meldung.bis_date_parsed,
        "wiederaufnahmedatum": meldung.wiederaufnahme_date,
        "zuletzt": meldung.zuletzt_date,
        "datum": creation_date,
    }

    # Create interactive PDF
    _fill_pdf_form(config.vorlage_krankmeldung_ohne_au_path, field_data, interactive_filename)

    # Flatten to final output
    flatten_pdf(interactive_filename, final_filename)
    config.log(f"PDF saved to: {final_filename}")

    # Cleanup
    _cleanup_files([interactive_filename])
    _cleanup_overlays(config.export_path)

    return final_filename

def create_pdf_form_mit_AU(row, creation_date):
    meldung = Meldung(row)
    date_tag = _get_date_tag(meldung)

    # Check if this is a Zwischenmeldung (Intermediate Report)
    # Condition: bis_date is strictly in the future relative to today
    is_zwischenmeldung = False
    if pd.notna(meldung.bis_date):
        # Normalize to midnight for accurate comparison
        today_midnight = pd.Timestamp.now().normalize()
        bis_midnight = meldung.bis_date.normalize()
        if bis_midnight > today_midnight:
            is_zwischenmeldung = True

    # 1) Create Krankmeldung (MitAU) interactive PDF
    krank_data = {
        "nachname_vorname": meldung.fullname,
        "pnr": meldung.PNr,
        "von_ohne": meldung.von_ohne_parsed,
        "bis_ohne": meldung.bis_ohne_parsed,
        "von_mit": meldung.au_von_parsed,
        "bis_mit": meldung.au_bis_parsed,
        "eAU_checkbox": "/Yes" if meldung.has_eAU else "/Off",
        "AU_checkbox": "/Yes" if meldung.has_AU else "/Off",
        "zuletzt": meldung.zuletzt_date,
        "datum": creation_date,
    }
    
    prefix = "Zwischenmeldung" if is_zwischenmeldung else "Krankmeldung"
    krank_interactive = os.path.join(config.export_path, f"{prefix}_{meldung.nachname}_{date_tag}_interactive.pdf")
    _fill_pdf_form(config.vorlage_krankmeldung_mit_au_path, krank_data, krank_interactive)

    # 2) Resolve optional AU file
    au_pdf = _resolve_au_file(meldung)

    # 3) Create Gesundmeldung interactive PDF (ONLY if NOT Zwischenmeldung)
    gesund_interactive = None
    if not is_zwischenmeldung:
        gesund_data = {
            "nachname_vorname": meldung.fullname,
            "pnr": meldung.PNr,
            "von": meldung.von_date_parsed,
            "bis": meldung.bis_date_parsed,
            "wiederaufnahmedatum": meldung.wiederaufnahme_date,
            "datum": creation_date,
        }
        gesund_interactive = os.path.join(config.export_path, f"Gesundmeldung_{meldung.nachname}_{date_tag}_interactive.pdf")
        _fill_pdf_form(config.vorlage_gesundmeldung_path, gesund_data, gesund_interactive)

    # 4) Merge: Krank + optional AU + [Gesund (if applicable)]
    final_prefix = "Zwischenmeldung" if is_zwischenmeldung else "Meldung"
    merged_interactive = os.path.join(config.export_path, f"{final_prefix}_{meldung.nachname}_{date_tag}_merged_interactive.pdf")
    
    merge_list = [krank_interactive]
    if au_pdf:
        merge_list.append(au_pdf)
    if gesund_interactive:
        merge_list.append(gesund_interactive)
    
    merge_pdfs(merge_list, merged_interactive)

    # 5) Flatten merged to final output
    final_filename = os.path.join(config.export_path, f"{final_prefix}_{meldung.nachname}_{date_tag}.pdf")
    flatten_pdf(merged_interactive, final_filename)
    config.log(f"PDF saved to: {final_filename}")

    # 6) Cleanup
    cleanup_list = [krank_interactive, merged_interactive]
    if gesund_interactive:
        cleanup_list.append(gesund_interactive)
    if au_pdf and au_pdf.endswith("_as_pdf.pdf"):
        cleanup_list.append(au_pdf)
    
    _cleanup_files(cleanup_list)
    _cleanup_overlays(config.export_path)

    return final_filename

