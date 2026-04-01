import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import glob
import os

def run_detailed_eda(target_day="Tuesday-20-02-2018"):
    print(f"Starting DETAILED EDA for {target_day}...")
    output_dir = f"analysis_results/{target_day}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    path = f"processed_dataset/{target_day}/*_flows.parquet"
    files = glob.glob(path)
    if not files:
        print(f"No valid flow parquets found for {target_day}")
        return

    # Sample to avoid OutOfMemory for PCA and seaborn plots
    benign_dfs = []
    attack_dfs = []

    for f in sorted(files, key=os.path.getsize, reverse=True):
        df = pd.read_parquet(f)
        label_col = 'label' if 'label' in df.columns else 'label_<lambda>'
        if label_col not in df.columns: continue
        
        attacks = df[df[label_col] != 'Benign']
        if len(attacks) > 0:
            attack_dfs.append(attacks)
            
        benign = df[df[label_col] == 'Benign']
        if len(benign) > 0:
            benign_dfs.append(benign.sample(min(len(benign), 5000), random_state=42))

        if sum(len(x) for x in attack_dfs) > 100000 and sum(len(x) for x in benign_dfs) > 100000:
            break

    df_attack = pd.concat(attack_dfs, ignore_index=True)
    df_benign = pd.concat(benign_dfs, ignore_index=True)
    
    # Stratified sampling for final combined df (50k vs 50k)
    sampled_attack = df_attack.sample(min(len(df_attack), 50000), random_state=42)
    sampled_benign = df_benign.sample(min(len(df_benign), 50000), random_state=42)
    
    combined = pd.concat([sampled_benign, sampled_attack], ignore_index=True)
    label_col = 'label' if 'label' in combined.columns else 'label_<lambda>'

    print(f"[1/5] Loaded subset: {len(combined)} samples ({len(sampled_benign)} Benign, {len(sampled_attack)} Attack)")

    # Define numeric features
    features = ['frame.len_count', 'frame.len_sum', 'frame.len_mean', 
                'frame.len_std', 'ip.proto_first', 'tcp.srcport_first', 
                'tcp.dstport_first', 'ip.ttl_mean']
    
    features = [f for f in features if f in combined.columns]
    X = combined[features].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
    y = combined[label_col]

    # --- 1. Correlation Heatmap ---
    print("[2/5] Generating Correlation Heatmap...")
    plt.figure(figsize=(10, 8))
    corr = X.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1)
    plt.title(f"{target_day} Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "correlation_heatmap.png"), dpi=300)
    plt.close()

    # --- 2. PCA Visualization ---
    print("[3/5] Generating PCA Visualization...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    combined['PCA1'] = X_pca[:, 0]
    combined['PCA2'] = X_pca[:, 1]
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x='PCA1', y='PCA2', hue=label_col, data=combined, palette='Set1', s=20, alpha=0.7)
    plt.title(f"{target_day} PCA 2D Projection (Benign vs DDoS)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pca_visualization.png"), dpi=300)
    plt.close()

    # --- 3. Feature Distribution Violin Plots ---
    print("[4/5] Generating Feature Distributions (Violin Plots)...")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    sns.violinplot(x=label_col, y='frame.len_mean', data=combined, palette='Set2', ax=axes[0])
    axes[0].set_yscale('log')
    axes[0].set_title("Average Frame Length Distribution")
    
    sns.violinplot(x=label_col, y='ip.ttl_mean', data=combined, palette='Set3', ax=axes[1])
    axes[1].set_title("Average TTL Distribution")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "feature_distributions_violin.png"), dpi=300)
    plt.close()

    # --- 4. Simple Feature Importance (Random Forest) ---
    print("[5/5] Calculating Baseline Feature Importance...")
    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
    # Convert labels to binary for simplicity (Benign=0, Attack=1)
    y_bin = (y != 'Benign').astype(int)
    rf.fit(X, y_bin)
    
    importances = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=importances.values, y=importances.index, palette='viridis')
    plt.title("Feature Importance for DDoS Detection (Random Forest)")
    plt.xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "feature_importance.png"), dpi=300)
    plt.close()

    print(f"Detailed EDA Complete. Results saved to {output_dir}/")

if __name__ == "__main__":
    run_detailed_eda()
