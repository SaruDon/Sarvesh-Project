import subprocess
import os

tshark = r"C:\Program Files\Wireshark\tshark.exe"

files_to_extract = [
    # (Source, Destination)
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.25", 
     r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.25.csv"),
    
    (r"C:\Users\Student\cicids2018\pcap\UCAP172.31.69.28", 
     r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Friday-23-02-2018\UCAP172.31.69.28.csv"),
    
    (r"C:\Users\Student\cicids2018\pcap\UCAP172.31.69.25", 
     r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Friday-23-02-2018\UCAP172.31.69.25.csv")
]

for src, dst in files_to_extract:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print(f"Extracting {os.path.basename(src)} -> {os.path.basename(dst)}...")
    cmd = [
        tshark, "-r", src, "-T", "fields",
        "-e", "frame.time_epoch", "-e", "ip.src", "-e", "ip.dst", "-e", "tcp.srcport", "-e", "tcp.dstport",
        "-e", "frame.len", "-e", "ip.proto", "-e", "tcp.flags", "-e", "udp.srcport", "-e", "udp.dstport",
        "-e", "ip.ttl", "-e", "tcp.window_size_value",
        "-E", "header=y", "-E", "separator=,", "-E", "quote=d"
    ]
    with open(dst, "w", encoding="utf8") as f:
        subprocess.run(cmd, stdout=f)
    print(f"Done: {dst}")
