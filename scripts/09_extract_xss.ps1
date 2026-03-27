$TSHARK = "C:\Program Files\Wireshark\tshark.exe"
$files = @(
    "C:\Users\Student\cicids2018\Friday-23-02-2018\pcap\capWIN-J6GMIG1DQE5-172.31.64.120",
    "C:\Users\Student\cicids2018\Friday-23-02-2018\pcap\capWIN-J6GMIG1DQE5-172.31.65.70"
)

foreach ($f in $files) {
    Write-Host "Checking $f"
    & $TSHARK -r $f -Y "http.request.uri contains '%3Cscript'" -T fields -e frame.time_epoch -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e http.request.uri | Select-Object -First 5
}
