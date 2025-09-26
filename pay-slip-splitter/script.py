#!/usr/bin/env python3
import os
import re
import sys
import requests
import yaml
import shutil
from PyPDF2 import PdfReader, PdfWriter
from tqdm import tqdm

# Global constants for directories
OUTPUT_DIR = "output"
TEMP_DIR = "temp"
EMPLOYEE_FILE = f"{TEMP_DIR}/employees.yaml"
EMPLOYEE_FILE_URL = "https://raw.githubusercontent.com/TelesCoop/company-settings/main/employees.yaml"
DATE_REGEX = r"Période\s*de\s*paie\s*:\s*du\s*(\d{2}/\d{2}/\d{4})"

def initiate_dir():
    # Create directories if they don't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

def download_employees():
    """Download employees.yaml from GitHub"""
    print("Downloading employee list from GitHub...")
    try:
        response = requests.get(EMPLOYEE_FILE_URL)
        response.raise_for_status()

        with open(EMPLOYEE_FILE, 'w') as f:
            f.write(response.text)

        print(f"Successfully downloaded employee list to {EMPLOYEE_FILE}")
        print("\nEmployee list content:")
        print("----------------------")
        with open(EMPLOYEE_FILE, 'r') as f:
            print(f.read())

        return True
    except Exception as e:
        print(f"Failed to download employee list: {e}")
        return False

def extract_date_from_pdf(pdf_path):
    """Extract month and year in YYYY-MM format from PDF text pattern"""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        # Check first few pages for the date pattern
        for page_num in range(min(5, len(pdf_reader.pages))):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()

            # Look for pattern like "Période de paie : du 01/09/2025 au 30/09/2025"
            match = re.search(DATE_REGEX, page_text)
            if match:
                date_str = match.group(1)
                _, month, year = date_str.split('/')
                return f"{year}-{month}"  # Return in YYYY-MM format

    return None

def format_name(employee_name):
    """Convert employee name from 'last.first' to 'Last First' format"""
    name_parts = employee_name.split('.')
    if len(name_parts) != 2:
        return None

    first_name = name_parts[1].capitalize()
    last_name = name_parts[0].capitalize()
    return f"{last_name} {first_name}"

def process_pdf(input_file, employees):
    """Process the PDF file to extract pages for each employee"""
    # Extract date from PDF content in YYYY-MM format
    date = extract_date_from_pdf(input_file) or ""

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read the PDF
    with open(input_file, 'rb') as file:
        pdf_reader = PdfReader(file)
        total_pages = len(pdf_reader.pages)

        # Create a dictionary to map pages to employees
        page_to_employees = {}
        for page_num in tqdm(range(total_pages), desc="Scanning pages", unit="page"):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()

            # Check for each employee's last name on this page
            for employee in employees:
                name = employee['name']
                full_name = format_name(name)

                if not full_name:
                    continue

                last_name = full_name.split(' ')[0]
                if last_name.lower() in page_text.lower():
                    if page_num not in page_to_employees:
                        page_to_employees[page_num] = []
                    page_to_employees[page_num].append((full_name, employee))

        # Create PDFs for each employee
        employee_pdfs = {}
        for page_num, employee_list in page_to_employees.items():
            for full_name, employee in employee_list:
                if full_name not in employee_pdfs:
                    employee_pdfs[full_name] = PdfWriter()
                employee_pdfs[full_name].add_page(pdf_reader.pages[page_num])

        # Save the PDFs
        for full_name, pdf_writer in employee_pdfs.items():
            output_filename = f"{OUTPUT_DIR}/{date} {full_name}.pdf"
            with open(output_filename, 'wb') as output_file:
                pdf_writer.write(output_file)
            print(f"Created PDF for {full_name}: {output_filename}")

def cleanup_temp_dir():
    """Clean up temporary directory and its contents"""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

def main():
    # Create temp directory if it doesn't exist
    initiate_dir()

    try:
        if len(sys.argv) < 2:
            print("Please provide file path")
            sys.exit(1)

        input_file = sys.argv[1]

        if not download_employees():
            sys.exit(1)

        # Load employees data
        with open(EMPLOYEE_FILE, 'r') as f:
            data = yaml.safe_load(f)

        if not data or 'employees' not in data:
            print("Invalid employees data format")
            sys.exit(1)

        # Process the PDF
        process_pdf(input_file, data['employees'])
    finally:
        # Ensure cleanup happens even if an error occurs
        cleanup_temp_dir()

if __name__ == "__main__":
    main()
