Write-Host '1. Stopping slow Expand-Archive process...'
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match 'Expand-Archive' -and $_.ProcessId -ne $PID } | ForEach-Object { Stop-Process $_.ProcessId -Force }

Write-Host '2. Downloading 7-Zip MSI installer...'
$installer = "C:\Users\Student\cicids2018\7z.msi"
Invoke-WebRequest -Uri "https://www.7-zip.org/a/7z2405-x64.msi" -OutFile $installer

Write-Host '3. Installing 7-Zip silently...'
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $installer, "/qn" -Wait

if (Test-Path "C:\Program Files\7-Zip\7z.exe") {
    Write-Host '4. Re-initializing extraction folder...'
    Remove-Item -Recurse -Force "C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap" -ErrorAction SilentlyContinue

    Write-Host '5. Extracting 41GB PCAP using 7z...'
    & "C:\Program Files\7-Zip\7z.exe" x "C:\Users\Student\cicids2018\Thursday-15-02-2018-pcap.zip" -o"C:\Users\Student\cicids2018\Thursday-15-02-2018" -y
    Write-Host '7z Extraction Complete!'
} else {
    Write-Host '7z Installation failed!'
}
