# extract_wednesday28.ps1
# Extracts tshark network features from Wednesday-28-02-2018 raw PCAP files
# Reads from cicids2018/Wednesday-28-02-2018/pcap/pcap/
# Outputs CSVs to extracted_features/Wednesday-28-02-2018/

$tshark  = "C:\Program Files\Wireshark\tshark.exe"
$srcBase = "C:\Users\Student\cicids2018\Wednesday-28-02-2018\pcap\pcap"
$outBase = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Wednesday-28-02-2018"

if (!(Test-Path $outBase)) { New-Item -ItemType Directory -Path $outBase }

$fields = @(
    "frame.time_epoch","ip.src","ip.dst","ip.proto","ip.ttl",
    "tcp.srcport","tcp.dstport","tcp.flags","tcp.window_size_value",
    "udp.srcport","udp.dstport","frame.len"
)
$fieldArgs = ($fields | ForEach-Object { "-e $_" }) -join " "

$candidates = Get-ChildItem -Path $srcBase -Recurse -ErrorAction SilentlyContinue |
              Where-Object { !$_.PSIsContainer -and $_.Length -gt 1MB }

Write-Host "Found $($candidates.Count) PCAP candidates in Wednesday-28" -ForegroundColor Cyan

$done=0; $skipped=0; $failed=0

foreach ($f in $candidates) {
    if ($f.Extension -eq ".csv" -or $f.Extension -eq ".txt") { continue }
    
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
Write-Host "=== Wednesday-28 Extraction Complete ===" -ForegroundColor Cyan
Write-Host "  Extracted: $done  |  Skipped: $skipped  |  Failed: $failed" -ForegroundColor Green
