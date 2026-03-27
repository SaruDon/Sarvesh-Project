param([string]$DayName)

$INPUT_DIR = "C:\Users\Student\cicids2018\$DayName"
$OUTPUT_DIR = "extracted_features\$DayName"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR -Force }

Write-Host "Searching for data in $INPUT_DIR..."

$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "*.pcap" -Recurse
if ($pcaps.Count -eq 0) {
    $pcap_sub = Join-Path $INPUT_DIR "pcap"
    if (Test-Path $pcap_sub) {
        $pcaps = Get-ChildItem -Path $pcap_sub -Filter "cap*"
    }
}

Write-Host "Found $($pcaps.Count) files."

foreach ($pcap in $pcaps) {
    $basename = $pcap.BaseName
    if ($pcap.Extension -ne ".pcap" -and $pcap.Extension -ne "") {
        $basename = "$($pcap.BaseName)$($pcap.Extension)"
    }
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) { continue }

    Write-Host "Processing $basename..."
    
    & $TSHARK_PATH -r $pcap.FullName -T fields `
        -e frame.time_epoch `
        -e ip.src -e ip.dst `
        -e tcp.srcport -e tcp.dstport `
        -e frame.len -e ip.proto -e tcp.flags `
        -e udp.srcport -e udp.dstport `
        -e ip.ttl -e tcp.window_size_value `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $target_csv -Encoding utf8
}

Write-Host "Extraction for $DayName finished."
