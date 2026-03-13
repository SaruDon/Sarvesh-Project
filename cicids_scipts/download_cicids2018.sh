#!/bin/bash

DATASET_DIR="/mnt/cicids2018"
mkdir -p "$DATASET_DIR"
cd "$DATASET_DIR"

BASE_S3="s3://cse-cic-ids2018/Original Network Traffic and Log data"
BASE_HTTP="https://cse-cic-ids2018.s3.amazonaws.com/Original%20Network%20Traffic%20and%20Log%20data"

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

LOGFILE="/home/a10/Desktop/Sarvesh Project/download_log.txt"

echo "Download started $(date)" | tee -a "$LOGFILE"

for FOLDER in "${FOLDERS[@]}"
do
    echo "Processing $FOLDER" | tee -a "$LOGFILE"

    FILES=$(aws s3 ls --no-sign-request "$BASE_S3/$FOLDER/")

    PCAP_FILE=$(echo "$FILES" | grep pcap | awk '{print $4}')
    LOG_FILE=$(echo "$FILES" | grep logs.zip | awk '{print $4}')

    LOCAL_PCAP="$DATASET_DIR/$FOLDER-$PCAP_FILE"
    LOCAL_LOG="$DATASET_DIR/$FOLDER-$LOG_FILE"

    # -------------------------
    # Download PCAP with resume
    # -------------------------
    # If the file exists but we see a .aria2 file, we SHOULD resume.
    # aria2 handles the -c resume internally, so if we HAVE a .aria2 file, 
    # we should NOT skip. 
    if [ -f "$LOCAL_PCAP" ] && [ ! -f "$LOCAL_PCAP.aria2" ]; then
        echo "SKIP: $PCAP_FILE already exists and no .aria2 file found" | tee -a "$LOGFILE"
    else
        echo "Starting/Resuming $PCAP_FILE with aria2..." | tee -a "$LOGFILE"

        URL="$BASE_HTTP/$FOLDER/$PCAP_FILE"

        aria2c \
        -x 8 \
        -s 8 \
        -c \
        -d "$DATASET_DIR" \
        -o "$FOLDER-$PCAP_FILE" \
        "$URL"
    fi

    # -------------------------
    # Download logs
    # -------------------------
    if [ -f "$LOCAL_LOG" ]; then
        echo "SKIP: $LOG_FILE already exists" | tee -a "$LOGFILE"
    else
        echo "Downloading $LOG_FILE" | tee -a "$LOGFILE"

        aws s3 cp --no-sign-request \
        "$BASE_S3/$FOLDER/$LOG_FILE" \
        "$LOCAL_LOG"
    fi

    echo "Finished $FOLDER" | tee -a "$LOGFILE"
    echo "---------------------------------" | tee -a "$LOGFILE"

done

echo "All downloads finished $(date)" | tee -a "$LOGFILE"
