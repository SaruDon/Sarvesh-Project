import os
import torch
import pandas as pd
import numpy as np
import glob
import random
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from src.models.hybrid_pipeline import HybridNIDS
import xgboost as xgb

# Configuration
TEST_DIR = "processed_dataset/Golden_Test_Set"
XGB_PATH = "models/xgboost_flow_v1.json"
TRANSFORMER_PATH = "models/transformer_seq_v1.pth"
FLOW_SCALER_PATH = "models/flow_scaler.joblib"
SEQ_SCALER_PATH = "models/seq_scaler.joblib"

def evaluate_final_research():
    print("Starting Shuffled Hybrid Evaluation (500k samples from Golden_Test_Set)...")
    
    # 1. Load Hybrid NIDS
    nids = HybridNIDS(XGB_PATH, TRANSFORMER_PATH, FLOW_SCALER_PATH, SEQ_SCALER_PATH)
    
    # 2. Collect Predictions
    y_true = []
    y_pred_final = []
    labels_true = []
    total_transformer_triggers = 0
    
    # Identify all flow files in the test set
    flow_files = glob.glob(os.path.join(TEST_DIR, "**", "*_flows.parquet"), recursive=True)
    random.seed(42) # Deterministic shuffle for reproducibility
    random.shuffle(flow_files)
    
    # Process files until we hit 500,000 samples
    LIMIT = 500000
    
    for flow_f in tqdm(flow_files, desc="Processing Test"):
        seq_f = flow_f.replace("_flows.parquet", "_sequences.parquet")
        
        try:
            df_flows = pd.read_parquet(flow_f)
            # Drop metadata and label
            exclude = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'timestamp_min', 'timestamp_max', 'label']
            X_flows = df_flows.drop(columns=[c for c in exclude if c in df_flows.columns]).values.astype(np.float32)
            y_flows_raw = df_flows['label'].values
            
            # Load sequences only if file exists and lengths match
            X_seqs = None
            if os.path.exists(seq_f):
                df_seqs = pd.read_parquet(seq_f)
                if len(df_seqs) == len(df_flows):
                    X_seqs = np.stack(df_seqs['sequence_features'].values).reshape(-1, 200, 9)
            
            # --- Vectorized Hybrid Inference ---
            file_preds, xgb_scores, triggers = nids.predict_batch(X_flows, X_seqs)
            
            # Collect results (Truncate if over LIMIT)
            current_count = len(y_true)
            remaining = LIMIT - current_count
            take = min(len(y_flows_raw), remaining)
            
            y_true.extend(np.where(y_flows_raw[:take] != 'Benign', 1, 0))
            y_pred_final.extend(file_preds[:take])
            labels_true.extend(y_flows_raw[:take])
            total_transformer_triggers += (triggers if take == len(y_flows_raw) else int(triggers * (take / len(y_flows_raw))))
            
            if len(y_true) >= LIMIT:
                break
                
        except Exception as e:
            print(f"Error processing {flow_f}: {e}")
            continue

    # 3. Final Report
    os.makedirs("analysis_results", exist_ok=True)
    if not y_true:
        print("ERROR: No samples were evaluated.")
        return

    y_true_np = np.array(y_true)
    y_pred_np = np.array(y_pred_final)

    report = classification_report(y_true_np, y_pred_np, target_names=["Benign", "Attack"], labels=[0, 1])
    cm = confusion_matrix(y_true_np, y_pred_np, labels=[0, 1])
    
    # Calculate Per-Attack Recall
    df_results = pd.DataFrame({'true_label': labels_true, 'pred': y_pred_final})
    attack_summary = []
    for label in df_results['true_label'].unique():
        subset = df_results[df_results['true_label'] == label]
        recall = subset['pred'].mean() if label != "Benign" else 1 - subset['pred'].mean()
        attack_summary.append(f"{label}: {recall:.2%} Recall")
    
    trigger_rate = total_transformer_triggers / len(y_true) if len(y_true) > 0 else 0
    attack_indices = np.where(y_true_np == 1)[0]
    final_attack_recall = y_pred_np[attack_indices].mean() if len(attack_indices) > 0 else 0.0

    with open("analysis_results/final_hybrid_report.txt", "w") as f:
        f.write("=== FINAL HYBRID NIDS EVALUATION (REFINED 500K) ===\n")
        f.write(f"Total Samples Evaluated: {len(y_true)}\n")
        f.write(f"Transformer Trigger Rate: {trigger_rate:.2%} ({total_transformer_triggers} sessions)\n")
        f.write(f"Overall Attack Recall: {final_attack_recall:.2%}\n")
        f.write("\n--- Classification Report ---\n")
        f.write(report)
        f.write("\n--- Per-Attack Recall ---\n")
        f.write("\n".join(attack_summary))
        f.write("\n\n--- Confusion Matrix ---\n")
        f.write(str(cm))
        
    # Plot CM
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=["Benign", "Attack"], yticklabels=["Benign", "Attack"])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Refined Hybrid NIDS Confusion Matrix (N={len(y_true)})')
    plt.savefig("analysis_results/final_confusion_matrix.png")
    
    print(f"\nFinal Evaluation Complete. {len(y_true)} samples processed.")
    print(f"Attack Recall: {final_attack_recall:.2%}")
    print("Metrics saved to analysis_results/final_hybrid_report.txt")

if __name__ == "__main__":
    evaluate_final_research()
