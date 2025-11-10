#!/usr/bin/env python3
import sys
import yaml
from utils import process_pdf

# Global constants
OUTPUT_DIR = "output"
EMPLOYEE_FILE = "../employees.yaml"


def main():
    if len(sys.argv) < 2:
        print("Please provide file path")
        sys.exit(1)

    input_file = sys.argv[1]

    print(f"Loading employee list from {EMPLOYEE_FILE}")
    with open(EMPLOYEE_FILE, "r") as f:
        data = yaml.safe_load(f)

    if not data or "employees" not in data:
        print("Invalid employees data format")
        sys.exit(1)

    # Filter active employees (exclude those with current_employee: false)
    active_employees = [
        employee
        for employee in data["employees"]
        if employee.get("current_employee", True)
    ]
    # Process the PDF
    process_pdf(input_file, active_employees, OUTPUT_DIR)


if __name__ == "__main__":
    main()
