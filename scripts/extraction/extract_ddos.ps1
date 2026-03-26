# DDoS Dataset Feature Extraction (Friday-16-02-2018)
$INPUT_DIR = "C:\Users\Student\cicids2018\Friday-16-02-2018\pcap"
$OUTPUT_DIR = "extracted_features\Friday-16-02-2018"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR -Force }

Write-Host "Starting extraction for DDoS dataset from $INPUT_DIR..."

$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "cap*"
$large_pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "*.pcap"
$all_files = $pcaps + $large_pcaps | Sort-Object Name -Unique

Write-Host "Found $($all_files.Count) files to process."

foreach ($pcap in $all_files) {
    $basename = $pcap.Name
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) {
        Write-Host "SKIP: $basename already processed."
        continue
    }

    Write-Host "Processing $basename ($([math]::Round($pcap.Length / 1MB, 2)) MB)..."
    
    & $TSHARK_PATH -r $pcap.FullName -T fields `
        -e frame.time_epoch `
        -e ip.src -e ip.dst `
        -e tcp.srcport -e tcp.dstport `
        -e frame.len -e ip.proto -e tcp.flags `
        -e udp.srcport -e udp.dstport `
        -e ip.ttl -e tcp.window_size_value `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $target_csv -Encoding utf8
}

Write-Host "DDoS Extraction Complete."
