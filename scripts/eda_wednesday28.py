import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import glob
import os

def run_detailed_eda(target_day):
    print(f"\n=====================================")
    print(f"Starting DETAILED EDA for {target_day}")
    print(f"=====================================")
    
    output_dir = f"analysis_results/{target_day}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    path = f"processed_dataset/{target_day}/*_flows.parquet"
    files = glob.glob(path)
    if not files:
        print(f"No valid flow parquets found for {target_day}")
        return

    benign_dfs = []
    attack_dfs = []

    # Sample data to avoid memory issues while ensuring we see attacks
    for f in sorted(files, key=os.path.getsize, reverse=True):
        df = pd.read_parquet(f)
        label_col = 'label'
        if label_col not in df.columns and 'label_<lambda>' in df.columns:
            label_col = 'label_<lambda>'
            df = df.rename(columns={'label_<lambda>': 'label'})
            label_col = 'label'
        
        if label_col not in df.columns: continue
        
        attacks = df[df[label_col] != 'Benign']
        if len(attacks) > 0:
            attack_dfs.append(attacks)
            
        benign = df[df[label_col] == 'Benign']
        if len(benign) > 0:
            # Sample benign to keep it balanced
            benign_dfs.append(benign.sample(min(len(benign), 10000), random_state=42))

        # Stop if we have enough for a representative sample
        if sum(len(x) for x in attack_dfs) > 200000:
            break

    if not attack_dfs:
        print(f"No attacks found in {target_day}, skipping visualization.")
        return

    df_attack = pd.concat(attack_dfs, ignore_index=True)
    df_benign = pd.concat(benign_dfs, ignore_index=True)
    
    # Final combined sample for plotting (max 100k)
    sampled_attack = df_attack.sample(min(len(df_attack), 50000), random_state=42)
    sampled_benign = df_benign.sample(min(len(df_benign), 50000), random_state=42)
    
    combined = pd.concat([sampled_benign, sampled_attack], ignore_index=True)
    print(f"Loaded subset: {len(combined)} samples ({len(sampled_benign)} Benign, {len(sampled_attack)} Attack)")

    # Define numeric features for analysis
    features = ['frame.len_count', 'frame.len_sum', 'frame.len_mean', 
                'frame.len_std', 'ip.proto', 'tcp.srcport', 
                'tcp.dstport', 'ip.ttl_mean', 'packet_rate', 'flow_duration_sec']
    
    features = [f for f in features if f in combined.columns]
    X = combined[features].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
    y = combined['label']

    # --- 1. Correlation Heatmap ---
    plt.figure(figsize=(12, 10))
    corr = X.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1)
    plt.title(f"{target_day} Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "correlation_heatmap.png"), dpi=300)
    plt.close()

    # --- 2. PCA Visualization ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    combined['PCA1'] = X_pca[:, 0]
    combined['PCA2'] = X_pca[:, 1]
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x='PCA1', y='PCA2', hue='label', data=combined, palette='Set1', s=15, alpha=0.5)
    plt.title(f"{target_day} PCA 2D Projection (Traffic Clusters)")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pca_visualization.png"), dpi=300)
    plt.close()

    # --- 3. Feature Distribution Violin Plots ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    sns.violinplot(x='label', y='packet_rate', data=combined, palette='Set2', ax=axes[0])
    axes[0].set_yscale('log')
    axes[0].set_title("Packet Rate Distribution (Log Scale)")
    
    sns.violinplot(x='label', y='ip.ttl_mean', data=combined, palette='Set3', ax=axes[1])
    axes[1].set_title("Average TTL Distribution")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "feature_distributions.png"), dpi=300)
    plt.close()

    # --- 4. Feature Importance (Random Forest) ---
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    y_bin = (y != 'Benign').astype(int)
    rf.fit(X, y_bin)
    
    importances = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=importances.values, y=importances.index, palette='magma')
    plt.title(f"{target_day} Feature Importance (Infiltration Detection)")
    plt.xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "feature_importance.png"), dpi=300)
    plt.close()

    # --- 5. Traffic Timeline ---
    if 'timestamp_min' in combined.columns:
        combined['datetime'] = pd.to_datetime(combined['timestamp_min'])
        combined['hour'] = combined['datetime'].dt.floor('h')
        
        timeline = combined.groupby(['hour', 'label']).size().reset_index(name='Flow Count')
        
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=timeline, x='hour', y='Flow Count', hue='label', marker='o')
        plt.title(f"{target_day} Traffic Volume Over Time (Hourly Samples)")
        plt.xlabel("Time (UTC)")
        plt.ylabel("Sampled flows")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "traffic_timeline.png"), dpi=300)
        plt.close()

    # --- 6. Summary Statistics ---
    stats = combined.groupby('label')[features].mean()
    stats.to_csv(os.path.join(output_dir, "label_stats.csv"))
    
    print(f"Results saved to {output_dir}/")

if __name__ == "__main__":
    run_detailed_eda("Wednesday-28-02-2018")
