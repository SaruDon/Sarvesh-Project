# Tuesday-20 DDoS FAST Parallel Extraction Script
$date = "Tuesday-20-02-2018"
$raw_dir = "C:\Users\Student\cicids2018\$date\pcap\pcap"
$out_dir = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\$date"
$max_jobs = 8  # Parallel throttle

if (-not (Test-Path $out_dir)) { New-Item -ItemType Directory -Path $out_dir -Force }

$pcap_files = Get-ChildItem -Path $raw_dir -File
Write-Host "🚀 Parallel Extraction Started: Found $($pcap_files.Count) PCAPs for $date"
Write-Host "   Target: $out_dir"
Write-Host "   Concurrency: $max_jobs parallel jobs"

$count = 0
foreach ($f in $pcap_files) {
    $out_csv = Join-Path $out_dir "$($f.Name).csv"
    
    # Skip if already exists
    if (Test-Path $out_csv) {
        $count++
        continue
    }

    # Throttle: Wait for a job slot
    while ((Get-Job -State Running).Count -ge $max_jobs) {
        Start-Sleep -Milliseconds 200
    }

    # Start Extraction Job
    $full_path = $f.FullName
    Start-Job -ScriptBlock {
        param($in, $out)
        # Use cmd /c to ensure reliable tshark execution in PowerShell jobs
        cmd /c "tshark -r `"$in`" -T fields -E header=y -E separator=, -E quote=d -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -e ip.src -e ip.dst -e ip.proto -e tcp.srcport -e tcp.dstport -e tcp.flags -e udp.srcport -e udp.dstport -e ip.ttl -e tcp.window_size_value > `"$out`""
    } -ArgumentList $full_path, $out_csv | Out-Null

    $count++
    if ($count % 10 -eq 0) {
        $running = (Get-Job -State Running).Count
        $done = (Get-Job -State Completed).Count
        Write-Host "   Progress: $count / $($pcap_files.Count) | Running: $running | Completed: $done"
        Receive-Job -Job (Get-Job -State Completed) -ErrorAction SilentlyContinue | Out-Null
        Remove-Job -State Completed
    }
}

# Final Wait
Write-Host "   Finishing remaining jobs..."
while ((Get-Job -State Running).Count -gt 0) { Start-Sleep -Seconds 1 }
Remove-Job *

Write-Host "=== $date Parallel Extraction Complete ==="
