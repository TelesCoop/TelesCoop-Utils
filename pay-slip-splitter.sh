#!/bin/bash
# Require pdftk and pdftotext

# Check if input file is provided
if [ -z "$1" ]
then
    echo "No input file provided"
    exit 1
fi

# Store the input file name in a variable
input_file="$1"

date=$(cut -d ' ' -f 1 <<< "$input_file")
echo "date : $date"

temp_file="temp.pdf"

# List of names
full_names=("Bernier Antoine" "Feltin Clément" "Madura Quentin" "Andres Alice" "Legeron Camille" "Bellec Maxime" "Auge Marc-Antoine")
names=("Bernier" "Feltin" "Madura" "Andres" "Legeron" "Bellec" "Auge")


# Loop through each name
for ((i=0; i<${#names[@]}; i++));
do
    # Store the name in a variable
    name="${names[$i]}"
    full_name="${full_names[$i]}"
    # Initialize an empty array to store page numbers
    pages=()

    # Loop through each page in the PDF
    for page in $(seq 1 $(pdftk "$input_file" dump_data | grep NumberOfPages | awk '{print $2}'))
    do
        # get current page content

        pdftk "$input_file" cat $page output $temp_file
        echo "Checking $name on page $page"
        # If the name is found on the page, add the page number to the array with insensitive case with pdftotext and only with the page
        if pdftotext $temp_file - | grep -qi "$name"; then
            echo "Found $name on page $page"
            pages+=($page)
        fi
    done

    # If pages were found for the name, create a new PDF with those pages
    if [ ${#pages[@]} -gt 0 ]; then
        pdftk "$input_file" cat ${pages[@]} output "output/${date} ${full_name}.pdf"
    fi
done

# delete $temp_file
rm $temp_file
