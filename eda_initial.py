import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from tqdm import tqdm
from scipy.stats import entropy

# Configuration
EXTRACTED_DATA_DIR = "extracted_features"
OUTPUT_DIR = "analysis_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def analyze_dataset():
    print(f"Searching for extracted features in {EXTRACTED_DATA_DIR}...")
    csv_files = glob.glob(os.path.join(EXTRACTED_DATA_DIR, "*.csv"))
    
    if not csv_files:
        print("No CSV files found. Please run extraction first.")
        return

    for file_path in tqdm(csv_files, desc="Processing files"):
        file_name = os.path.basename(file_path)
        print(f"\nAnalyzing {file_name}...")
        
        try:
            # Load data
            df = pd.read_csv(file_path)
            
            # Basic stats
            print(f"Dataset Shape: {df.shape}")
            print(f"Missing Values:\n{df.isnull().sum()}")
            
            # --- Plotting ---
            
            # 1. Packet Size Distribution
            plt.figure(figsize=(10, 6))
            df['frame.len'].hist(bins=100)
            plt.title(f"Packet Size Distribution - {file_name}")
            plt.xlabel("Packet Size (bytes)")
            plt.ylabel("Count")
            plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_packet_sizes.png"))
            plt.close()

            # 2. Protocol Distribution
            if 'ip.proto' in df.columns:
                plt.figure(figsize=(10, 6))
                # Map common protocols for readability
                proto_map = {6: 'TCP', 17: 'UDP', 1: 'ICMP'}
                mapped_protos = df['ip.proto'].map(lambda x: proto_map.get(x, f'Other({x})'))
                sns.countplot(x=mapped_protos, order=mapped_protos.value_counts().index)
                plt.title(f"Protocol Distribution - {file_name}")
                plt.xlabel("Protocol")
                plt.ylabel("Count")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_protocols.png"))
                plt.close()

            # 3. Time-based features
            if 'frame.time_epoch' in df.columns:
                df['timestamp'] = pd.to_datetime(df['frame.time_epoch'], unit='s', errors='coerce')
                df = df.dropna(subset=['timestamp'])
                df = df.sort_values('timestamp')
                df.set_index('timestamp', inplace=True)
                
                # Packet Rate Analysis
                packet_rate = df.resample('1s').size()
                plt.figure(figsize=(12, 6))
                packet_rate.plot()
                plt.title(f"Packet Rate Analytics - {file_name}")
                plt.ylabel("Packets / Second")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_packet_rate.png"))
                plt.close()

                # Inter-arrival Time
                df['interarrival'] = df.index.to_series().diff().dt.total_seconds()
                plt.figure(figsize=(10, 6))
                df['interarrival'].hist(bins=100)
                plt.title(f"Inter-arrival Time Distribution - {file_name}")
                plt.xlabel("Seconds")
                plt.ylabel("Count")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_interarrival.png"))
                plt.close()
                
                # Flow Duration Distribution (estimate via basic groupby)
                if all(col in df.columns for col in ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport']):
                    df_reset = df.reset_index()
                    df_reset.fillna({'tcp.srcport': 0, 'tcp.dstport': 0}, inplace=True)
                    flows = df_reset.groupby(['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport'])['timestamp']
                    durations = (flows.max() - flows.min()).dt.total_seconds()
                    
                    plt.figure(figsize=(10, 6))
                    durations[durations > 0].hist(bins=100) # Only plot flows > 0s
                    plt.title(f"Flow Duration Distribution - {file_name}")
                    plt.xlabel("Duration (Seconds)")
                    plt.ylabel("Count")
                    plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_flow_duration.png"))
                    plt.close()

                df.reset_index(inplace=True)

            # 4. Top Talkers
            if 'ip.src' in df.columns:
                top_src = df['ip.src'].value_counts().head(20)
                plt.figure(figsize=(12, 6))
                sns.barplot(x=top_src.values, y=top_src.index)
                plt.title(f"Top 20 Source IPs - {file_name}")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_top_src_ips.png"))
                plt.close()
                
            if 'ip.dst' in df.columns:
                top_dst = df['ip.dst'].value_counts().head(20)
                plt.figure(figsize=(12, 6))
                sns.barplot(x=top_dst.values, y=top_dst.index)
                plt.title(f"Top 20 Destination IPs - {file_name}")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_top_dst_ips.png"))
                plt.close()

            # 5. Port Analysis & Entropy
            if 'tcp.dstport' in df.columns:
                top_ports = df['tcp.dstport'].value_counts().head(20)
                plt.figure(figsize=(12, 6))
                sns.barplot(x=top_ports.index, y=top_ports.values)
                plt.title(f"Top 20 Destination Ports - {file_name}")
                plt.xticks(rotation=45)
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_top_ports.png"))
                plt.close()
                
                # Destination Port Entropy over Time
                if 'timestamp' in df.columns:
                    df_ports = df.dropna(subset=['tcp.dstport']).copy()
                    df_ports.set_index('timestamp', inplace=True)
                    # Resample every minute and calculate entropy of port distribution
                    port_entropy = df_ports['tcp.dstport'].resample('1min').apply(
                        lambda x: entropy(x.value_counts(normalize=True)) if not x.empty else 0
                    )
                    plt.figure(figsize=(12, 6))
                    port_entropy.plot()
                    plt.title(f"Destination Port Entropy (1Min Bins) - {file_name}")
                    plt.ylabel("Entropy")
                    plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_port_entropy.png"))
                    plt.close()
                    df_ports.reset_index(inplace=True)

            # 6. TCP Flags Analysis
            if 'tcp.flags' in df.columns:
                plt.figure(figsize=(10, 6))
                sns.countplot(data=df, y='tcp.flags', order=df['tcp.flags'].value_counts().iloc[:10].index)
                plt.title(f"Top 10 TCP Flags - {file_name}")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_tcp_flags.png"))
                plt.close()

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    analyze_dataset()
