"""
Common utilities for pay slip processing scripts.
Shared functions for Google Drive API, PDF processing, and text manipulation.
"""

import os
import re
import pickle
import unicodedata
import io
from PyPDF2 import PdfReader, PdfWriter
from tqdm import tqdm
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

FOLDER_ID = "1sd9SHPo-gNwpOOuGvWviQjtAHqzwlsfl"

# Constants
DATE_REGEX = r"Période\s*de\s*paie\s*:\s*du\s*(\d{2}/\d{2}/\d{4})"


def remove_accents(input_str):
    """Remove accents from characters and normalize to lowercase"""
    if not input_str:
        return ""
    # Normalize to NFD form which separates base characters from diacritics
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    # Remove diacritics and convert to lowercase
    return "".join([c.lower() for c in nfkd_form if not unicodedata.combining(c)])


def authenticate_drive(
    token_file="../token.pickle", creds_file="../credentials.json", readonly=False
):
    """
    Authenticate user and return Google Drive service

    Args:
        token_file: Path to token pickle file
        creds_file: Path to credentials JSON file
        readonly: If True, request read-only scope

    Returns:
        Google Drive API service object
    """
    scopes = (
        ["https://www.googleapis.com/auth/drive.readonly"]
        if readonly
        else ["https://www.googleapis.com/auth/drive"]
    )
    creds = None

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def get_folder_items(service, folder_id):
    """Get all files and folders in a Google Drive folder"""
    query = f"'{folder_id}' in parents and trashed=false"
    results = (
        service.files()
        .list(q=query, fields="files(id, name, mimeType)", pageSize=1000)
        .execute()
    )
    return results.get("files", [])


def name_contains_string(filename, search_string):
    """Check if filename contains search string (case-insensitive, accent-insensitive)"""
    if not search_string:
        return True
    filename_clean = remove_accents(filename)
    search_clean = remove_accents(search_string)
    return search_clean in filename_clean


def extract_date_from_filename(filename):
    """
    Extract date in YYYY-MM format from filename
    Looks for patterns like YYYY-MM, YYYY_MM, MM-YYYY, YYYY (year only), etc.

    Returns:
        str: Date in YYYY-MM format, or YYYY if only year found, or None if not found
    """
    import re

    # Try YYYY-MM or YYYY_MM pattern
    match = re.search(r'(\d{4})[-_](\d{2})', filename)
    if match:
        year, month = match.groups()
        if 1 <= int(month) <= 12:
            return f"{year}-{month}"

    # Try MM-YYYY or MM_YYYY pattern
    match = re.search(r'(\d{2})[-_](\d{4})', filename)
    if match:
        month, year = match.groups()
        if 1 <= int(month) <= 12:
            return f"{year}-{month}"

    # Try YYYYMM pattern (6 consecutive digits)
    match = re.search(r'(\d{4})(\d{2})(?!\d)', filename)
    if match:
        year, month = match.groups()
        if 1 <= int(month) <= 12:
            return f"{year}-{month}"

    # Try standalone YYYY (year only, with word boundaries or spaces)
    match = re.search(r'(?:^|[^\d])(\d{4})(?:[^\d]|$)', filename)
    if match:
        year = match.group(1)
        year_int = int(year)
        # Only accept reasonable years (e.g., 2000-2099)
        if 2000 <= year_int <= 2099:
            return year

    return None


def extract_document_type(text):
    """
    Extract document type from text (filename or folder name)

    Args:
        text: Text to analyze (filename or folder name)

    Returns:
        str: 'fiche-de-paie' or 'participation', defaults to 'fiche-de-paie'
    """
    text_lower = text.lower()

    # Check for participation-related keywords
    if any(keyword in text_lower for keyword in ['participation', 'particip', 'part']):
        return 'participation'

    # Check for pay slip keywords (fiche de paie, bulletin de paie, etc.)
    if any(keyword in text_lower for keyword in ['fiche', 'bulletin', 'paie', 'salaire', 'bp', 'salari']):
        return 'fiche-de-paie'

    # Default to fiche-de-paie
    return 'fiche-de-paie'


def download_file(
    service,
    file_id,
    file_name,
    dest_folder,
    employee_full_name=None,
    folder_date=None,
    folder_doc_type=None,
):
    """
    Download a file from Google Drive

    Args:
        service: Google Drive API service
        file_id: File ID to download
        file_name: Original filename
        dest_folder: Destination folder
        employee_full_name: Full employee name for renaming (optional) - format: "LastName FirstName"
        folder_date: Date extracted from parent folder name (optional, takes priority)
        folder_doc_type: Document type from parent folder name (optional, takes priority)

    Returns:
        str: Path to downloaded file, or None if download failed
    """
    try:
        request = service.files().get_media(fileId=file_id)
        os.makedirs(dest_folder, exist_ok=True)

        # Determine final filename
        if employee_full_name:
            # Use folder date/type if available, otherwise extract from filename
            date = folder_date if folder_date else extract_date_from_filename(file_name)
            doc_type = (
                folder_doc_type if folder_doc_type else extract_document_type(file_name)
            )
            # Get file extension
            _, ext = os.path.splitext(file_name)

            if date:
                # Format: <YYYY-MM>-<doc-type>-<LastName> <FirstName>.pdf
                new_file_name = f"{date}-{doc_type}-{employee_full_name}{ext}"
            else:
                # No date found, use doc type and employee name
                new_file_name = f"{doc_type}-{employee_full_name}{ext}"
        else:
            new_file_name = file_name

        file_path = os.path.join(dest_folder, new_file_name)
        fh = io.FileIO(file_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  Progress: {int(status.progress() * 100)}%", end="\r")

        if file_name != new_file_name:
            print(f"  ✓ Downloaded: {file_name} → {new_file_name}")
        else:
            print(f"  ✓ Downloaded: {file_name}")
        return file_path
    except Exception as e:
        print(f"  ✗ Error downloading {file_name}: {str(e)}")
        return None


def upload_file(service, file_path, dest_folder_id):
    """
    Upload a file to Google Drive

    Returns:
        str: Web view link to uploaded file, or None if upload failed
    """
    try:
        file_name = os.path.basename(file_path)
        file_metadata = {"name": file_name, "parents": [dest_folder_id]}

        media = MediaFileUpload(file_path, resumable=True)
        file = (
            service.files()
            .create(
                body=file_metadata, media_body=media, fields="id, name, webViewLink"
            )
            .execute()
        )

        print(f"  ✓ Uploaded: {file_name}")
        return file.get("webViewLink")
    except Exception as e:
        print(f"  ✗ Error uploading {file_path}: {str(e)}")
        return None


def clean_directory(directory):
    """
    Remove all files in a directory, or create it if it doesn't exist

    Args:
        directory: Path to directory to clean
    """
    import shutil

    if os.path.exists(directory):
        print(f"🗑️  Cleaning directory: {directory}")
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)
    print(f"✓ Directory ready: {directory}")


def search_and_download(
    service,
    folder_id,
    name_filter=None,
    dest_folder="input",
    employee_full_name=None,
    level=0,
    downloaded_files=None,
):
    """
    Recursively search folders and download matching PDF files

    Args:
        service: Google Drive API service
        folder_id: Folder ID to search
        name_filter: Optional string to filter filenames
        dest_folder: Destination folder for downloads
        employee_full_name: Full employee name for renaming files (optional)
        level: Current recursion level (for display)
        downloaded_files: List to accumulate downloaded files

    Returns:
        list: Paths to all downloaded files
    """
    if downloaded_files is None:
        downloaded_files = []

    indent = "  " * level

    try:
        folder_metadata = service.files().get(fileId=folder_id, fields="name").execute()
        folder_name = folder_metadata.get("name", "Unknown")
    except Exception as e:
        print(f"{indent}Error accessing folder: {str(e)}")
        return downloaded_files

    print(f"{indent}📁 Searching folder: {folder_name}")

    # Extract date and document type from folder name
    folder_date = extract_date_from_filename(folder_name)
    folder_doc_type = extract_document_type(folder_name)

    items = get_folder_items(service, folder_id)
    if not items:
        print(f"{indent}  (empty folder)")
        return downloaded_files

    folders = [
        item
        for item in items
        if item["mimeType"] == "application/vnd.google-apps.folder"
    ]
    files = [
        item
        for item in items
        if item["mimeType"] != "application/vnd.google-apps.folder"
    ]

    # Filter PDF files
    pdf_files = [f for f in files if f["name"].lower().endswith(".pdf")]
    if name_filter:
        pdf_files = [
            f for f in pdf_files if name_contains_string(f["name"], name_filter)
        ]

    # Download matching files
    for file_item in pdf_files:
        # Skip Google Workspace files
        if file_item.get("mimeType", "").startswith("application/vnd.google-apps."):
            print(f"{indent}  Skipping Google Workspace file: {file_item['name']}")
            continue

        file_path = download_file(
            service,
            file_item["id"],
            file_item["name"],
            dest_folder,
            employee_full_name=employee_full_name,
            folder_date=folder_date,
            folder_doc_type=folder_doc_type,
        )
        if file_path:
            downloaded_files.append(file_path)

    # Recursively search subfolders
    for folder in folders:
        search_and_download(
            service,
            folder["id"],
            name_filter,
            dest_folder,
            employee_full_name,
            level + 1,
            downloaded_files,
        )

    return downloaded_files


def extract_date_from_pdf(pdf_path):
    """Extract month and year in YYYY-MM format from PDF text pattern"""
    with open(pdf_path, "rb") as file:
        pdf_reader = PdfReader(file)
        for page_num in range(min(5, len(pdf_reader.pages))):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            match = re.search(DATE_REGEX, page_text)
            if match:
                date_str = match.group(1)
                _, month, year = date_str.split("/")
                return f"{year}-{month}"
    return None


def format_name(employee_name):
    """Convert employee name from 'last.first' to 'Last First' format"""
    name_parts = employee_name.split(".")
    if len(name_parts) != 2:
        return None
    first_name = name_parts[1].capitalize()
    last_name = name_parts[0].capitalize()
    return f"{last_name} {first_name}"


def name_in_text(name, text):
    """Check if name is in text, handling cases with hyphens, line breaks, and accents"""
    if not name or not text:
        return False
    name_clean = re.sub(r"[\s-]", "", name)
    text_clean = re.sub(r"[\s-]", "", text)
    return name_clean in text_clean


def process_pdf(input_file, employees, output_dir="output"):
    """
    Process the PDF file to extract pages for each employee

    Args:
        input_file: Path to input PDF file
        employees: List of employee dictionaries
        output_dir: Directory to save output PDFs

    Returns:
        list: Paths to all created output files
    """
    date = extract_date_from_pdf(input_file) or ""
    os.makedirs(output_dir, exist_ok=True)

    # Pre-format employee names
    formatted_employees = []
    for employee in employees:
        name = employee["name"]
        full_name = format_name(name)
        if full_name:
            last_name = full_name.split(" ")[0]
            first_name = (
                full_name.split(" ")[1] if len(full_name.split(" ")) > 1 else ""
            )
            formatted_employees.append(
                {
                    "full_name": full_name,
                    "last_name": remove_accents(last_name),
                    "first_name": remove_accents(first_name),
                    "original": employee,
                }
            )

    # Read the PDF
    with open(input_file, "rb") as file:
        pdf_reader = PdfReader(file)
        total_pages = len(pdf_reader.pages)

        # Create a dictionary to map pages to employees
        page_to_employees = {}
        for page_num in tqdm(range(total_pages), desc="Scanning pages", unit="page"):
            page = pdf_reader.pages[page_num]
            page_text = remove_accents(page.extract_text())

            for emp in formatted_employees:
                if name_in_text(emp["last_name"], page_text) and name_in_text(
                    emp["first_name"], page_text
                ):
                    if page_num not in page_to_employees:
                        page_to_employees[page_num] = []
                    page_to_employees[page_num].append(emp)

        # Create PDFs for each employee
        employee_pdfs = {}
        for page_num, employee_list in page_to_employees.items():
            for emp in employee_list:
                if emp["full_name"] not in employee_pdfs:
                    employee_pdfs[emp["full_name"]] = PdfWriter()
                employee_pdfs[emp["full_name"]].add_page(pdf_reader.pages[page_num])

        # Save the PDFs
        output_files = []
        for full_name, pdf_writer in employee_pdfs.items():
            output_filename = f"{output_dir}/{date} {full_name}.pdf"
            with open(output_filename, "wb") as output_file:
                pdf_writer.write(output_file)
            tqdm.write(f"✓ Created PDF for {full_name}: {output_filename}")
            output_files.append(output_filename)

        return output_files
