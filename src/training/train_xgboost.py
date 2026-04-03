import os
import xgboost as xgb
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix
from src.data.data_loader import get_parquet_chunks
from tqdm import tqdm

# Configuration
PROCESSED_DIR = "processed_dataset"
SCALER_PATH = "models/flow_scaler.joblib"
MODEL_OUT = "models/xgboost_flow_v1.json"

def train_stage1():
    print("Starting Stage 1 Training: XGBoost (Flow Classification)...")
    
    # Initialize the booster
    # Using 'hist' for high-speed processing of large datasets
    params = {
        'objective': 'binary:logistic',
        'tree_method': 'hist', # Optimized for large data
        'device': 'cuda',     # Run on the RTX A400 GPU
        'max_depth': 6,
        'learning_rate': 0.1,
        'eval_metric': 'logloss',
        'scale_pos_weight': 50 # Handle imbalance (Benign ~50x Attack)
    }
    
    model = None
    first_chunk = True
    
    # Stream the dataset in chunks to avoid OOM
    # Total flows: 51 Million. Chunk size: 500k
    chunk_gen = get_parquet_chunks(PROCESSED_DIR, mode='flow', chunk_size=500000, scaler_path=SCALER_PATH)
    
    # Simple training loop for XGBoost (Incremental/Continual not directly supported in sklearn API for all cases)
    # We will accumulate a representative subset for this baseline or use the booster API
    X_train_list = []
    y_train_list = []
    
    # For a baseline, we'll take a large stratified sample (5 Million flows) to balance time and accuracy
    MAX_SAMPLES = 5000000 
    curr_samples = 0
    
    print(f"Sampling {MAX_SAMPLES} flows for training...")
    for X_chunk, y_chunk in tqdm(chunk_gen, desc="Loading Chunks"):
        X_train_list.append(X_chunk)
        y_train_list.append(y_chunk)
        curr_samples += len(X_chunk)
        if curr_samples >= MAX_SAMPLES:
            break
            
    X_train = np.vstack(X_train_list)
    y_train = np.concatenate(y_train_list)
    
    print(f"Training on {len(X_train)} samples with GPU...")
    dtrain = xgb.DMatrix(X_train, label=y_train)
    bst = xgb.train(params, dtrain, num_boost_round=100)
    
    # Save the model
    os.makedirs("models", exist_ok=True)
    bst.save_model(MODEL_OUT)
    print(f"Model saved to {MODEL_OUT}")

    # Preliminary Evaluation
    preds = bst.predict(dtrain)
    y_pred = (preds > 0.5).astype(int)
    print("\nTraining Set Performance:")
    print(classification_report(y_train, y_pred))

if __name__ == "__main__":
    train_stage1()
