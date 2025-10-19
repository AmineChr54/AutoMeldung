# this file fills out pdf forms with data from excel table
import automeldung.config as config
from automeldung.utils.data.meldung import Meldung
from automeldung.utils.data.data_extractor import create_dataframe_from_excel_table
import automeldung.utils.pdf.pdf_creator as pdf_creator

def main_exporter():
    KGdf = create_dataframe_from_excel_table(config.krankmeldungsliste_path)
    # Optional row limit from environment to allow UI control without changing logic elsewhere

    for row in KGdf.head(config.limit_rows).itertuples():
        Days = row.summe_der_tage
        is_selected = row.select
        config.log(f"Processing: {row.nachname} -- Is selected: {is_selected}")
        if is_selected:
            if Days <= 3:
                pdf_creator.create_pdf_form_ohne_AU(row)
            else:
                pdf_creator.create_pdf_form_mit_AU(row)
