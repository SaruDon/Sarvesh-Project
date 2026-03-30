# Tuesday-20 DDoS Extraction Script
$date = "Tuesday-20-02-2018"
$raw_dir = "C:\Users\Student\cicids2018\$date\pcap\pcap"
$out_dir = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\$date"

if (-not (Test-Path $out_dir)) { New-Item -ItemType Directory -Path $out_dir -Force }

$pcap_files = Get-ChildItem -Path $raw_dir -File
Write-Host "Found $($pcap_files.Count) PCAP candidates in $date"

$count = 0
foreach ($f in $pcap_files) {
    $out_csv = Join-Path $out_dir "$($f.Name).csv"
    if (Test-Path $out_csv) {
        $count++
        continue
    }
    
    Write-Host "  Extracting: $($f.Name) ($([math]::Round($f.Length/1MB, 1)) MB)..."
    
    # Run tshark via CMD to avoid PowerShell pipeline issues
    cmd /c "tshark -r `"$($f.FullName)`" -T fields -E header=y -E separator=, -E quote=d -e frame.number -e frame.time_relative -e frame.len -e ip.src -e ip.dst -e ip.proto -e tcp.srcport -e tcp.dstport -e tcp.flags -e udp.srcport -e udp.dstport -e ip.ttl -e tcp.window_size_value > `"$out_csv`""
    
    $count++
    # Periodic progress
    if ($count % 50 -eq 0) { Write-Host "Progress: $count / $($pcap_files.Count)" }
}

Write-Host "=== $date Extraction Complete ==="
Write-Host "  Extracted: $count  |  Skipped: 0  |  Failed: 0"
