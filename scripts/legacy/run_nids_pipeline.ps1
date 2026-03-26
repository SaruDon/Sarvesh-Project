# Hybrid NIDS Pipeline Master Script (PowerShell)
# Coordinates: Download -> Extraction -> EDA -> Flow Generation

$PROJECT_ROOT = Get-Location
$DATASET_DIR = "C:\Users\Student\cicids2018"
$LOGFILE = Join-Path $PROJECT_ROOT "pipeline.log"

Write-Host "=== Hybrid NIDS Pipeline Started: $(Get-Date) ===" | Tee-Object -Append $LOGFILE

# 1. Download Phase (Optional if already running)
Write-Host "[1/4] Checking Data Acquisition..." | Tee-Object -Append $LOGFILE
# & powershell.exe -ExecutionPolicy Bypass -File "cicids_scipts\download_missing.ps1"

# 2. Extraction Phase
Write-Host "[2/4] Extracting PCAP features using Wireshark/tshark..." | Tee-Object -Append $LOGFILE
& powershell.exe -ExecutionPolicy Bypass -File "cicids_scipts\extract_pcap.ps1"

# 3. EDA Phase
Write-Host "[3/4] Running Initial EDA..." | Tee-Object -Append $LOGFILE
.\venv\Scripts\python.exe eda_initial.py | Tee-Object -Append $LOGFILE

# 4. Dataset Building
Write-Host "[4/4] Building Labeled Datasets..." | Tee-Object -Append $LOGFILE
.\venv\Scripts\python.exe dataset_builder.py | Tee-Object -Append $LOGFILE

Write-Host "=== Pipeline Completed: $(Get-Date) ===" | Tee-Object -Append $LOGFILE
