import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from tqdm import tqdm
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Configuration
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "processed_dataset")
if len(sys.argv) > 1:
    PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "processed_dataset", sys.argv[1])
    OUTPUT_DIR = os.path.join(BASE_DIR, "analysis_results", sys.argv[1])
else:
    OUTPUT_DIR = os.path.join(BASE_DIR, "analysis_results", "advanced_eda")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_advanced_eda():
    print(f"Searching for processed Parquet files in {PROCESSED_DATA_DIR}...")
    
    # We focus on _flows.parquet for statistical EDA
    parquet_files = []
    for root, _, files in os.walk(PROCESSED_DATA_DIR):
        for f in files:
            if f.endswith("_flows.parquet"):
                parquet_files.append(os.path.join(root, f))
    
    if not parquet_files:
        print("No processed flows found. Please run dataset_builder.py first.")
        return

    print(f"Found {len(parquet_files)} flow files. Loading data...")
    all_dfs = []
    for f in tqdm(parquet_files, desc="Loading data"):
        all_dfs.append(pd.read_parquet(f))
    
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Handle lambda-named label column if necessary
    if 'label_<lambda>' in df.columns:
        df = df.rename(columns={'label_<lambda>': 'label'})
    
    print(f"Total rows for analysis: {len(df)}")
    print(f"Labels found: {df['label'].unique()}")

    # 1. Label Distribution
    plt.figure(figsize=(10, 6))
    df['label'].value_counts().plot(kind='bar')
    plt.title("Overall Label Distribution")
    plt.yscale('log')
    plt.ylabel("Count (Log Scale)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "label_distribution.png"))
    plt.close()

    # 2. Feature distributions by Label (Boxplots)
    features_to_plot = ['frame.len_mean', 'flow_duration_sec', 'packet_rate', 'ip.ttl_mean']
    for feat in features_to_plot:
        if feat in df.columns:
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df, x='label', y=feat)
            plt.title(f"{feat} Distribution by Label")
            plt.xticks(rotation=45)
            plt.yscale('log') if df[feat].max() > 1000 else None
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, f"dist_{feat.replace('.', '_')}.png"))
            plt.close()

    # 3. Correlation Heatmap (Numeric features only)
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        plt.figure(figsize=(12, 10))
        corr = numeric_df.corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap='coolwarm', center=0)
        plt.title("Feature Correlation Heatmap")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "correlation_heatmap.png"))
        plt.close()

    # 4. Time-Series Attack Spikes
    if 'timestamp_min' in df.columns:
        df['dt'] = pd.to_datetime(df['timestamp_min'])
        df_sorted = df.sort_values('dt')
        
        # Resample by minute and plot
        plt.figure(figsize=(15, 7))
        for label in df['label'].unique():
            subset = df_sorted[df_sorted['label'] == label]
            if not subset.empty:
                subset.set_index('dt')['frame.len_count'].resample('1min').sum().plot(label=label)
        
        plt.title("Traffic Intensity (Packet Counts) Over Time by Label")
        plt.ylabel("Total Packets per Minute")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "traffic_spikes_over_time.png"))
        plt.close()

    # 5. Dimensionality Reduction (PCA)
    print("Running PCA...")
    features = df.select_dtypes(include=[np.number]).dropna(axis=1)
    # Use a sample if too large
    if len(df) > 50000:
        sample_df = df.sample(50000, random_state=42)
    else:
        sample_df = df
        
    X = sample_df[features.columns].fillna(0)
    y = sample_df['label']
    
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=components[:, 0], y=components[:, 1], hue=y, alpha=0.5)
    plt.title(f"PCA 2D Cluster Analysis (Variance Explained: {sum(pca.explained_variance_ratio_):.2f})")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "pca_clusters.png"))
    plt.close()

    print(f"Analysis complete. Results ready in {OUTPUT_DIR}")

if __name__ == "__main__":
    run_advanced_eda()
