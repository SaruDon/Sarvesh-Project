# download_missing.ps1 - Resume/download missing CIC-IDS-2018 dataset files
# Uses aria2c with --continue flag to resume from last checkpoint
# Skips files that already exist and are complete (no .aria2 sidecar)
#
# SMART SKIP LOGIC:
#   - Friday-16-02-2018: processed_dataset exists -> SKIP
#   - Friday-23-02-2018: processed_dataset exists -> SKIP
#   - Friday-02-03-2018: processed_dataset exists -> SKIP
#   - Thursday-15-02-2018: pcap.zip (41GB) already downloaded -> SKIP pcap, get logs
#   - Thursday-22-02-2018: pcap.zip (46GB) already downloaded -> SKIP
#   - Tuesday-20-02-2018:  pcap.rar (41GB) already downloaded -> SKIP
#   - Wednesday-14-02-2018: processed_dataset exists -> SKIP
#   - Wednesday-21-02-2018: processed_dataset exists -> SKIP
#   - Wednesday-28-02-2018: no special skip (logs+pcap needed)
#   - Thursday-01-03-2018: NO PCAP -> MUST DOWNLOAD

$DOWNLOAD_DIR = "C:\Users\Student\cicids2018"
$BASE_HTTP = "https://cse-cic-ids2018.s3.amazonaws.com/Original%20Network%20Traffic%20and%20Log%20data"

# Only days that still need downloading based on SMART SKIP LOGIC
$datasets = @(
    @{ Name = "Thursday-15-02-2018"; GetPcap = $true; GetLogs = $false }
)

function Is-FileComplete {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        # Check for aria2 sidecar (means download was interrupted)
        if (Test-Path "$FilePath.aria2") { return $false }
        if ((Get-Item $FilePath).Length -gt 0) { return $true }
    }
    # Check for temp fragment files from interrupted aria2 downloads
    $parentDir = Split-Path $FilePath -Parent
    $baseName = Split-Path $FilePath -Leaf
    $fragments = Get-ChildItem -Path $parentDir -Filter "$baseName.*" -ErrorAction SilentlyContinue |
                 Where-Object { $_.Extension -match '^\.[a-zA-Z0-9]{8}$' }
    if ($fragments.Count -gt 0) { return $false }
    return $false
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  CIC-IDS-2018 Download Manager (Resume)    " -ForegroundColor Cyan
Write-Host "  Target: $DOWNLOAD_DIR                      " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check aria2c is available
if (-not (Get-Command aria2c -ErrorAction SilentlyContinue)) {
    Write-Error "aria2c not found! Please install aria2 and add to PATH."
    exit 1
}

if (-not (Test-Path $DOWNLOAD_DIR)) {
    New-Item -ItemType Directory -Path $DOWNLOAD_DIR -Force | Out-Null
}

$skipped = 0
$downloaded = 0
$failed = 0
$resumed = 0

foreach ($ds in $datasets) {
    $dayName = $ds.Name
    Write-Host "--- $dayName ---" -ForegroundColor Yellow
    
    # ========== LOGS ==========
    if ($ds.GetLogs -eq $false) {
        Write-Host "  SKIP: Logs (per smart logic)" -ForegroundColor Cyan
    } else {
        $localLog = Join-Path $DOWNLOAD_DIR "$dayName-logs.zip"
        $logUrl = "$BASE_HTTP/$dayName/logs.zip"
        
        if (Is-FileComplete $localLog) {
            $sizeMB = [math]::Round((Get-Item $localLog).Length / 1MB, 1)
            Write-Host "  SKIP: $dayName-logs.zip (${sizeMB} MB, complete)" -ForegroundColor Green
            $skipped++
        } else {
            $isResume = (Test-Path $localLog) -or (Test-Path "$localLog.aria2")
            if ($isResume) {
                Write-Host "  RESUME: $dayName-logs.zip ..." -ForegroundColor Magenta
                $resumed++
            } else {
                Write-Host "  DOWNLOAD: $dayName-logs.zip ..." -ForegroundColor White
            }
            
            & aria2c --continue=true `
                     --dir="$DOWNLOAD_DIR" `
                     --out="$dayName-logs.zip" `
                     --max-connection-per-server=8 `
                     --split=8 `
                     --min-split-size=10M `
                     --file-allocation=none `
                     --auto-file-renaming=false `
                     --allow-overwrite=false `
                     "$logUrl"
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  DONE: $dayName-logs.zip" -ForegroundColor Green
                $downloaded++
            } else {
                Write-Host "  FAILED: $dayName-logs.zip (exit: $LASTEXITCODE)" -ForegroundColor Red
                $failed++
            }
        }
    } # End Logs
    
    # ========== PCAP ==========
    if ($ds.GetPcap -eq $false) {
        Write-Host "  SKIP: PCAP (per smart logic)" -ForegroundColor Cyan
    } else {
        # Try both .zip and .rar extensions; S3 filenames are just "pcap.zip" or "pcap.rar"
        $localPcapZip = Join-Path $DOWNLOAD_DIR "$dayName-pcap.zip"
        $localPcapRar = Join-Path $DOWNLOAD_DIR "$dayName-pcap.rar"
        
        # Check if either complete pcap already exists
        if ((Is-FileComplete $localPcapZip) -or (Is-FileComplete $localPcapRar)) {
            $existingFile = if (Is-FileComplete $localPcapZip) { $localPcapZip } else { $localPcapRar }
            $sizeMB = [math]::Round((Get-Item $existingFile).Length / 1MB, 1)
            $existName = Split-Path $existingFile -Leaf
            Write-Host "  SKIP: $existName (${sizeMB} MB, complete)" -ForegroundColor Green
            $skipped++
        } else {
            # Determine which extension to try
            $pcapExtensions = @("zip", "rar")
            $downloadedPcap = $false
            
            foreach ($ext in $pcapExtensions) {
                $localPcap = Join-Path $DOWNLOAD_DIR "$dayName-pcap.$ext"
                $pcapUrl = "$BASE_HTTP/$dayName/pcap.$ext"
                
                $hasPartial = (Test-Path $localPcap) -or (Test-Path "$localPcap.aria2")
                $tempFragments = Get-ChildItem -Path $DOWNLOAD_DIR -Filter "$dayName-pcap.$ext.*" -ErrorAction SilentlyContinue
                if ($tempFragments.Count -gt 0) { $hasPartial = $true }
                
                if ($hasPartial) {
                    Write-Host "  RESUME: $dayName-pcap.$ext (continuing from checkpoint)..." -ForegroundColor Magenta
                    $resumed++
                } else {
                    Write-Host "  TRYING: $dayName-pcap.$ext ..." -ForegroundColor White
                }
                
                & aria2c --continue=true `
                         --dir="$DOWNLOAD_DIR" `
                         --out="$dayName-pcap.$ext" `
                         --max-connection-per-server=8 `
                         --split=8 `
                         --min-split-size=10M `
                         --file-allocation=none `
                         --auto-file-renaming=false `
                         --allow-overwrite=false `
                         "$pcapUrl"
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  DONE: $dayName-pcap.$ext" -ForegroundColor Green
                    $downloaded++
                    $downloadedPcap = $true
                    break
                }
            }
            
            if (-not $downloadedPcap) {
                Write-Host "  FAILED: No PCAP found for $dayName (tried .zip and .rar)" -ForegroundColor Red
                $failed++
            }
        }
    } # End PCAP
    
    Write-Host ""
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Summary:" -ForegroundColor Cyan
Write-Host "    Skipped (complete):  $skipped" -ForegroundColor Green
Write-Host "    Downloaded:          $downloaded" -ForegroundColor White
Write-Host "    Resumed:             $resumed" -ForegroundColor Magenta
Write-Host "    Failed:              $failed" -ForegroundColor Red
Write-Host "=============================================" -ForegroundColor Cyan
