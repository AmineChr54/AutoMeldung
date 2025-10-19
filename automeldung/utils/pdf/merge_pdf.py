import os
from typing import Optional
import pikepdf
from automeldung.utils.image.image_converter import image_to_pdf_a4


def merge_pdfs(paths: list[str], output_path: str) -> str:
    """
    Merge provided PDF files in order into output_path using pikepdf, preserving
    annotations and form fields. Combines AcroForm dictionaries and sets
    /NeedAppearances so checkboxes and text fields render properly in viewers.
    Skips missing paths.
    """
    # Filter to existing PDFs
    pdfs = [p for p in paths if p and os.path.exists(p)]
    if not pdfs:
        raise FileNotFoundError("No input PDFs to merge")

    base = pikepdf.Pdf.open(pdfs[0])

    # Append remaining PDFs, copying pages and merging AcroForms
    for extra_path in pdfs[1:]:
        src = pikepdf.Pdf.open(extra_path)

        # Append pages (this handles foreign import internally)
        base.pages.extend(src.pages)

        # Merge AcroForms
        if '/AcroForm' in src.Root:
            if '/AcroForm' not in base.Root:
                base.Root['/AcroForm'] = base.copy_foreign(src.Root['/AcroForm'])
            else:
                base_form = base.Root['/AcroForm']
                src_form = src.Root['/AcroForm']
                # Ensure Fields arrays exist
                base_fields = base_form.get('/Fields', base.make_indirect(pikepdf.Array()))
                src_fields = src_form.get('/Fields', pikepdf.Array())
                # Append fields from src into base, copying foreign objects
                for fld in src_fields:
                    base_fields.append(base.copy_foreign(fld))
                base_form['/Fields'] = base_fields

    # Encourage viewers to generate appearances
    try:
        if '/AcroForm' in base.Root:
            base.Root['/AcroForm']['/NeedAppearances'] = True
    except Exception:
        pass

    base.save(output_path)
    return output_path

def ensure_pdf_for_merge(path: str) -> Optional[str]:
    """Return a PDF path; if input is an image, convert to temp PDF in export folder."""
    if not path:
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return path
    if ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"]:
        base = os.path.splitext(os.path.basename(path))[0]
        out_pdf = os.path.join("./export", f"{base}_as_pdf.pdf")
        return image_to_pdf_a4(path, out_pdf)
    return None