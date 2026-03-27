import os

base_dir = r"C:\Users\Student\cicids2018\pcap"
print(f"Cleaning up {base_dir}...")

reclaimed = 0
for file in os.listdir(base_dir):
    if file.startswith("cap") and "UCAP" not in file:
        full_path = os.path.join(base_dir, file)
        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            try:
                os.remove(full_path)
                reclaimed += size
                print(f"Deleted root segment: {file} ({size / (1024**3):.2f} GB)")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

print(f"Cleanup complete. Reclaimed {reclaimed / (1024**3):.2f} GB from root pcap folder.")
