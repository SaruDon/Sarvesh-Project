#!/bin/bash

# Hybrid NIDS Pipeline Master Script
# Coordinates: Download -> Extraction -> EDA -> Flow Generation

PROJECT_ROOT=$(pwd)
LOGFILE="$PROJECT_ROOT/download.log"

echo "=== Hybrid NIDS Pipeline Started: $(date) ===" | tee -a "$LOGFILE"

# 1. Download Phase
echo "[1/4] Starting/Resuming CIC-IDS-2018 Download..." | tee -a "$LOGFILE"
bash "$PROJECT_ROOT/cicids_scipts/download_cicids2018.sh"

# 2. Extraction Phase (Integrating tshark)
echo "[2/4] Extracting PCAP features from C:/Users/Student/cicids2018..." | tee -a "$LOGFILE"
bash "$PROJECT_ROOT/extract_pcap.sh"

# 3. EDA Phase
echo "[3/4] Running Initial EDA..." | tee -a "$LOGFILE"
python3 "$PROJECT_ROOT/eda_initial.py"

# 4. Dataset Building
echo "[4/4] Building Labeled Datasets..." | tee -a "$LOGFILE"
python3 "$PROJECT_ROOT/dataset_builder.py"

echo "=== Pipeline Completed: $(date) ===" | tee -a "$LOGFILE"
