# PCAP Feature Extraction for Friday-02-03-2018 (Full)
# Extracts fields relevant for flow analysis from the Botnet dataset

$INPUT_DIR = "C:\Users\Student\cicids2018\Friday-02-03-2018\pcap"
$OUTPUT_DIR = "extracted_features\Friday-02-03-2018"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR -Force }

# Check for Wireshark
if (!(Test-Path $TSHARK_PATH)) {
    Write-Error "tshark.exe not found at $TSHARK_PATH. Please ensure Wireshark is installed."
    return
}

# Search for all files starting with 'cap' or '.pcap' in the input directory
$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "cap*"

Write-Host "Found $($pcaps.Count) PCAP files in $INPUT_DIR. Starting FULL extraction..."

$count = 0
foreach ($pcap in $pcaps) {
    if ($pcap.PSIsContainer) { continue }
    
    $basename = $pcap.Name
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) {
        Write-Host "SKIP: $basename.csv already exists."
        continue
    }

    Write-Host "Processing $basename ($($count+1)/$($pcaps.Count))..."
    
    # Run tshark to extract flow features
    & $TSHARK_PATH -r $pcap.FullName -T fields `
        -e frame.time_epoch `
        -e ip.src -e ip.dst `
        -e tcp.srcport -e tcp.dstport `
        -e frame.len -e ip.proto -e tcp.flags `
        -e udp.srcport -e udp.dstport `
        -e ip.ttl -e tcp.window_size_value `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $target_csv -Encoding utf8
    
    $count++
}

Write-Host "Full extraction finished. Processed $count files."
