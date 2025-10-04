# this file fills out pdf forms with data from excel table
import pandas as pd
from data_extractor import create_dataframe_from_excel_table
import pdf_creator


KGdf = create_dataframe_from_excel_table("./tables/Krankmeldungsliste.xlsx")

for row in KGdf.itertuples():
    Days = row.summe_der_tage
    Mit_eAU = row.eau
    Mit_AU = row.au
    if Days <= 3:
        pdf_creator.create_pdf_form_ohne_AU(row)
    else:
        if Mit_eAU:
            pdf_creator.create_pdf_form_mit_AU(row, has_eAU=True)
        elif Mit_AU:
            pdf_creator.create_pdf_form_mit_AU(row, has_eAU=False)
        else:
            print("Need to provide AU!")