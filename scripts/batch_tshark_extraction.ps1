$days = @("Wednesday-21-02-2018", "Thursday-15-02-2018")
$basePath = "c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features"
$tshark = "C:\Program Files\Wireshark\tshark.exe"

foreach ($day in $days) {
    $dayPath = Join-Path $basePath $day
    if (!(Test-Path $dayPath)) { New-Item -ItemType Directory -Path $dayPath }
    
    $files = Get-ChildItem -Path $dayPath -Filter "cap*"
    Write-Host "Processing ${day}: $($files.Count) files..."
    
    foreach ($f in $files) {
        $out = $f.FullName + ".csv"
        if ($f.Length -gt 1MB) {
            Write-Host "  Extracting $($f.Name)..."
            try {
                $cmd = "`"C:\Program Files\Wireshark\tshark.exe`" -r `"$($f.FullName)`" -T fields -E header=y -E separator=, -E quote=d -e frame.time_epoch -e ip.src -e ip.dst -e ip.proto -e ip.ttl -e tcp.srcport -e tcp.dstport -e tcp.flags -e tcp.window_size_value -e udp.srcport -e udp.dstport -e frame.len > `"$out`""
                cmd /c $cmd
            } catch {
                Write-Host "    Error on $($f.Name): $_"
            }
        }
    }
}
