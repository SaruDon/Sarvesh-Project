$INPUT_DIR = "C:\Users\Student\cicids2018\Friday-23-02-2018\pcap"
$OUTPUT_DIR = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Friday-23-02-2018"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"

if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR -Force
}

$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "cap*"
$large_pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "*.pcap"
$all_files = $pcaps + $large_pcaps | Sort-Object Name -Unique

Write-Host "Starting Brute Force Extraction for $($all_files.Count) files..."

foreach ($f in $all_files) {
    if ($f.Length -eq 0) { continue }
    $csv_name = $f.Name + ".csv"
    $output_path = Join-Path $OUTPUT_DIR $csv_name
    
    if (Test-Path $output_path) {
        if ((Get-Item $output_path).Length -gt 0) {
            continue
        }
    }

    $size_mb = [math]::Round($f.Length / 1MB, 2)
    Write-Host "Processing $($f.Name) ($size_mb MB)..."
    
    & $TSHARK_PATH -r $f.FullName -T fields `
        -e frame.time_epoch -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport `
        -e frame.len -e ip.proto -e tcp.flags -e udp.srcport -e udp.dstport `
        -e ip.ttl -e tcp.window_size_value `
        -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $output_path -Encoding utf8
}

Write-Host "Brute Force Extraction Complete."
