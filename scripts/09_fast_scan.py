import os
import glob
import time

def scan_pcaps():
    pcap_dir = "C:/Users/Student/cicids2018/Friday-23-02-2018/pcap"
    files = glob.glob(os.path.join(pcap_dir, "*.pcap")) + glob.glob(os.path.join(pcap_dir, "cap*"))
    
    signatures = [b"UNION SELECT", b"%3Cscript", b"sqlmap"]
    
    print(f"Scanning {len(files)} files for definitive signatures: {signatures}")
    found_files = set()
    start_time = time.time()
    
    for f in files:
        if not os.path.isfile(f): continue
        try:
            with open(f, "rb") as file:
                chunk_size = 10 * 1024 * 1024
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    
                    for sig in signatures:
                        if sig in chunk:
                            print(f"[!] Signature {sig} found in {os.path.basename(f)}")
                            found_files.add(f)
                            break
                    
                    if f in found_files:
                        break
        except Exception as e:
            pass
            
    print(f"Scan complete in {time.time() - start_time:.2f} seconds.")
    print(f"Found {len(found_files)} files containing attacks.")

if __name__ == "__main__":
    scan_pcaps()
