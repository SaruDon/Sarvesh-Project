# PCAP Feature Extraction (PowerShell)
# Extracts fields relevant for flow analysis from CIC-IDS-2018 datasets

$INPUT_DIR = "C:\Users\Student\cicids2018"
$OUTPUT_DIR = "extracted_features"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR }

# Check for Wireshark
if (!(Test-Path $TSHARK_PATH)) {
    Write-Error "tshark.exe not found at $TSHARK_PATH. Please ensure Wireshark is installed."
    return
}

Write-Host "Searching for data in $INPUT_DIR..."

# 1. First, handle any ZIP files that need extraction
$zips = Get-ChildItem -Path $INPUT_DIR -Filter "*.zip"
foreach ($zip in $zips) {
    # Only unzip if there isn't a corresponding .aria2 file (meaning download is complete)
    if (!(Test-Path "$($zip.FullName).aria2")) {
        Write-Host "Unzipping $($zip.Name)..."
        try {
            Expand-Archive -Path $zip.FullName -DestinationPath $INPUT_DIR -Force
        } catch {
            Write-Warning "Failed to unzip $($zip.Name): $_"
        }
    } else {
        Write-Host "Skipping $($zip.Name) (Download in progress...)"
    }
}

# 2. Process all PCAP files found
$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "*.pcap" -Recurse
foreach ($pcap in $pcaps) {
    $basename = $pcap.BaseName
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) {
        Write-Host "SKIP: $basename.csv already exists."
        continue
    }

    Write-Host "Processing $basename..."
    
    # Run tshark to extract flow features
    & $TSHARK_PATH -r $pcap.FullName -T fields `
        -e frame.number -e frame.time_relative -e frame.len `
        -e ip.src -e ip.dst -e ip.proto `
        -e tcp.srcport -e tcp.dstport -e tcp.flags `
        -e udp.srcport -e udp.dstport `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $target_csv -Encoding utf8
}

Write-Host "Extraction finished."
