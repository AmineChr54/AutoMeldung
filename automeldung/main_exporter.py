# this file fills out pdf forms with data from excel table
import automeldung.config as config
from automeldung.utils.data.data_extractor import create_dataframe_from_excel_table
import automeldung.utils.pdf.pdf_creator as pdf_creator
from automeldung.utils.data.meldung import Meldung
from datetime import datetime

def main_exporter():
    KGdf = create_dataframe_from_excel_table(config.krankmeldungsliste_path)
    # Optional row limit from environment to allow UI control without changing logic elsewhere

    for row in KGdf.head(config.limit_rows).itertuples():
        is_selected = row.select
        is_valid, err_msg = Meldung.check_info_validity(row)
        
        if is_selected:
            config.log(f"Processing: {row.vorname}, {row.nachname}")
            if is_valid:
                Days = Meldung.get_days_sum(row)
                # Use configured creation date or default to today
                creation_date = config.creation_date if getattr(config, 'creation_date', None) else datetime.now().strftime("%d.%m.%Y")
                
                has_au = getattr(row, "au", False) or getattr(row, "eau", False)
                if Days <= 3 and not has_au:
                    pdf_creator.create_pdf_form_ohne_AU(row, creation_date)
                elif has_au:
                    pdf_creator.create_pdf_form_mit_AU(row, creation_date)
                else:
                    config.log(f"Problem encountered with row: {row.vorname}, {row.nachname} -- Days: {Days} -- Has AU: {has_au}")
            else:
                config.log(err_msg)