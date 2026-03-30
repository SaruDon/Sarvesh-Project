# extract_thursday15.ps1
# Reads raw PCAP files from cicids2018/Thursday-15-02-2018/ (after extracting pcap.zip)
# Extracts network features using tshark -> CSV files in extracted_features/Thursday-15-02-2018/
# Includes BOTH cap* files AND UCAP files (DoS victim is UCAP172.31.69.25)

$tshark   = "C:\Program Files\Wireshark\tshark.exe"
$srcBase  = "C:\Users\Student\cicids2018\Thursday-15-02-2018"
$outBase  = "C:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018"

# Create output dir if missing
if (!(Test-Path $outBase)) { New-Item -ItemType Directory -Path $outBase }

# tshark fields to export (matching the rest of the pipeline)
$fields = @(
    "frame.time_epoch", "ip.src", "ip.dst", "ip.proto", "ip.ttl",
    "tcp.srcport", "tcp.dstport", "tcp.flags", "tcp.window_size_value",
    "udp.srcport", "udp.dstport", "frame.len"
)
$fieldArgs = ($fields | ForEach-Object { "-e $_" }) -join " "

# Search ALL subdirs inside the extracted folder for any pcap/cap/UCAP files
$candidates = Get-ChildItem -Path $srcBase -Recurse -ErrorAction SilentlyContinue |
              Where-Object { !$_.PSIsContainer -and $_.Length -gt 1MB }

Write-Host "Found $($candidates.Count) PCAP candidates in $srcBase" -ForegroundColor Cyan

$done = 0; $skipped = 0; $failed = 0

foreach ($f in $candidates) {
    $safeName = $f.Name -replace '[^\w\.\-]', '_'
    $outCsv = Join-Path $outBase ($safeName + ".csv")

    if ((Test-Path $outCsv) -and (Get-Item $outCsv).Length -gt 1KB) {
        Write-Host "  SKIP (done): $($f.Name)" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    Write-Host "  Extracting: $($f.Name) ($([math]::Round($f.Length/1MB,1)) MB)..." -ForegroundColor Yellow
    try {
        $cmd = "`"$tshark`" -r `"$($f.FullName)`" -T fields -E header=y -E separator=, -E quote=d $fieldArgs > `"$outCsv`""
        cmd /c $cmd
        $done++
    } catch {
        Write-Host "    ERROR: $($f.Name) -> $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "=== Extraction Complete ===" -ForegroundColor Cyan
Write-Host "  Extracted: $done  |  Skipped: $skipped  |  Failed: $failed" -ForegroundColor Green
