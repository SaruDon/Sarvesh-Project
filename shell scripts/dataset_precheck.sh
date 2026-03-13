#!/bin/bash

DATASET_SIZE_GB=230
EXTRACTION_SIZE_GB=500

TARGET_DIR="/media/a10/Windows"

AVAILABLE=$(df -BG "$TARGET_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')

echo "Available disk space: ${AVAILABLE} GB"
echo "Dataset download size: ${DATASET_SIZE_GB} GB"
echo "Estimated extracted size: ${EXTRACTION_SIZE_GB} GB"

if [ "$AVAILABLE" -gt "$EXTRACTION_SIZE_GB" ]; then
    echo "✔ Enough space for full dataset"
elif [ "$AVAILABLE" -gt "$DATASET_SIZE_GB" ]; then
    echo "⚠ Enough space for compressed dataset but extraction may fail"
else
    echo "✖ Not enough space to download dataset"
fi
