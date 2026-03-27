import os
import shutil

base_dir = r"C:\Users\Student\cicids2018"

# 1. ZIP files to delete (Already processed and verified)
zips_to_delete = [
    "Friday-16-02-2018-pcap.zip",
    "Friday-23-02-2018-pcap.zip",
    "Thursday-01-03-2018-pcap.zip",
    "Thursday-15-02-2018-pcap.zip",
    "Thursday-22-02-2018-pcap.zip", # Assuming processed or redundant
]

# 2. Extracted directories to delete
dirs_to_delete = [
    "Thursday-01-03-2018",
    "Thursday-01-03-2018_v2",
    "Thursday-15-02-2018",
    "Friday-23-02-2018", # If it exists
    "extracted_logs",
    "Friday_Logs",
    "logs"
]

print("Starting Cleanup...")

total_reclaimed = 0

# Delete ZIPs
for z in zips_to_delete:
    path = os.path.join(base_dir, z)
    if os.path.exists(path):
        size = os.path.getsize(path)
        try:
            os.remove(path)
            total_reclaimed += size
            print(f"Deleted ZIP: {z} ({size / (1024**3):.2f} GB)")
        except Exception as e:
            print(f"Error deleting {z}: {e}")

# Delete Directories
for d in dirs_to_delete:
    path = os.path.join(base_dir, d)
    if os.path.exists(path):
        # Calculate size first
        dir_size = 0
        for root, _, files in os.walk(path):
            for f in files:
                dir_size += os.path.getsize(os.path.join(root, f))
        try:
            shutil.rmtree(path)
            total_reclaimed += dir_size
            print(f"Deleted Directory: {d} ({dir_size / (1024**3):.2f} GB)")
        except Exception as e:
            print(f"Error deleting directory {d}: {e}")

print(f"\nCleanup Complete. Total Space Reclaimed: {total_reclaimed / (1024**3):.2f} GB")
