import pandas as pd
from PyPDF2 import PdfReader, PdfWriter

Kontaktdaten = pd.read_excel("./tables/Azubikontaktdaten.xlsx")

def create_pdf_form_ohne_AU(row):
    fullname = f"{row.nachname}, {row.vorname}"
    von_date = row.von
    bis_date = row.bis
    von_date_parsed = pd.to_datetime(row.von, format="%d.%m.%Y")
    bis_date_parsed = pd.to_datetime(row.bis, format="%d.%m.%Y")
    wiederaufnahme_date = (bis_date_parsed + pd.Timedelta(days=1)).strftime("%d.%m.%Y")
    zuletzt_date = (von_date_parsed - pd.Timedelta(days=1)).strftime("%d.%m.%Y")
    todays_date = pd.Timestamp.now().strftime("%d.%m.%Y")
    PNr = Kontaktdaten.loc[
        (Kontaktdaten['Name'] == row.nachname) & (Kontaktdaten['Vorname'] == row.vorname),
        'PNr'
    ].values[0]
    reader = PdfReader("./templates/Vorlage_Krank_Gesundmeldung_Ohne_AU.pdf")
    writer = PdfWriter()

    # Copy over all pages
    writer.append_pages_from_reader(reader)

    # Fill the form fields
    writer.update_page_form_field_values(
        writer.pages[0],
        {
            "Darmstadt, denDarmstadt, den": todays_date,
            "PNr": PNr,
            "Wiederaufnahme": wiederaufnahme_date,
            "DatumBis": bis_date,
            "ZuletztAm": zuletzt_date,
            "DatumAb": von_date,
            "AzubiAuswahl0": fullname,
        },
    )
    # Save filled PDF
    von_date_formatted = pd.to_datetime(row.von, format="%d.%m.%Y").strftime("%Y-%m-%d")
    filename = f"./export/Meldung_{row.nachname}_{von_date_formatted}.pdf"
    with open(filename, "wb") as f:
        writer.write(f)




def create_pdf_form_mit_AU(row, has_eAU):
    if has_eAU:
        pass
    else:
        pass


# # Load the PDF form
# reader = PdfReader("./templates/pdf_template.pdf")
# writer = PdfWriter()

# # Copy over all pages
# writer.append_pages_from_reader(reader)

# # Fill the form fields
# writer.update_page_form_field_values(
#     writer.pages[0],
#     {
#         "NameVorname": "Amine Cheikhrouhou",
#         "Datum": "01.01.2024",
#         "Box": "Yes"
#     },
# )

# # Save filled PDF
# with open("./export/filled_form.pdf", "wb") as f:
#     writer.write(f)


