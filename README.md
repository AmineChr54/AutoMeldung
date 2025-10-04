# PDF Automation - Automeldung

A Python-based automation tool for generating sick leave notifications (Krankmeldungen) by extracting data from Excel files and filling PDF forms automatically.

## 🚀 Features

- **Excel Data Extraction**: Read and process sick leave data from Excel spreadsheets
- **PDF Form Filling**: Automatically fill PDF notification forms with extracted data
- **Column Name Cleaning**: Automatically clean Excel column names for easier programming
- **Date Processing**: Smart date parsing and calculation for leave periods
- **Batch Processing**: Process multiple entries at once
- **Flexible Templates**: Support for different types of sick leave forms

## 📋 Requirements

- Python 3.7+
- Required packages listed in `requirements.txt`

## 🛠️ Installation

1. Clone this repository:
```bash
git clone https://github.com/AmineChr54/pdf-automation.git
cd pdf-automation
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📁 Project Structure

```
├── data_extractor.py          # Excel data extraction and processing
├── pdf_creator.py             # PDF form filling and generation
├── main_exporter.py           # Main execution script
├── requirements.txt           # Python dependencies
├── templates/                 # PDF templates and field mappings
│   ├── pdf_template.pdf
│   └── fields.txt
└── export/                    # Generated PDF outputs (gitignored)
```

## 🔧 Usage

### Basic Usage

1. **Prepare your data**: Place your Excel files with sick leave data in the `tables/` directory
2. **Configure templates**: Ensure PDF templates are in the `templates/` directory
3. **Run the automation**:

```python
from data_extractor import create_dataframe_from_excel_table
from pdf_creator import create_pdf_form_ohne_AU

# Extract data from Excel
df = create_dataframe_from_excel_table("./tables/Krankmeldungsliste.xlsx")

# Process each row to generate PDFs
for index, row in df.iterrows():
    create_pdf_form_ohne_AU(row)
```

### Data Extraction

The `data_extractor.py` module automatically:
- Cleans column names (removes spaces, converts to lowercase)
- Handles special characters in column headers
- Returns a processed pandas DataFrame

### PDF Generation

The `pdf_creator.py` module:
- Reads Excel data for contact information and sick leave periods
- Calculates relevant dates (return date, last working day, etc.)
- Fills PDF form fields automatically
- Generates uniquely named output files

## 📊 Expected Data Format

Your Excel files should contain columns for:
- `nachname` (Last name)
- `vorname` (First name)
- `von` (From date - format: DD.MM.YYYY)
- `bis` (To date - format: DD.MM.YYYY)

Contact data should include:
- `Name` (Last name)
- `Vorname` (First name)
- `PNr` (Personnel number)

## 🎯 Features in Development

- [ ] Support for electronic sick leave certificates (eAU)
- [ ] Enhanced error handling and validation
- [ ] GUI interface for non-technical users
- [ ] Email integration for automatic sending
- [ ] Bulk processing with progress tracking

## ⚠️ Important Notes

- This tool is designed for German sick leave processes
- Ensure compliance with your organization's data protection policies
- Test thoroughly with sample data before production use
- Keep sensitive data files local (they are excluded from version control)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Privacy & Security

This project handles potentially sensitive employee data. Please ensure:
- Data files are kept secure and not shared inappropriately
- Compliance with GDPR and local data protection laws
- Regular security updates of dependencies
- Proper access controls on generated files

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Note**: This tool is designed for internal organizational use. Ensure proper authorization before processing employee data.