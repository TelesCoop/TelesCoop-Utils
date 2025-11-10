#!/usr/bin/env python3
"""
Script to download pay slips from Google Drive, split them by employee,
and upload individual PDFs back to Google Drive.

Uses the default source folder ID from utils.FOLDER_ID unless overridden.

Usage:
    python process_and_upload.py <dest_folder_id> [employee_filter] [source_folder_id]

Example:
    python process_and_upload.py 1xyz789ghi012
    python process_and_upload.py 1xyz789ghi012 "Madura"
    python process_and_upload.py 1xyz789ghi012 "Madura" 1abc123def456
"""

import sys
import yaml
from utils import (
    authenticate_drive,
    search_and_download,
    process_pdf,
    upload_file,
    FOLDER_ID,
)

# Constants
OUTPUT_DIR = "output"
EMPLOYEE_FILE = "../employees.yaml"


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python process_and_upload.py <dest_folder_id> [employee_filter] [source_folder_id]"
        )
        print("Example: python process_and_upload.py 1xyz789ghi012")
        print('Example: python process_and_upload.py 1xyz789ghi012 "Madura"')
        print(
            'Example: python process_and_upload.py 1xyz789ghi012 "Madura" 1abc123def456'
        )
        print(f"\nDefault source folder ID: {FOLDER_ID}")
        sys.exit(1)

    dest_folder_id = sys.argv[1]
    employee_filter = sys.argv[2] if len(sys.argv) > 2 else None
    source_folder_id = sys.argv[3] if len(sys.argv) > 3 else FOLDER_ID

    print("=" * 70)
    print("    PAY SLIP PROCESSOR - DOWNLOAD, SPLIT & UPLOAD")
    print("=" * 70)
    print(f"Source folder ID: {source_folder_id}")
    print(f"Destination folder ID: {dest_folder_id}")
    if employee_filter:
        print(f"Employee filter: {employee_filter}")
    print("=" * 70)
    print()

    # Authenticate
    print("🔐 Authenticating...")
    service = authenticate_drive(readonly=False)
    print("✓ Authentication successful!")
    print()

    # Step 1: Download PDFs from Google Drive
    print("📥 STEP 1: Downloading PDFs from Google Drive")
    print("-" * 70)
    downloaded_files = search_and_download(
        service,
        source_folder_id,
        name_filter=employee_filter,
        dest_folder="input",
        employee_full_name=None,  # Don't rename during download, will process later
    )
    print(f"✓ Downloaded {len(downloaded_files)} file(s)")
    print()

    if not downloaded_files:
        print("No files to process. Exiting.")
        sys.exit(0)

    # Step 2: Load employee list
    print("📋 STEP 2: Loading employee list")
    print("-" * 70)
    with open(EMPLOYEE_FILE, "r") as f:
        data = yaml.safe_load(f)

    if not data or "employees" not in data:
        print("✗ Invalid employees data format")
        sys.exit(1)

    active_employees = [
        employee
        for employee in data["employees"]
        if employee.get("current_employee", True)
    ]
    print(f"✓ Loaded {len(active_employees)} active employee(s)")
    print()

    # Step 3: Process each downloaded PDF
    print("✂️  STEP 3: Splitting PDFs by employee")
    print("-" * 70)
    all_output_files = []
    for pdf_file in downloaded_files:
        print(f"Processing: {pdf_file}")
        output_files = process_pdf(pdf_file, active_employees, OUTPUT_DIR)
        all_output_files.extend(output_files)
    print(f"✓ Created {len(all_output_files)} individual pay slip(s)")
    print()

    # Step 4: Upload to Google Drive
    print("📤 STEP 4: Uploading individual pay slips to Google Drive")
    print("-" * 70)
    uploaded_count = 0
    for output_file in all_output_files:
        link = upload_file(service, output_file, dest_folder_id)
        if link:
            uploaded_count += 1

    print()
    print("=" * 70)
    print("✅ PROCESS COMPLETE!")
    print("=" * 70)
    print(f"Downloaded: {len(downloaded_files)} file(s)")
    print(f"Created: {len(all_output_files)} pay slip(s)")
    print(f"Uploaded: {uploaded_count} file(s)")
    print("=" * 70)


if __name__ == "__main__":
    main()
