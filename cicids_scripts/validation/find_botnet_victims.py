import pandas as pd
import os
import glob
from tqdm import tqdm

def find_botnet(day_dir):
    files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
    target_date = pd.to_datetime("2018-03-02").date()
    # Attack 1: 14:00 - 15:00 UTC
    # Attack 2: 18:00 - 19:00 UTC
    
    potential_victims = {}
    
    print("Searching for Botnet C2 traffic (Ports 8080, 8081, 10000, 10443)...")
    
    for f in tqdm(files, desc="Checking files"):
        # We need ports and IPs
        df = pd.read_parquet(f)
        if df['timestamp_min'].iloc[0].date() != target_date: continue
        
        # Ares Botnet often uses these
        c2_ports = [8080, 8081, 10000, 10443]
        mask = (df['tcp.dstport'].isin(c2_ports)) | (df['tcp.srcport'].isin(c2_ports))
        
        # Filter by time window (just to be sure)
        # mask = mask & (((df['timestamp_min'].dt.hour == 14) | (df['timestamp_min'].dt.hour == 18)))
        
        bot_traffic = df[mask]
        if not bot_traffic.empty:
            for _, row in bot_traffic.iterrows():
                # One is internal, one is external usually
                for ip in [row['ip.src'], row['ip.dst']]:
                    if ip.startswith('172.31.'):
                        potential_victims[ip] = potential_victims.get(ip, 0) + 1

    print("\nPotential Victim IPs (based on C2 port activity):")
    sorted_victims = sorted(potential_victims.items(), key=lambda x: x[1], reverse=True)
    for ip, count in sorted_victims[:10]:
        print(f"  {ip}: {count} C2-port flows")

if __name__ == "__main__":
    find_botnet("processed_dataset/Friday-02-03-2018")
