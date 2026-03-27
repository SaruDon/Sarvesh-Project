import subprocess
import os

tshark = r"C:\Program Files\Wireshark\tshark.exe"

segments = [
    # Thursday-15-02-2018 (Remaining small segments)
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.15", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.15.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.18", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.18.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.21", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.21.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.22", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.22.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.27", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.27.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-15-02-2018\pcap\UCAP172.31.69.7", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-15-02-2018\UCAP172.31.69.7.csv"),
    
    # Thursday-01-03-2018 (Lateral movement / hidden segments)
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.15", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.15.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.18", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.18.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.21", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.21.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.22", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.22.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.25", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.25.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.27", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.27.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.28", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.28.csv"),
    (r"C:\Users\Student\cicids2018\Thursday-01-03-2018\pcap\UCAP172.31.69.7", r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Thursday-01-03-2018\UCAP172.31.69.7.csv"),
]

for src, dst in segments:
    if not os.path.exists(src):
        continue
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print(f"Extracting {os.path.basename(src)} -> {dst}...")
    cmd = [
        tshark, "-r", src, "-T", "fields",
        "-e", "frame.time_epoch", "-e", "ip.src", "-e", "ip.dst", "-e", "tcp.srcport", "-e", "tcp.dstport",
        "-e", "frame.len", "-e", "ip.proto", "-e", "tcp.flags", "-e", "udp.srcport", "-e", "udp.dstport",
        "-e", "ip.ttl", "-e", "tcp.window_size_value",
        "-E", "header=y", "-E", "separator=,", "-E", "quote=d"
    ]
    with open(dst, "w", encoding="utf8") as f:
        subprocess.run(cmd, stdout=f)

print("Batch Extraction Complete.")
