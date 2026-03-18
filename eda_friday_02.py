import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from tqdm import tqdm

# Configuration
DATA_DIR = "processed_dataset/Friday-02-03-2018"
OUTPUT_DIR = "analysis_results/Friday-02-03-2018"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_eda():
    flow_files = glob.glob(os.path.join(DATA_DIR, "*_flows.parquet"))
    
    if not flow_files:
        print(f"No flow files found in {DATA_DIR}.")
        return

    print(f"Found {len(flow_files)} files. Aggregating summary statistics...")
    
    all_summaries = []
    daily_timeline = []
    
    # Identify label column name (could be label_<lambda>)
    sample_df = pd.read_parquet(flow_files[0], columns=['timestamp_min'])
    label_col = [c for c in pd.read_parquet(flow_files[0]).columns if 'label' in c][0]

    for f in tqdm(flow_files, desc="Processing files"):
        df = pd.read_parquet(f)
        
        # 1. Timeline Data (Packets per minute)
        df['timestamp'] = pd.to_datetime(df['timestamp_min'])
        timeline = df.set_index('timestamp').resample('1min')['frame.len_count'].sum().reset_index()
        daily_timeline.append(timeline)
        
        # 2. Label Counts
        counts = df[label_col].value_counts().reset_index()
        counts.columns = ['label', 'count']
        counts['file'] = os.path.basename(f)
        all_summaries.append(counts)

    # Combine Data
    summary_df = pd.concat(all_summaries)
    timeline_df = pd.concat(daily_timeline).groupby('timestamp')['frame.len_count'].sum().reset_index()
    
    print("\nGenerating Plots...")

    # 1. Label Distribution Plot
    plt.figure(figsize=(10, 6))
    total_labels = summary_df.groupby('label')['count'].sum().reset_index()
    sns.barplot(data=total_labels, x='label', y='count', palette='viridis')
    plt.yscale('log')
    plt.title("Friday-02-03-2018: Label Distribution (Log Scale)")
    plt.ylabel("Total Flows")
    plt.savefig(os.path.join(OUTPUT_DIR, "label_distribution.png"))
    plt.close()

    # 2. Traffic Timeline Plot
    plt.figure(figsize=(15, 6))
    plt.plot(timeline_df['timestamp'], timeline_df['frame.len_count'], color='blue', alpha=0.7)
    plt.title("Friday-02-03-2018: Traffic Volume Over Time (UTC)")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Packets per Minute")
    plt.grid(True, alpha=0.3)
    
    # Highlight Attack Windows (calculated earlier as 14:02-15:02 and 18:00-19:00 UTC)
    plt.axvspan(pd.to_datetime("2018-03-02 14:02"), pd.to_datetime("2018-03-02 15:02"), color='red', alpha=0.2, label='Botnet Window 1')
    plt.axvspan(pd.to_datetime("2018-03-02 18:00"), pd.to_datetime("2018-03-02 19:00"), color='red', alpha=0.2, label='Botnet Window 2')
    plt.legend()
    
    plt.savefig(os.path.join(OUTPUT_DIR, "traffic_timeline.png"))
    plt.close()

    # 3. Numeric Summary Report
    with open(os.path.join(OUTPUT_DIR, "summary_report.txt"), "w") as f:
        f.write("Friday-02-03-2018 Processing Summary\n")
        f.write("====================================\n")
        f.write(f"Total Files: {len(flow_files)}\n")
        f.write(f"Total Label Distribution:\n{total_labels.to_string()}\n")
        
    print(f"EDA complete. Results saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_eda()
