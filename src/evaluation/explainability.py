import os
import torch
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import xgboost as xgb
from src.models.seq_classifier import TransformerNIDS
from src.data.data_loader import get_parquet_chunks

def explain_xgboost(processed_dir, model_path, scaler_path, out_dir="analysis_results/explainability"):
    os.makedirs(out_dir, exist_ok=True)
    print("Generating SHAP explanations for XGBoost (Flows)...")
    
    # Load model and data sample
    bst = xgb.Booster()
    bst.load_model(model_path)
    scaler = joblib.load(scaler_path)
    
    # Get a sample of attack and benign flows
    chunk_gen = get_parquet_chunks(processed_dir, mode='flow', chunk_size=1000, scaler_path=scaler_path)
    X_sample, y_sample = next(chunk_gen)
    
    # SHAP Tree Explainer
    explainer = shap.TreeExplainer(bst)
    shap_values = explainer.shap_values(X_sample)
    
    # Feature Names (Based on dataset_builder.py logic)
    feature_names = [
        'frame.len_count', 'frame.len_sum', 'frame.len_mean', 'frame.len_std',
        'ip.ttl_mean', 'tcp.window_size_value_mean', 'flow_duration_sec', 'packet_rate'
    ]
    # Handle the fact that some columns might be missing or added
    if shap_values.shape[1] > len(feature_names):
        feature_names += [f"extra_{i}" for i in range(shap_values.shape[1] - len(feature_names))]
    elif shap_values.shape[1] < len(feature_names):
        feature_names = feature_names[:shap_values.shape[1]]

    # Summary Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_sample, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "xgboost_shap_summary.png"))
    plt.close()
    print(f"SHAP summary saved to {out_dir}")

def explain_transformer(model_path, sample_input, out_dir="analysis_results/explainability"):
    # This requires the model to be loaded and a sample input
    # For now, we'll implement the attention extractor logic
    os.makedirs(out_dir, exist_ok=True)
    print("Generating Attention Heatmaps for Transformer (Sequences)...")
    
    # Visualizing attention is best done during/after training with the model object
    # We will create a utility here that can be called by the evaluation script
    pass

def generate_research_plots(processed_dir, out_dir="analysis_results/eda"):
    os.makedirs(out_dir, exist_ok=True)
    print("Generating Research EDA Portfolio...")
    
    # 1. Packet Rate Distribution
    all_stats = []
    flow_files = glob.glob(os.path.join(processed_dir, "**", "*_flows.parquet"), recursive=True)[:50] # Sample for speed
    for f in flow_files:
        df = pd.read_parquet(f, columns=['label', 'packet_rate', 'flow_duration_sec'])
        all_stats.append(df)
    
    combined = pd.concat(all_stats)
    
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=combined, x='label', y='packet_rate')
    plt.yscale('log')
    plt.title("Packet Rate Distribution by Attack Type")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "packet_rate_dist.png"))
    
    # 2. Attack Duration
    plt.figure(figsize=(12, 6))
    sns.violinplot(data=combined[combined['label'] != 'Benign'], x='label', y='flow_duration_sec')
    plt.title("Attack Duration (Seconds)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "attack_duration.png"))
    
    print(f"Research plots saved to {out_dir}")

if __name__ == "__main__":
    import glob
    processed_dir = "processed_dataset"
    generate_research_plots(processed_dir)
    if os.path.exists("models/xgboost_flow_v1.json"):
        explain_xgboost(processed_dir, "models/xgboost_flow_v1.json", "models/flow_scaler.joblib")
