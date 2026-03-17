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
    # Check if download is complete
    if (Test-Path "$($zip.FullName).aria2") {
        Write-Host "Skipping $($zip.Name) (Download in progress...)"
        continue
    }

    # Check if already extracted (heuristic: look for a folder with same name or a 'pcap' folder)
    $extracted_folder = Join-Path $INPUT_DIR $zip.BaseName
    $pcap_folder = Join-Path $INPUT_DIR "pcap"
    
    if ((Test-Path $extracted_folder) -or (Test-Path $pcap_folder)) {
        Write-Host "Skipping unzip: Data for $($zip.Name) appears already extracted."
        continue
    }

    Write-Host "Unzipping $($zip.Name)..."
    try {
        Expand-Archive -Path $zip.FullName -DestinationPath $INPUT_DIR -Force
    } catch {
        Write-Warning "Failed to unzip $($zip.Name): $_"
    }
}

# 2. Process all PCAP files found
# Search for .pcap files OR files starting with 'cap' in a 'pcap' subdirectory
$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "*.pcap" -Recurse
if ($pcaps.Count -eq 0) {
    $pcap_sub = Join-Path $INPUT_DIR "pcap"
    if (Test-Path $pcap_sub) {
        $pcaps = Get-ChildItem -Path $pcap_sub -Filter "cap*"
    }
}

$count = 0
foreach ($pcap in $pcaps) {
    $basename = $pcap.BaseName
    if ($pcap.Extension -ne ".pcap" -and $pcap.Extension -ne "") {
        $basename = "$($pcap.BaseName)$($pcap.Extension)"
    }
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) {
        Write-Host "SKIP: $basename.csv already exists."
        continue
    }

    if ($count -ge 3) { break }
    $count++

    Write-Host "Processing $basename..."
    
    # Run tshark to extract flow features
    # Note: added ip.ttl and tcp.window_size_value for advanced sequence modeling
    & $TSHARK_PATH -r $pcap.FullName -T fields `
        -e frame.time_epoch `
        -e ip.src -e ip.dst `
        -e tcp.srcport -e tcp.dstport `
        -e frame.len -e ip.proto -e tcp.flags `
        -e udp.srcport -e udp.dstport `
        -e ip.ttl -e tcp.window_size_value `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $target_csv -Encoding utf8
}

Write-Host "Extraction finished."
