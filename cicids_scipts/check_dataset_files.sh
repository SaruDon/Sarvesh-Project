#!/bin/bash

BASE="s3://cse-cic-ids2018/Original Network Traffic and Log data"

FOLDERS=(
"Friday-02-03-2018"
"Friday-16-02-2018"
"Friday-23-02-2018"
"Thursday-01-03-2018"
"Thursday-15-02-2018"
"Thursday-22-02-2018"
"Tuesday-20-02-2018"
"Wednesday-14-02-2018"
"Wednesday-21-02-2018"
"Wednesday-28-02-2018"
)

echo "Checking dataset files..."
echo "--------------------------------"

for FOLDER in "${FOLDERS[@]}"
do
    echo "Checking $FOLDER"

    FILES=$(aws s3 ls --no-sign-request "$BASE/$FOLDER/")

    HAS_PCAP=$(echo "$FILES" | grep "pcap.rar")
    HAS_LOGS=$(echo "$FILES" | grep "logs.zip")

    if [[ -n "$HAS_PCAP" && -n "$HAS_LOGS" ]]; then
        echo "OK: pcap.rar and logs.zip exist"
    else
        echo "WARNING: Missing files in $FOLDER"
        echo "$FILES"
    fi

    echo "--------------------------------"
done
