import os
import glob

base_dir = r"C:\Users\Student\cicids2018"
days = ["Friday-02-03-2018", "Friday-16-02-2018", "Thursday-01-03-2018"]

print(f"{'Day':<20} | {'UCAP Files Found / Non-standard Files'}")
print("-" * 60)

for day in days:
    day_path = os.path.join(base_dir, day)
    found = []
    if os.path.exists(day_path):
        # Search recursively for UCAP or files with no extension
        for root, dirs, files in os.walk(day_path):
            for file in files:
                if "UCAP" in file or "." not in file:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, day_path)
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    found.append(f"{rel_path} ({size_mb:.2f} MB)")
    else:
        found.append("[Directory not found]")
    
    if not found:
        print(f"{day:<20} | None")
    else:
        print(f"{day:<20} | {', '.join(found)}")

# Also check the root pcap folder one more time for these dates
root_pcap = os.path.join(base_dir, "pcap")
if os.path.exists(root_pcap):
    print("\nChecking root pcap folder for potential matches...")
    for file in os.listdir(root_pcap):
        if "UCAP" in file:
            print(f"Found in root pcap: {file} ({os.path.getsize(os.path.join(root_pcap, file))/(1024*1024):.2f} MB)")
