$msi = "C:\Users\Student\cicids2018\7z.msi"
$target = "C:\Users\Student\cicids2018\7zip"

Write-Host "1. Creating target directory..."
if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target -Force | Out-Null }

Write-Host "2. Extracting MSI locally..."
Start-Process -FilePath "msiexec.exe" -ArgumentList "/a", $msi, "/qb", "TARGETDIR=$target" -Wait

# The 7z.exe binary will be at C:\Users\Student\cicids2018\7zip\Files\7-Zip\7z.exe
$exe7z = "$target\Files\7-Zip\7z.exe"

if (Test-Path $exe7z) {
    Write-Host "3. 7z successfully extracted!"
    Write-Host "4. Empting partial extraction folder..."
    Remove-Item -Recurse -Force "C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap" -ErrorAction SilentlyContinue

    Write-Host "5. Starting High-Speed PCAP extraction..."
    & $exe7z x "C:\Users\Student\cicids2018\Thursday-15-02-2018-pcap.zip" -o"C:\Users\Student\cicids2018\Thursday-15-02-2018" -y
    Write-Host "7z Extraction Complete!"
} else {
    Write-Host "Local Extraction Failed."
}
