#!/bin/bash

set -eu

APP_HOME=$HOME/work/create-ics

OUTPUT_DIR=$APP_HOME/24hr-checkins

if [ ! -f "$OUTPUT_DIR" ]; then
	mkdir -p "$OUTPUT_DIR"
fi

tmpdir=${TMPDIR-/tmp}/club-visits.$$
mkdir $tmpdir || exit 1
trap "rm -rf $tmpdir; exit" 0 1 2 3 15

cd $tmpdir

$APP_HOME/download-pdf.py --headless

if [ ! -f *.pdf ]; then
	echo "No pdf downloaded"
	exit 1
fi

pdf_file=$(ls *.pdf)

$APP_HOME/club-visits-cal.py "$pdf_file"

cp -v *.pdf *.ics "$OUTPUT_DIR"

