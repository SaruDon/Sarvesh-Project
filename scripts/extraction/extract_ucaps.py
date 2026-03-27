import os
import subprocess
import glob

INPUT_DIR = r"C:\Users\Student\cicids2018\pcap"
OUTPUT_DIR = r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Wednesday-14-02-2018"
TSHARK_PATH = r"C:\Program Files\Wireshark\tshark.exe"

os.makedirs(OUTPUT_DIR, exist_ok=True)

ucaps = glob.glob(os.path.join(INPUT_DIR, "UCAP*"))
print(f"Found {len(ucaps)} UCAP files.")

for pcap in ucaps:
    basename = os.path.basename(pcap)
    target_csv = os.path.join(OUTPUT_DIR, f"{basename}.csv")
    
    print(f"Processing {basename}...")
    
    cmd = [
        TSHARK_PATH, "-r", pcap, "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "ip.src", "-e", "ip.dst",
        "-e", "tcp.srcport", "-e", "tcp.dstport",
        "-e", "frame.len", "-e", "ip.proto", "-e", "tcp.flags",
        "-e", "udp.srcport", "-e", "udp.dstport",
        "-e", "ip.ttl", "-e", "tcp.window_size_value",
        "-E", "header=y", "-E", "separator=,", "-E", "quote=d"
    ]
    
    try:
        with open(target_csv, "w", encoding="utf-8") as f:
            subprocess.run(cmd, stdout=f, check=True)
    except Exception as e:
        print(f"Error processing {basename}: {e}")

print("Batch UCAP extraction finished.")
