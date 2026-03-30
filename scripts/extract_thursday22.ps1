# extract_thursday22.ps1
# Extracts tshark network features from Thursday-22-02-2018 raw PCAP files
# Reads from cicids2018/Thursday-22-02-2018/ after pcap.zip is extracted
# Outputs CSVs to extracted_features/Thursday-22-02-2018/
# Includes cap* AND UCAP* files. Skips already-done CSVs.

$tshark  = "C:\Program Files\Wireshark\tshark.exe"
$srcBase = "C:\Users\Student\cicids2018\Thursday-22-02-2018"
$outBase = "C:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-22-02-2018"

if (!(Test-Path $outBase)) { New-Item -ItemType Directory -Path $outBase }

$fields = @(
    "frame.time_epoch","ip.src","ip.dst","ip.proto","ip.ttl",
    "tcp.srcport","tcp.dstport","tcp.flags","tcp.window_size_value",
    "udp.srcport","udp.dstport","frame.len"
)
$fieldArgs = ($fields | ForEach-Object { "-e $_" }) -join " "

$candidates = Get-ChildItem -Path $srcBase -Recurse -ErrorAction SilentlyContinue |
              Where-Object { !$_.PSIsContainer -and $_.Length -gt 1MB }

Write-Host "Found $($candidates.Count) PCAP candidates in Thursday-22" -ForegroundColor Cyan

$done=0; $skipped=0; $failed=0

foreach ($f in $candidates) {
    $safeName = $f.Name -replace '[^\w\.\-]','_'
    $outCsv = Join-Path $outBase ($safeName + ".csv")

    if ((Test-Path $outCsv) -and (Get-Item $outCsv).Length -gt 1KB) {
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
Write-Host "=== Thursday-22 Extraction Complete ===" -ForegroundColor Cyan
Write-Host "  Extracted: $done  |  Skipped: $skipped  |  Failed: $failed" -ForegroundColor Green
