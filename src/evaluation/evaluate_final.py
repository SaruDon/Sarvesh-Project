import os
import torch
import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from src.models.hybrid_pipeline import HybridNIDS
from src.data.data_loader import get_parquet_chunks

# Configuration
TEST_DIR = "processed_dataset/Golden_Test_Set"
XGB_PATH = "models/xgboost_flow_v1.json"
TRANSFORMER_PATH = "models/transformer_seq_v1.pth"
SCALER_PATH = "models/flow_scaler.joblib"

def evaluate_final_research():
    print("Starting Final Hybrid Evaluation (Golden_Test_Set)...")
    
    # 1. Load Hybrid NIDS
    nids = HybridNIDS(XGB_PATH, TRANSFORMER_PATH, SCALER_PATH)
    
    # 2. Collect Predictions (Sampling for speed on the large test set)
    y_true = []
    y_pred = []
    
    # Use the flow-based chunk generator for the test set
    chunk_gen = get_parquet_chunks(TEST_DIR, mode='flow', chunk_size=1000)
    
    for X_chunk, y_chunk in tqdm(chunk_gen, desc="Running Hybrid Inference"):
        for i in range(len(X_chunk)):
            flow_feat = X_chunk.iloc[i].values
            
            # For this evaluation, we simulate "sequence availability" 
            # In a real environment, sequences would be tracked in a buffer.
            # Here, we assume Stage 2 always has access to the packet windows.
            label, score = nids.predict(flow_feat)
            
            y_true.append(y_chunk.iloc[i])
            y_pred.append(1 if "ATTACK" in label else 0)
            
            # Limit to 50,000 test samples for the final paper's core metrics
            if len(y_true) >= 50000:
                break
        if len(y_true) >= 50000:
            break

    # 3. Final Report
    os.makedirs("analysis_results", exist_ok=True)
    report = classification_report(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    
    with open("analysis_results/final_hybrid_report.txt", "w") as f:
        f.write("=== FINAL HYBRID NIDS EVALUATION (APRIL 3RD, 2026) ===\n")
        f.write(report)
        f.write("\nConfusion Matrix:\n")
        f.write(str(cm))
        
    # Plot CM
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Final Hybrid NIDS Confusion Matrix')
    plt.savefig("analysis_results/final_confusion_matrix.png")
    
    print("\nFinal Evaluation Complete. Metrics saved to analysis_results/")

if __name__ == "__main__":
    evaluate_final_research()
