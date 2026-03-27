$ucapPath = "C:\Users\Student\cicids2018"
$outputPath = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018"
$tshark = "C:\Program Files\Wireshark\tshark.exe"

if (!(Test-Path $outputPath)) { New-Item -ItemType Directory -Path $outputPath }

$files = Get-ChildItem -Path $ucapPath -Filter "UCAP*"
foreach ($f in $files) {
    # Check if this matches Feb 15 (GoldenEye/Slowloris)
    # Note: Feb 15 target was 172.31.69.25
    # We already checked these UCAPs, let's see which ones are Feb 15.
    $out = Join-Path $outputPath ($f.Name + ".csv")
    if (!(Test-Path $out)) {
        Write-Host "Processing $($f.Name)..."
        try {
            & $tshark -r $f.FullName -T fields -E header=y -E separator=, -E quote=d -e frame.time_epoch -e ip.src -e ip.dst -e ip.proto -e ip.ttl -e tcp.srcport -e tcp.dstport -e tcp.flags -e tcp.window_size_value -e udp.srcport -e udp.dstport -e frame.len > $out
        } catch {
            Write-Host "Error processing $($f.Name): $_"
        }
    } else {
        Write-Host "Skipping $($f.Name) (exists)"
    }
}
