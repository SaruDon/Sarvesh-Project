import subprocess
import os
from datetime import datetime, timezone

tshark = r"C:\Program Files\Wireshark\tshark.exe"
base_dir = r"C:\Users\Student\cicids2018"

print(f"{'File Path':<80} | {'Date (UTC)':<20} | {'Size (MB)'}")
print("-" * 115)

# Find all files with UCAP or no extension recursively
for root, dirs, files in os.walk(base_dir):
    # Skip processed_dataset to avoid circular finds
    if "processed_dataset" in root or ".gemini" in root:
        continue
    
    for file in files:
        # Check for UCAP or potential extensionless pcaps (larger than 1MB)
        if "UCAP" in file or ("." not in file and os.path.getsize(os.path.join(root, file)) > 1024*1024):
            full_path = os.path.join(root, file)
            try:
                # Use tshark to get first timestamp
                cmd = [tshark, "-r", full_path, "-T", "fields", "-e", "frame.time_epoch", "-c", "1"]
                out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
                if out:
                    ts = float(out)
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    size = os.path.getsize(full_path) / (1024*1024)
                    rel_path = os.path.relpath(full_path, base_dir)
                    print(f"{rel_path:<80} | {dt.strftime('%Y-%m-%d %H:%M:%S')} | {size:.2f}")
            except:
                pass
