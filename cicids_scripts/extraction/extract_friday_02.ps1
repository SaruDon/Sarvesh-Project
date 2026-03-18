# Robust Parallel PCAP Feature Extraction for Friday-02-03-2018
# Uses Absolute Paths and throttles jobs to prevent overhead

$BASE_DIR = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project"
$INPUT_DIR = "C:\Users\Student\cicids2018\Friday-02-03-2018\pcap"
$OUTPUT_DIR = "$BASE_DIR\extracted_features\Friday-02-03-2018"
$TSHARK_PATH = "C:\Program Files\Wireshark\tshark.exe"
$MAX_PARALLEL = 8

if (!(Test-Path $OUTPUT_DIR)) { New-Item -ItemType Directory -Path $OUTPUT_DIR -Force }

$pcaps = Get-ChildItem -Path $INPUT_DIR -Filter "cap*"
Write-Host "Total PCAPs to check: $($pcaps.Count)"

$jobs = @()
$count = 0

foreach ($pcap in $pcaps) {
    if ($pcap.PSIsContainer) { continue }
    
    $target_csv = Join-Path $OUTPUT_DIR "$($pcap.Name).csv"
    
    # Skip if already exists and has data
    if (Test-Path $target_csv) {
        if ((Get-Item $target_csv).Length -gt 500) {
            continue
        }
    }

    # Throttle
    while ((Get-Job -State Running).Count -ge $MAX_PARALLEL) {
        Start-Sleep -Seconds 1
    }

    $sb = {
        param($in, $out, $exe)
        & $exe -r $in -T fields `
            -e frame.time_epoch -e ip.src -e ip.dst `
            -e tcp.srcport -e tcp.dstport -e frame.len `
            -e ip.proto -e tcp.flags -e udp.srcport `
            -e udp.dstport -e ip.ttl -e tcp.window_size_value `
            -E "header=y" -E "separator=," -E "quote=d" | Out-File -FilePath $out -Encoding utf8
    }

    Start-Job -ScriptBlock $sb -ArgumentList $pcap.FullName, $target_csv, $TSHARK_PATH | Out-Null
    $count++
    
    if ($count % 10 -eq 0) {
        Write-Host "Started $count new extraction jobs..."
    }
}

Write-Host "All jobs submitted. Waiting for completion..."
while ((Get-Job -State Running).Count -gt 0) {
    Write-Host "Remaining jobs: $((Get-Job -State Running).Count)"
    Start-Sleep -Seconds 5
}

Write-Host "Full parallel extraction finished."
Get-Job | Remove-Job
