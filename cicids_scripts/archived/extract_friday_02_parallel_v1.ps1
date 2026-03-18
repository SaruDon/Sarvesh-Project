# High-Performance Parallel PCAP Feature Extraction for Friday-02-03-2018
# Utilizes multiple CPU cores to process PCAPs in parallel

$INPUT_DIR = "C:\Users\Student\cicids2018\Friday-02-03-2018\pcap"
$OUTPUT_DIR = "extracted_features\Friday-02-03-2018"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"
$MAX_PARALLEL = 10  # Number of concurrent tshark instances

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR -Force }

$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "cap*" | Where-Object { -not $_.PSIsContainer }
Write-Host "Found $($pcaps.Count) PCAP files. Starting PARALLEL extraction ($MAX_PARALLEL threads)..."

$jobs = @()
$total = $pcaps.Count
$processed = 0

foreach ($pcap in $pcaps) {
    $basename = $pcap.Name
    $target_csv = Join-Path $OUTPUT_DIR "$basename.csv"
    
    if (Test-Path $target_csv) {
        # Check if file is empty or just header
        if ((Get-Item $target_csv).Length -gt 200) {
            $processed++
            continue
        }
    }

    # Throttle: Wait if too many jobs are running
    while (($jobs | Where-Object { $_.State -eq "Running" }).Count -ge $MAX_PARALLEL) {
        Start-Sleep -Milliseconds 500
    }

    $scriptBlock = {
        param($pcapPath, $csvPath, $tsharkPath)
        & $tsharkPath -r $pcapPath -T fields `
            -e frame.time_epoch `
            -e ip.src -e ip.dst `
            -e tcp.srcport -e tcp.dstport `
            -e frame.len -e ip.proto -e tcp.flags `
            -e udp.srcport -e udp.dstport `
            -e ip.ttl -e tcp.window_size_value `
            -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $csvPath -Encoding utf8
    }

    $jobs += Start-Job -ScriptBlock $scriptBlock -ArgumentList $pcap.FullName, $target_csv, $TSHARK_PATH
    $processed++
    
    if ($processed % 5 -eq 0) {
        Write-Host "Dispatched $processed/$total files..."
    }
}

Write-Host "All jobs dispatched. Waiting for completion..."
$jobs | Wait-Job | Out-Null
Write-Host "Parallel extraction finished."
