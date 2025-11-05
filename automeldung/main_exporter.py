# this file fills out pdf forms with data from excel table
import automeldung.config as config
from automeldung.utils.data.data_extractor import create_dataframe_from_excel_table
import automeldung.utils.pdf.pdf_creator as pdf_creator
from automeldung.utils.data.meldung import Meldung

def main_exporter():
    KGdf = create_dataframe_from_excel_table(config.krankmeldungsliste_path)
    # Optional row limit from environment to allow UI control without changing logic elsewhere

    for row in KGdf.head(config.limit_rows).itertuples():
        is_selected = row.select
        is_valid, err_msg = Meldung.check_info_validity(row)
        if is_selected and is_valid:
            Days = row.summe_der_tage
            config.log(f"Processing: {row.nachname} -- Is selected: {is_selected}")
            has_au = getattr(row, "au", False) or getattr(row, "eau", False)
            if Days <= 3 and not has_au:
                pdf_creator.create_pdf_form_ohne_AU(row)
            elif has_au:
                pdf_creator.create_pdf_form_mit_AU(row)
            else:
                config.log(f"Problem encountered with row: {row.nachname} -- Days: {Days} -- Has AU: {has_au}")
        elif is_selected and not is_valid:
            config.log(err_msg)