# Pay Slip Splitter

This script splits a PDF containing multiple pay slips into individual PDF files, one for each employee.

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

## Usage

1. Place your input PDF file containing all pay slips in the `input` directory
2. Run the script with the path to your input PDF file:

```bash
python script.py input/your-payslip-file.pdf
```

### Example

```bash
python script.py input/VisualiserBPMonth.pdf
```

## How It Works

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

## Troubleshooting

- If you get a "No input file provided" error, make sure to specify the path to your PDF file
- If you get a "Failed to download employee list" error, check your internet connection
- If the script doesn't find any employees in your PDF, verify that the employee names in the PDF match those in the employee list
- If the date is not extracted correctly, ensure the PDF contains the pattern "Période de paie : du DD/MM/YYYY"
