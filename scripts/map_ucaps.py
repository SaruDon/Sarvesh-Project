import subprocess
import os
import glob
from datetime import datetime, timezone

tshark = r"C:\Program Files\Wireshark\tshark.exe"
pcap_dir = r"C:\Users\Student\cicids2018\pcap"
files = glob.glob(os.path.join(pcap_dir, "*UCAP*"))

print(f"Mapping {len(files)} UCAP files...")

for f in files:
    try:
        # Get first timestamp
        cmd = [tshark, "-r", f, "-T", "fields", "-e", "frame.time_epoch", "-c", "1"]
        out = subprocess.check_output(cmd, text=True).strip()
        if out:
            ts = float(out)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            size = os.path.getsize(f) / (1024*1024)
            print(f"{os.path.basename(f)}: {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC, Size: {size:.2f} MB")
    except Exception as e:
        print(f"Error mapping {f}: {e}")
