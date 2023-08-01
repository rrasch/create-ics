#!/bin/bash

set -eux

APP_HOME=$HOME/work/create-ics

OUTPUT_DIR=$APP_HOME/24hr-checkins

if [ ! -f "$OUTPUT_DIR" ]; then
	mkdir -p "$OUTPUT_DIR"
fi

if [ $# -ne 1 ]; then
    echo -e "\nUsage: $0 <pdf file>\n"
    exit 1
fi

pdf_file=$1

pdf_base="${pdf_file%%.*}"

pdf_name="${pdf_base##*/}"

ocr_file="${pdf_name}.ocr.pdf"

tif_file="${pdf_name}.tif"

txt_file="${pdf_base%.*}.txt"

tmpdir=${TMPDIR-/tmp}/gym-cal.$$
mkdir $tmpdir || exit 1
trap "rm -rf $tmpdir; exit" 0 1 2 3 15

cd $tmpdir

# #OCRMYPDF_ARGS="--tesseract-pagesegmode 6 --tesseract-oem 3"
# OCRMYPDF_ARGS="--oversample 300"
# 
# ocrmypdf --output-type pdf --skip-text $OCRMYPDF_ARGS "$pdf_file" "$ocr_file"
#  
# pdftotext "$ocr_file" - | tee "$txt_file"

gs -q -dNOPAUSE -r300 -sDEVICE=tiffgray -sOutputFile="$tif_file" "$pdf_file" -c quit

#tesseract --psm 12 "$tif_file" stdout pdf > "$ocr_file"
tesseract "$tif_file" stdout pdf > "$ocr_file"

pdftotext "$ocr_file" - | tee "$txt_file"

sed -i '/^$/d' "$txt_file"
sed -i 's/^\([23456789]\)1/\1\//g' "$txt_file"

$APP_HOME/gym-calendar.py "$txt_file" 2023

