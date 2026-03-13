#!/bin/bash

# PCAP Feature Extraction Script
# Uses tshark to extract fields relevant for flow analysis

INPUT_DIR="C:/Users/Student/cicids2018"
OUTPUT_DIR="extracted_features"
mkdir -p "$OUTPUT_DIR"

echo "Starting feature extraction from $INPUT_DIR..."

for PCAP in "$INPUT_DIR"/*.pcap; do
    BASENAME=$(basename "$PCAP" .pcap)
    echo "Processing $BASENAME..."
    
    # Extracting core flow fields
    tshark -r "$PCAP" -T fields \
        -e frame.number -e frame.time_relative -e frame.len \
        -e ip.src -e ip.dst -e ip.proto \
        -e tcp.srcport -e tcp.dstport -e tcp.flags \
        -e udp.srcport -e udp.dstport \
        -E header=y -E separator=, -E quote=d > "$OUTPUT_DIR/$BASENAME.csv"
done

echo "Extraction finished."
