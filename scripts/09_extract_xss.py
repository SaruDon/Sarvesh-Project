import subprocess

tshark = r"C:\Program Files\Wireshark\tshark.exe"
files = [
    r"C:\Users\Student\cicids2018\Friday-23-02-2018\pcap\capWIN-J6GMIG1DQE5-172.31.64.120",
    r"C:\Users\Student\cicids2018\Friday-23-02-2018\pcap\capWIN-J6GMIG1DQE5-172.31.65.70"
]

for f in files:
    print(f"Checking {f}")
    cmd = [
        tshark, '-r', f, 
        '-Y', 'frame contains "%3Cscript"',
        '-T', 'fields',

        '-e', 'frame.time_epoch',
        '-e', 'ip.src',
        '-e', 'ip.dst',
        '-e', 'tcp.dstport',
        '-e', 'http.request.uri'
    ]
    try:
        out = subprocess.check_output(cmd, text=True)
        lines = out.strip().split('\n')
        for l in lines[:10]:
            print(l)
    except Exception as e:
        print("Error:", e)
