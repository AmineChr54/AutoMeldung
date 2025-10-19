import sys
import os
import pikepdf
from pikepdf import Name, Array
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


def flatten_pdf(input_path: str, output_path: str) -> None:
    """
    Flatten a PDF, but first stamp field values into page content so values remain visible.
    - Draws text for text fields (FT=/Tx) at their widget rect positions.
    - Draws an "X" for checked checkboxes (FT=/Btn with /V=/Yes).
    - Then removes widgets and /AcroForm like flatten_pdf.

    Assumes A4 page size for the overlay (your project uses A4 templates).
    """
    base = pikepdf.Pdf.open(input_path)

    # 1) Build an overlay PDF with the same number of pages, drawing field values
    overlay_path = _temp_overlay_path(input_path)
    c = canvas.Canvas(overlay_path, pagesize=A4)
    for page in base.pages:
        annots = page.get(Name('/Annots'), [])
        # Draw field values
        c.setFillColor(colors.black)
        for annot in annots:
            subtype = annot.get(Name('/Subtype'))
            if subtype != Name('/Widget'):
                continue
            ft = annot.get(Name('/FT'))  # Field type
            rect = annot.get(Name('/Rect'))
            if rect is None or len(rect) != 4:
                continue
            x0, y0, x1, y1 = [float(v) for v in rect]
            # Small padding inside the rect
            tx = x0 + 2
            ty = y0 + 3
            width = x1 - x0
            height = y1 - y0

            if ft == Name('/Tx'):
                # Text value can be on the widget or the parent field
                val = annot.get(Name('/V'))
                if val is None and annot.get(Name('/Parent')) is not None:
                    try:
                        parent = annot[Name('/Parent')].get_object()
                        val = parent.get(Name('/V'))
                    except Exception:
                        val = None
                if val is None:
                    continue
                text = str(val)
                # Basic single-line draw; for multiline handling, splitlines and reduce font
                c.setFont("Helvetica", 10)
                c.drawString(tx, ty + max(0, (height - 10) * 0.35), text)
            if ft == Name('/Tx'):
                # Text value can be on the widget or the parent field
                val = annot.get(Name('/V'))
                if val is None and annot.get(Name('/Parent')) is not None:
                    try:
                        parent = annot[Name('/Parent')].get_object()
                        val = parent.get(Name('/V'))
                    except Exception:
                        val = None
                if val is None:
                    continue
                text = str(val)
                # Basic single-line draw; for multiline handling, splitlines and reduce font
                c.setFont("Helvetica", 10)
                c.drawString(tx, ty + max(0, (height - 10) * 0.35), text)
            elif ft == Name('/Btn'):
                # Determine the actual on-state from appearances; default to /Yes
                on_name = Name('/Yes')
                ap = annot.get(Name('/AP'))
                try:
                    if ap and ap.get(Name('/N')):
                        n_dict = ap[Name('/N')].get_object()
                        for k in n_dict.keys():
                            if k != Name('/Off'):
                                on_name = k
                                break
                except Exception:
                    pass
                # Value may be on the widget or the parent; also consider /AS (appearance state)
                val = annot.get(Name('/V'))
                if val is None and annot.get(Name('/Parent')) is not None:
                    try:
                        parent = annot[Name('/Parent')].get_object()
                        val = parent.get(Name('/V'))
                    except Exception:
                        val = None
                as_val = annot.get(Name('/AS'))
                is_checked = (val == on_name) or (as_val == on_name)
                if is_checked:
                    # Draw a simple X in the box
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(1)
                    c.line(x0 + 2, y0 + 2, x1 - 2, y1 - 2)
                    c.line(x0 + 2, y1 - 2, x1 - 2, y0 + 2)
                    try:
                        parent = annot[Name('/Parent')].get_object()
                        val = parent.get(Name('/V'))
                    except Exception:
                        val = None
                as_val = annot.get(Name('/AS'))
                is_checked = (val == on_name) or (as_val == on_name)
                if is_checked:
                    # Draw a simple X in the box
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(1)
                    c.line(x0 + 2, y0 + 2, x1 - 2, y1 - 2)
                    c.line(x0 + 2, y1 - 2, x1 - 2, y0 + 2)
        c.showPage()
    c.save()

    # 2) Merge overlay into base
    overlay = pikepdf.Pdf.open(overlay_path)
    for i, page in enumerate(base.pages):
        page.Contents = base.make_stream(
            page.Contents.read_bytes() + overlay.pages[i].Contents.read_bytes()
        )

    # 3) Remove widgets and AcroForm
    for page in base.pages:
        annots = page.get(Name('/Annots'), None)
        if annots is None:
            continue
        kept = Array()
        for annot in annots:
            if annot.get(Name('/Subtype')) == Name('/Widget'):
                continue
            kept.append(annot)
        if len(kept) > 0:
            page[Name('/Annots')] = kept
        else:
            try:
                del page[Name('/Annots')]
            except Exception:
                page[Name('/Annots')] = Array()

    if Name('/AcroForm') in base.Root:
        try:
            del base.Root[Name('/AcroForm')]
        except Exception:
            base.Root[Name('/AcroForm')] = pikepdf.Dictionary()

    base.save(output_path)


def _temp_overlay_path(input_path: str) -> str:
    base, _ = os.path.splitext(input_path)
    return f"{base}__overlay.pdf"


def _main(argv: list[str]) -> int:
    if len(argv) not in (2, 3, 4):
        print("Usage: python flatten_pdf.py <input.pdf> [output.pdf] [--preserve-values]")
        return 2
    input_path = argv[1]
    if not os.path.exists(input_path):
        print(f"Input not found: {input_path}")
        return 2
    output_path = argv[2] if len(argv) >= 3 and not argv[-1].startswith("--") else _default_out(input_path)
    preserve = argv[-1] == "--preserve-values"
    if preserve:
        flatten_pdf(input_path, output_path)
    else:
        flatten_pdf(input_path, output_path)
    print(f"✅ Flattened PDF written to: {output_path}")
    return 0


def _default_out(path: str) -> str:
    base, ext = os.path.splitext(path)
    return f"{base}_flat{ext or '.pdf'}"


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
