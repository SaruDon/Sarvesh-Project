# Optimized Tuesday-20 UCAP Extraction
$in_pcap = "C:\Users\Student\cicids2018\Tuesday-20-02-2018\pcap\pcap\UCAP172.31.69.25"
$out_csv = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Tuesday-20-02-2018\UCAP172.31.69.25.csv"

# Attack Windows (Epochs) with 5m buffer
$windows = @(
    "(frame.time_epoch >= 1519135620 && frame.time_epoch <= 1519139580)", # 14:12 - 15:08 UTC
    "(frame.time_epoch >= 1519149600 && frame.time_epoch <= 1519153800)"  # 18:05 - 19:05 UTC
)
$filter = $windows -join " || "

Write-Host "🚀 Starting Optimized Extraction for $in_pcap"
Write-Host "   Filter: $filter"

# Clean up any partial files
Get-Process tshark, dumpcap | Stop-Process -Force -ErrorAction SilentlyContinue
if (Test-Path $out_csv) { Remove-Item $out_csv -Force }

# Run tshark with display filter
cmd /c "tshark -r `"$in_pcap`" -Y `"$filter`" -T fields -E header=y -E separator=, -E quote=d -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -e ip.src -e ip.dst -e ip.proto -e tcp.srcport -e tcp.dstport -e tcp.flags -e udp.srcport -e udp.dstport -e ip.ttl -e tcp.window_size_value > `"$out_csv`""

Write-Host "=== Optimized Extraction Complete ==="
