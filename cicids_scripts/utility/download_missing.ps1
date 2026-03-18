# CIC-IDS-2018 Missing Data Downloader (PowerShell)
$DATASET_DIR = "C:\Users\Student\cicids2018"
$BASE_HTTP = "https://cse-cic-ids2018.s3.amazonaws.com/Original%20Network%20Traffic%20and%20Log%20data"
$BASE_S3 = "s3://cse-cic-ids2018/Original Network Traffic and Log data"

$folders = @(
    "Friday-02-03-2018",
    "Friday-16-02-2018",
    "Friday-23-02-2018",
    "Thursday-01-03-2018",
    "Thursday-15-02-2018",
    "Thursday-22-02-2018",
    "Tuesday-20-02-2018",
    "Wednesday-14-02-2018",
    "Wednesday-21-02-2018",
    "Wednesday-28-02-2018"
)

# PCAP file mapping (some use rar, most use zip)
$pcap_map = @{
    "Tuesday-20-02-2018" = "pcap.rar"
}

if (!(Test-Path $DATASET_DIR)) { New-Item -ItemType Directory -Path $DATASET_DIR }

foreach ($f in $folders) {
    echo "--- Processing $f ---"
    
    # 1. Determine PCAP filename
    $pcap_name = "pcap.zip"
    if ($pcap_map.ContainsKey($f)) { $pcap_name = $pcap_map[$f] }
    
    $local_pcap = "$f-$pcap_name"
    $target_pcap = Join-Path $DATASET_DIR $local_pcap
    $url = "$BASE_HTTP/$f/$pcap_name"

    # Special handling for Tuesday partials if they exist under generic names
    if ($f -eq "Tuesday-20-02-2018") {
        if (!(Test-Path $target_pcap) -and (Test-Path (Join-Path $DATASET_DIR "pcap.rar"))) {
            echo "Renaming generic pcap.rar to Tuesday-20-02-2018-pcap.rar"
            Move-Item (Join-Path $DATASET_DIR "pcap.rar") $target_pcap
            if (Test-Path (Join-Path $DATASET_DIR "pcap.rar.aria2")) {
                Move-Item (Join-Path $DATASET_DIR "pcap.rar.aria2") "$target_pcap.aria2"
            }
        }
    }

    # Download PCAP
    if (Test-Path $target_pcap) {
        if (Test-Path "$target_pcap.aria2") {
            echo "Resuming $local_pcap..."
            aria2c -c -x 8 -s 8 -d $DATASET_DIR -o $local_pcap $url
        } else {
            echo "SKIP: $local_pcap already exists."
        }
    } else {
        echo "Downloading $local_pcap..."
        aria2c -c -x 8 -s 8 -d $DATASET_DIR -o $local_pcap $url
    }

    # 2. Download logs.zip
    $local_log = "$f-logs.zip"
    $target_log = Join-Path $DATASET_DIR $local_log
    if (!(Test-Path $target_log)) {
        echo "Downloading $local_log from S3..."
        aws s3 cp --no-sign-request "$BASE_S3/$f/logs.zip" $target_log
    } else {
        echo "SKIP: $local_log already exists."
    }
}
