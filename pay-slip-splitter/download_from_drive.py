#!/usr/bin/env python3
"""
Script to download files from a Google Drive folder that contain a specific employee name.
Supports recursive folder traversal.

Usage:
    python download_from_drive.py <employee_name> [folder_id]

Example:
    python download_from_drive.py "Madura"
    python download_from_drive.py "Madura" 1abc123def456
"""

import sys
import os
import yaml
from utils import authenticate_drive, search_and_download, clean_directory, format_name, FOLDER_ID

EMPLOYEE_FILE = "../employees.yaml"


def find_employee_full_name(employee_filter):
    """
    Find the full name of an employee from employees.yaml based on a filter string

    Args:
        employee_filter: String to match against employee names (last name or full name)

    Returns:
        str: Full name in "LastName FirstName" format, or the filter string if not found
    """
    try:
        with open(EMPLOYEE_FILE, "r") as f:
            data = yaml.safe_load(f)

        if not data or "employees" not in data:
            return employee_filter

        # Get active employees
        active_employees = [
            employee
            for employee in data["employees"]
            if employee.get("current_employee", True)
        ]

        # Search for matching employee
        filter_lower = employee_filter.lower()
        for employee in active_employees:
            full_name = format_name(employee["name"])
            if full_name:
                # Check if filter matches last name or full name
                if (
                    filter_lower in full_name.lower()
                    or filter_lower in employee["name"].lower()
                ):
                    return full_name

        # If no match found, return the original filter
        return employee_filter
    except Exception as e:
        print(f"Warning: Could not load employee list: {e}")
        return employee_filter


def main():
    if len(sys.argv) < 2:
        print("Usage: python download_from_drive.py <employee_name> [folder_id]")
        print('Example: python download_from_drive.py "Madura"')
        print(f'Example: python download_from_drive.py "Madura" 1abc123def456')
        print(f"\nDefault folder ID: {FOLDER_ID}")
        sys.exit(1)

    employee_filter = sys.argv[1]
    folder_id = sys.argv[2] if len(sys.argv) > 2 else FOLDER_ID

    # Get full employee name from employees.yaml
    employee_full_name = find_employee_full_name(employee_filter)

    # Create output directory path based on employee filter
    output_dir = os.path.join("output", employee_filter)

    print("=" * 60)
    print("    GOOGLE DRIVE FILE DOWNLOADER")
    print("=" * 60)
    print(f"Employee filter: {employee_filter}")
    print(f"Employee full name: {employee_full_name}")
    print(f"Folder ID: {folder_id}")
    print(f"Download directory: {output_dir}")
    print("=" * 60)
    print()

    # Clean output directory
    clean_directory(output_dir)
    print()

    # Authenticate
    print("🔐 Authenticating...")
    service = authenticate_drive(readonly=True)
    print("✓ Authentication successful!")
    print()

    # Search and download
    downloaded_files = search_and_download(
        service,
        folder_id,
        name_filter=employee_filter,
        dest_folder=output_dir,
        employee_full_name=employee_full_name,
    )

    print()
    print("=" * 60)
    print(f"Download complete! Total files downloaded: {len(downloaded_files)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
