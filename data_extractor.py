# this file extracts data from excel table

import pandas as pd

def create_dataframe_from_excel_table(excel_file):
    df = pd.read_excel(excel_file)
    # Clean column names: remove spaces, convert to lowercase, remove special characters
    df.columns = (df.columns
                  .str.strip()           # Remove leading/trailing spaces
                  .str.lower()           # Convert to lowercase
                  .str.replace(' ', '_') # Replace spaces with underscores
                  .str.replace('[^a-zA-Z0-9_]', '', regex=True)  # Remove special characters
                  )
    return df


create_dataframe_from_excel_table("./tables/Krankmeldungsliste.xlsx")
Index = ['nachname', 'vorname', 'von', 'bis', 'summe_der_tage',
       'summe_der_tage_ohne_we', 'von_wochentag', 'bis_wochentag', 'au', 'eau',
       'inkorrektgemeldet', 'bemerkung', 'au_file_id', 'zeitraumohne_au',
       'zeitraummit_au']