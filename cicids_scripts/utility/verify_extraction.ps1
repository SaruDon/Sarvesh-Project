# Comprehensive Health Check for Friday-02-03-2018 Extraction
$targetPath = "extracted_features\Friday-02-03-2018"
$expectedCount = 434

Write-Host "--- Starting Extraction Audit for $targetPath ---"

if (!(Test-Path $targetPath)) {
    Write-Error "Directory $targetPath not found!"
    return
}

$files = Get-ChildItem -Path $targetPath -Filter *.csv
$totalFound = $files.Count
$emptyFiles = $files | Where-Object { $_.Length -eq 0 }
$emptyCount = $emptyFiles.Count

# Header and Data Check (Sample 20 random files)
$sampleSize = 20
$randomFiles = $files | Get-Random -Count $sampleSize
$passCount = 0

foreach ($f in $randomFiles) {
    if ($f.Length -lt 200) { continue } # Too small to have data
    $firstLine = Get-Content $f.FullName -TotalCount 1
    if ($firstLine -like '*frame.time_epoch,ip.src,ip.dst*') {
        $passCount++
    }
}

Write-Host "1. Total Files Found: $totalFound / $expectedCount"
Write-Host "2. Empty Files (0 bytes): $emptyCount"
if ($emptyCount -gt 0) {
    Write-Host "   !! Warning: Empty files detected !!"
}

Write-Host "3. Header Validity (Sample $sampleSize): $passCount/$sampleSize Passed"

if ($totalFound -eq $expectedCount -and $emptyCount -eq 0 -and $passCount -eq $sampleSize) {
    Write-Host "`nFINAL STATUS: 100% SUCCESS. Data is ready for Dataset Builder."
} else {
    Write-Host "`nFINAL STATUS: AUDIT FAILED. Please review the errors above."
}
