# AutoMeldung

> Automates the generation of German sick leave (Krankmeldung) and return-to-work PDFs from Excel data. Features AU attachment merging, PDF flattening, and a modern Flet GUI.

**Automeldung** is a desktop application designed to streamline the process of creating *Krankmeldungen* (sick notes) and *Gesundmeldungen* (return-to-work notes). It reads data from an Excel sheet, fills out PDF forms, merges optional AU (*Arbeitsunfähigkeitsbescheinigung*) attachments, and flattens the final documents for distribution.

## Features
- **Excel Integration**: Reads data from a *Krankmeldungsliste* and optional *Kontaktdaten* file.
- **Smart Form Generation**:
- Automatically selects between *Krankmeldung Ohne AU* ( 3 days) and *Krankmeldung Mit AU* (> 3 days).
- Generates corresponding *Gesundmeldung*.
- **PDF Merging & Flattening**: Combines the sick note, optional AU attachment, and return note into a single, flattened PDF per employee.
- **Image Conversion**: Automatically converts AU attachments (JPG, PNG, WebP) to A4 PDF format.
- **Modern GUI**: Built with [Flet](https://flet.dev), featuring file pickers, collapsible sections, and live status logging.
- **Persistent Settings**: Remembers your file paths and configurations between sessions.

## Installation

### Download Executable
You can download the latest standalone executable for Windows from the [Releases page](https://github.com/AmineChr54/pdf-automation/releases).

### Run from Source
1. **Clone the repository:**
   `bash
   git clone https://github.com/AmineChr54/pdf-automation.git
   cd pdf-automation
   ` 

2. **Set up a virtual environment:**
   `powershell
   python -m venv .venv
   .venv\Scripts\Activate
   ` 

3. **Install dependencies:**
   `bash
   pip install -r requirements.txt
   ` 

4. **Run the application:**
   `bash
   python gui/app.py
   ` 

## Usage

1. **Launch the App**: Run the executable or the python script.
2. **Configure Inputs**:
   - Select your **Krankmeldungen** Excel file and Sheet Name.
   - (Optional) Select your **Kontaktdaten** Excel file.
   - Choose your PDF templates for *Krankmeldung* (with/without AU) and *Gesundmeldung*.
   - Select the folder containing your **AU Files** (images or PDFs).
3. **Set Export Options**:
   - Choose an output folder.
   - Set a row limit (useful for testing).
4. **Run**: Click "Start Export" and watch the status log for progress.

## Project Structure
- `gui/app.py`: Main entry point for the Flet GUI.
- `automeldung/main_exporter.py`: Core logic for processing rows and generating PDFs.
- `automeldung/config.py`: Configuration management.
- `automeldung/utils/`: Helper modules for data extraction, PDF manipulation, and image conversion.
- `templates/`: Directory for PDF form templates.

## Building the Executable
To build a standalone .exe file using PyInstaller (via Flet):

`powershell
flet pack gui/app.py --name Automeldung --add-data "templates;templates" --path .
` 
The output will be located in the dist/ folder.

## Troubleshooting
- **No output PDFs**: Verify that your template paths are correct and the export folder is writable.
- **Missing Excel columns**: Ensure your Excel headers match the expected names (e.g., Nachname, Vorname, Von, Bis).
- **AU not found**: Ensure AU filenames start with the corresponding `au_file_id` from your Excel sheet.
