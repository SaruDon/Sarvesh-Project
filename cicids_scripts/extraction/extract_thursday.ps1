# PCAP Feature Extraction for Thursday-01-03-2018 (Custom)
# Extracts fields relevant for flow analysis from the Thursday dataset

$INPUT_DIR = "C:\Users\Student\cicids2018\Thursday-01-03-2018_v2"
$OUTPUT_DIR = "extracted_features\Thursday-01-03-2018"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR -Force }

# Check for Wireshark
if (!(Test-Path $TSHARK_PATH)) {
    Write-Error "tshark.exe not found at $TSHARK_PATH. Please ensure Wireshark is installed."
    return
}

# Search for all files starting with 'cap' in the input directory (recursive)
$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "cap*" -Recurse

Write-Host "Found $($pcaps.Count) potential PCAP files in $INPUT_DIR."

$count = 0
foreach ($pcap in $pcaps) {
    # Skip if it's a directory
    if ($pcap.PSIsContainer) { continue }
    
    $basename = $pcap.Name
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) {
        Write-Host "SKIP: $basename.csv already exists."
        continue
    }

    # Trial limit: 3 files (as in original script)
    if ($count -ge 3) { 
        Write-Host "Trial limit (3 files) reached. Stopping extraction."
        break 
    }
    $count++

    Write-Host "Processing $basename..."
    
    # Run tshark to extract flow features
    & $TSHARK_PATH -r $pcap.FullName -T fields `
        -e frame.time_epoch `
        -e ip.src -e ip.dst `
        -e tcp.srcport -e tcp.dstport `
        -e frame.len -e ip.proto -e tcp.flags `
        -e udp.srcport -e udp.dstport `
        -e ip.ttl -e tcp.window_size_value `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $target_csv -Encoding utf8
}

Write-Host "Extraction finished. Processed $count files."
