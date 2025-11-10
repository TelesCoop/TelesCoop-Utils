# Pay Slip Splitter

This directory contains three scripts and a shared utilities module:

1. **process_and_upload.py** - Complete workflow: download, split, and upload (recommended)
2. **download_from_drive.py** - Downloads files from Google Drive filtered by employee name
3. **script.py** - Splits a PDF containing multiple pay slips into individual PDF files
4. **utils.py** - Shared utilities for Google Drive API, PDF processing, and text manipulation

## Requirements

- Python 3.x
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone this repository or download the script files
2. Navigate to the `pay-slip-splitter` directory
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Complete Workflow (Recommended)

The `process_and_upload.py` script provides an end-to-end solution that:

1. Downloads pay slip PDFs from a Google Drive folder
2. Splits them into individual employee pay slips
3. Uploads the individual PDFs back to Google Drive

### Usage

```bash
python process_and_upload.py <dest_folder_id> [employee_filter] [source_folder_id]
```

**Parameters:**

- `dest_folder_id`: Google Drive folder ID where individual pay slips will be uploaded
- `employee_filter` (optional): Filter to download only PDFs matching a specific name
- `source_folder_id` (optional): Google Drive folder ID containing the pay slip PDFs to download (defaults to FOLDER_ID in utils.py)

### Examples

Process all PDFs from the default source folder:

```bash
python process_and_upload.py 1xyz789ghi012
```

Process only PDFs containing "September" or specific employee name:

```bash
python process_and_upload.py 1xyz789ghi012 "September"
```

Use a custom source folder:

```bash
python process_and_upload.py 1xyz789ghi012 "September" 1abc123def456
```

### Workflow Steps

1. **Download**: Recursively searches the source folder for PDF files (optionally filtered by name)
2. **Split**: Processes each PDF to extract individual employee pages based on the employee list
3. **Upload**: Uploads all generated individual pay slips to the destination folder

### Output

- Individual pay slip PDFs are created in the `output` directory locally
- All PDFs are automatically uploaded to the specified Google Drive destination folder
- Files are named with the format: `[YYYY-MM] [Employee Name].pdf`

## Individual Script Usage

### script.py - Local PDF Splitting

1. Place your input PDF file containing all pay slips in the `input` directory
2. Run the script with the path to your input PDF file:

```bash
python script.py input/your-payslip-file.pdf
```

### Example

```bash
python script.py input/VisualiserBPMonth.pdf
```

## Downloading Files from Google Drive

The `download_from_drive.py` script downloads files from a Google Drive folder that contain a specific employee name in their filename.

### Setup

1. Ensure you have `credentials.json` in the parent directory (see Google Drive API setup below)
2. The script will use/create a `token.pickle` file for authentication

### Usage

```bash
python download_from_drive.py <employee_name> [folder_id]
```

**Parameters:**

- `employee_name`: The name to search for in filenames (case-insensitive, accent-insensitive)
- `folder_id` (optional): The ID of the Google Drive folder (defaults to FOLDER_ID in utils.py)

### Example

Download from default folder:

```bash
python download_from_drive.py "Madura"
```

Download from specific folder:

```bash
python download_from_drive.py "Madura" 1abc123def456ghi
```

### Features

- **Recursive folder search**: Searches through all subfolders
- **Name filtering**: Only downloads files containing the employee name in the filename
- **Accent-insensitive matching**: Handles special characters and accents
- **Progress tracking**: Shows download progress and summary
- **Automatic authentication**: Uses OAuth2 with Google Drive API

### Output

Downloaded files are saved to `output/<employee_name>/` directory with automatic renaming:

- **Filename format**: `<YYYY-MM>-<fiche-de-paie|participation>-<LastName> <FirstName>.pdf`
- **Examples**:
  - Pay slip for Antoine Bernier dated July 2023: `2023-07-fiche-de-paie-Bernier Antoine.pdf`
  - Participation document from 2022: `2022-participation-Bernier Antoine.pdf`
- The directory is automatically cleaned before each download to ensure you always have the latest files
- The script looks up the employee's full name from `employees.yaml`

**Date extraction priority:**
1. Parent folder name (e.g., folder "2023-07" → date "2023-07", folder "2022 Participation" → date "2022")
2. Filename (e.g., "BP_2025-09.pdf" → date "2025-09")
3. Supports formats: `YYYY-MM`, `YYYY_MM`, `MM-YYYY`, `YYYYMM`, `YYYY` (year only)

**Document type detection priority:**
1. Parent folder name (e.g., "2022 Participation" → type "participation")
2. Filename (e.g., "Bulletin_paie.pdf" → type "fiche-de-paie")
3. Default: `fiche-de-paie`

Keywords for detection:
- **Participation**: "participation", "particip", "part"
- **Fiche de paie**: "fiche", "bulletin", "paie", "salaire", "BP", "salarié"

Example: `python download_from_drive.py "Bernier"` processing folder "2023-07" containing "2023-07-01-BERNIER-Antoine-00001-Salarié.pdf" → saved as `2023-07-fiche-de-paie-Bernier Antoine.pdf`

### Notes

- Date and document type are extracted from parent folder names with priority over filenames
- The output directory is cleaned (deleted and recreated) before each download
- Google Workspace files (Docs, Sheets, Slides) are skipped as they require special export handling
- The script requires read-only access to Google Drive
- First run will open a browser window for OAuth authentication

## How It Works (script.py)

1. The script downloads the employee list from the TelesCoop GitHub repository
2. It extracts the month and year in YYYY-MM format from the PDF text pattern "Période de paie : du DD/MM/YYYY"
3. It processes the input PDF file, searching for each employee's last name
4. For each employee found, it extracts the relevant pages and creates a separate PDF file
5. The output PDF files are saved in the `output` directory with the format: `[YYYY-MM] [Employee Name].pdf`

## Input File Format

- The input PDF should contain all pay slips in a single file
- Each employee's pay slip should be on separate pages
- The employee's last name should appear in the text of their pay slip pages
- The PDF should contain a date pattern like "Période de paie : du 01/09/2025" to extract the month and year

## Output

- Individual PDF files for each employee are created in the `output` directory
- Each file is named with the extracted date in YYYY-MM format (or the date from the input filename if extraction fails) and the employee's full name

## Notes

- The script creates temporary files in a `temp` directory which are automatically cleaned up
- If the employee list cannot be downloaded, the script will exit with an error
- The script requires internet access to download the employee list from GitHub

## Google Drive API Setup

To use the `download_from_drive.py` script, you need to set up Google Drive API credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API for your project
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials and save as `credentials.json` in the parent directory
6. On first run, the script will open a browser for authentication
7. The token will be saved as `token.pickle` for future use

## Troubleshooting

### script.py

- If you get a "No input file provided" error, make sure to specify the path to your PDF file
- If you get a "Failed to download employee list" error, check your internet connection
- If the script doesn't find any employees in your PDF, verify that the employee names in the PDF match those in the employee list
- If the date is not extracted correctly, ensure the PDF contains the pattern "Période de paie : du DD/MM/YYYY"

### download_from_drive.py

- If authentication fails, ensure `credentials.json` exists in the parent directory
- If no files are downloaded, verify the folder ID and that files contain the employee name
- If you get permission errors, ensure your Google account has access to the folder
- Delete `token.pickle` and re-authenticate if you encounter persistent auth issues

## Configuration

The default Google Drive source folder is configured in `utils.py`:

```python
FOLDER_ID = "1sd9SHPo-gNwpOOuGvWviQjtAHqzwlsfl"  # Default source folder
```

This is the root folder where pay slip PDFs are stored. You can override this by passing a custom folder ID as a command-line argument.

## Code Organization

All scripts share common functionality through the `utils.py` module to avoid code duplication:

### utils.py - Shared Functions

- **Google Drive API**:

  - `authenticate_drive()` - OAuth2 authentication
  - `get_folder_items()` - List files in a folder
  - `download_file()` - Download a file
  - `upload_file()` - Upload a file
  - `search_and_download()` - Recursively search and download
  - `clean_directory()` - Remove old files and prepare directory

- **PDF Processing**:

  - `extract_date_from_pdf()` - Extract date from pay slip
  - `process_pdf()` - Split PDF by employee
  - `format_name()` - Convert employee name format

- **Text Utilities**:
  - `remove_accents()` - Normalize text for comparison
  - `name_in_text()` - Check if name appears in text
  - `name_contains_string()` - Filter filenames
  - `extract_date_from_filename()` - Extract YYYY-MM date from filename
  - `extract_document_type()` - Detect document type (fiche-de-paie or participation)

### Script Structure

Each script is now minimal and focused on its specific workflow:

- **script.py**: 37 lines - Load employees → Process PDF
- **download_from_drive.py**: 118 lines - Find employee name → Clean directory → Download with auto-rename
- **process_and_upload.py**: 131 lines - Download → Process → Upload
- **utils.py**: 473 lines - Shared functions including folder-aware date/type extraction and renaming logic
