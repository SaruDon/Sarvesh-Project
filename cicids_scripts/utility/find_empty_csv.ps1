$targetPath = "extracted_features\Friday-02-03-2018"
$emptyFiles = Get-ChildItem -Path $targetPath -Filter *.csv | Where-Object { $_.Length -eq 0 }
foreach ($f in $emptyFiles) {
    Write-Host "Found empty file: $($f.Name)"
    $pcapName = $f.Name.Replace(".csv", "")
    Write-Host "Corresponding PCAP: $pcapName"
}
