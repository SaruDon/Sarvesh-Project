"""
XGBoost v4: Attack-Priority Loading + Multi-Class
====================================================
Key improvements over v3:
1. ATTACK-PRIORITY LOADING: Load ALL attack-bearing files first,
   then fill remaining capacity with benign files.
   This ensures the model sees every attack variant.
2. MULTI-CLASS: Train with multi:softprob (9 classes) instead
   of binary. Each attack type has different patterns.
3. Same 43 enhanced features from v3.
"""
import os
import glob
import random
import json
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

PROCESSED_DIR = "processed_dataset"
GOLDEN_DIR = os.path.join(PROCESSED_DIR, "Golden_Test_Set")
MODEL_DIR = "models"
RESULTS_DIR = "analysis_results"
SEED = 42

# Well-known ports
WELL_KNOWN_PORTS = {
    'http': [80, 8080, 8000, 8888],
    'https': [443, 8443],
    'ssh': [22],
    'ftp': [21, 20],
    'dns': [53],
    'smtp': [25, 587],
    'mysql': [3306],
    'rdp': [3389],
    'smb': [445, 139],
}

OLD_METADATA_COLS = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport',
                     'timestamp_min', 'timestamp_max', 'label']


def engineer_features(df):
    """Same 43 features as v3."""
    features = pd.DataFrame(index=df.index)

    features['packet_count'] = df['frame.len_count'].fillna(0)
    features['total_bytes'] = df['frame.len_sum'].fillna(0)
    features['avg_packet_size'] = df['frame.len_mean'].fillna(0)
    features['packet_size_std'] = df['frame.len_std'].fillna(0)
    features['ttl_mean'] = df['ip.ttl_mean'].fillna(0)
    features['window_size_mean'] = df['tcp.window_size_value_mean'].fillna(0)
    features['flow_duration'] = df['flow_duration_sec'].fillna(0)
    features['packet_rate'] = df['packet_rate'].fillna(0)

    features['log_packet_count'] = np.log1p(features['packet_count'])
    features['log_total_bytes'] = np.log1p(features['total_bytes'])
    features['log_packet_rate'] = np.log1p(features['packet_rate'])
    features['log_duration'] = np.log1p(features['flow_duration'])

    features['bytes_per_sec'] = features['total_bytes'] / features['flow_duration'].replace(0, 0.001)
    features['log_bytes_per_sec'] = np.log1p(features['bytes_per_sec'].clip(upper=1e9))
    features['packet_size_cv'] = (features['packet_size_std'] / features['avg_packet_size'].replace(0, 0.001)).clip(upper=100)
    features['is_single_packet'] = (features['packet_count'] == 1).astype(np.float32)
    features['is_micro_flow'] = (features['packet_count'] <= 5).astype(np.float32)
    features['is_large_flow'] = (features['packet_count'] > 100).astype(np.float32)
    features['is_small_payload'] = (features['avg_packet_size'] < 100).astype(np.float32)

    proto = df['ip.proto'].fillna(0).astype(int)
    features['proto_tcp'] = (proto == 6).astype(np.float32)
    features['proto_udp'] = (proto == 17).astype(np.float32)
    features['proto_icmp'] = (proto == 1).astype(np.float32)
    features['proto_other'] = ((proto != 6) & (proto != 17) & (proto != 1)).astype(np.float32)

    srcport = df['tcp.srcport'].fillna(0).astype(int)
    dstport = df['tcp.dstport'].fillna(0).astype(int)

    for name, ports in WELL_KNOWN_PORTS.items():
        features[f'dst_is_{name}'] = dstport.isin(ports).astype(np.float32)

    features['src_ephemeral'] = (srcport > 1024).astype(np.float32)
    features['dst_ephemeral'] = (dstport > 1024).astype(np.float32)
    features['both_ephemeral'] = ((srcport > 1024) & (dstport > 1024)).astype(np.float32)
    features['dstport_value'] = dstport.clip(upper=65535).astype(np.float32)
    features['srcport_value'] = srcport.clip(upper=65535).astype(np.float32)

    features['low_ttl'] = (features['ttl_mean'] < 32).astype(np.float32)
    ttl_rounded = features['ttl_mean'].round()
    features['unusual_ttl'] = (~ttl_rounded.isin([32, 64, 128, 255])).astype(np.float32)
    features['zero_window'] = (features['window_size_mean'] == 0).astype(np.float32)
    features['large_window'] = (features['window_size_mean'] > 60000).astype(np.float32)
    features['bytes_x_packets'] = np.log1p(features['total_bytes'] * features['packet_count'])
    features['rate_x_size'] = features['packet_rate'] * features['avg_packet_size'] / 1e6

    features = features.fillna(0).replace([np.inf, -np.inf], 0)
    return features


def get_train_files():
    all_files = glob.glob(os.path.join(PROCESSED_DIR, "**", "*_flows.parquet"), recursive=True)
    return [f for f in all_files if "Golden_Test_Set" not in f
            and os.path.relpath(f, PROCESSED_DIR).split(os.sep)[0] != 'pcap']

def get_test_files():
    return glob.glob(os.path.join(GOLDEN_DIR, "**", "*_flows.parquet"), recursive=True)


def classify_files(files):
    """Separate files into attack-bearing and benign-only."""
    attack_files = []
    benign_files = []

    for f in tqdm(files, desc="Classifying files"):
        try:
            labels = pd.read_parquet(f, columns=['label'])['label']
            if (labels != 'Benign').any():
                attack_files.append(f)
            else:
                benign_files.append(f)
        except:
            continue

    return attack_files, benign_files


def load_attack_priority(train_files, max_total=12_000_000):
    """
    Load ALL attack-bearing files first, then fill with benign files.
    This ensures the model sees every attack variant.
    """
    print("\n[1] Classifying files...")
    attack_files, benign_files = classify_files(train_files)
    print(f"    Attack-bearing files: {len(attack_files)}")
    print(f"    Benign-only files: {len(benign_files)}")

    X_list, labels_list = [], []
    curr = 0

    # Phase 1: Load ALL attack-bearing files (guaranteed)
    print(f"\n[2] Loading ALL {len(attack_files)} attack-bearing files...")
    for f in tqdm(attack_files, desc="  Attack files"):
        try:
            df = pd.read_parquet(f)
            if len(df) == 0: continue
            X_list.append(engineer_features(df).values.astype(np.float32))
            labels_list.append(df['label'].values)
            curr += len(df)
        except:
            continue

    attack_samples = curr
    print(f"    Loaded {attack_samples:,} samples from attack files")

    # Phase 2: Fill with benign files until max
    remaining = max_total - curr
    random.seed(SEED)
    random.shuffle(benign_files)

    print(f"\n[3] Filling with benign files (up to {remaining:,} more)...")
    for f in tqdm(benign_files, desc="  Benign files"):
        if curr >= max_total:
            break
        try:
            df = pd.read_parquet(f)
            if len(df) == 0: continue
            X_list.append(engineer_features(df).values.astype(np.float32))
            labels_list.append(df['label'].values)
            curr += len(df)
        except:
            continue

    X = np.vstack(X_list)
    labels = np.concatenate(labels_list)

    # Get feature names
    sample = pd.read_parquet(train_files[0])
    feature_names = list(engineer_features(sample.head(1)).columns)

    return X, labels, feature_names


def main():
    print("=" * 70)
    print("XGBOOST v4: ATTACK-PRIORITY + MULTI-CLASS")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    random.seed(SEED)
    np.random.seed(SEED)

    train_files = get_train_files()
    test_files = get_test_files()
    print(f"Training files: {len(train_files)}")
    print(f"Test files: {len(test_files)}")

    # ============================================================
    # STAGE 1: Attack-Priority Loading
    # ============================================================
    print("\n" + "=" * 70)
    print("STAGE 1: ATTACK-PRIORITY DATA LOADING")
    print("=" * 70)

    X_train, labels_train, feature_names = load_attack_priority(train_files, max_total=12_000_000)

    # Label encoding for multi-class
    le = LabelEncoder()
    y_train = le.fit_transform(labels_train)
    num_classes = len(le.classes_)

    print(f"\nTotal training samples: {len(X_train):,}")
    print(f"Number of classes: {num_classes}")
    print("\nClass distribution:")
    for i, cls in enumerate(le.classes_):
        count = (y_train == i).sum()
        pct = count / len(y_train) * 100
        print(f"  [{i}] {cls:20s}: {count:>10,} ({pct:.2f}%)")

    # Save label encoder
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder_v4.joblib"))

    # ============================================================
    # STAGE 2: Scaling
    # ============================================================
    print("\n" + "=" * 70)
    print("STAGE 2: SCALING")
    print("=" * 70)

    scaler = StandardScaler()
    scaler.fit(X_train)
    scaler_path = os.path.join(MODEL_DIR, "flow_scaler_v4.joblib")
    joblib.dump(scaler, scaler_path)

    X_train_scaled = np.nan_to_num(scaler.transform(X_train), nan=0.0, posinf=10.0, neginf=-10.0)
    print(f"Scaler saved: {scaler_path}")

    # ============================================================
    # STAGE 3: Multi-Class XGBoost Training
    # ============================================================
    print("\n" + "=" * 70)
    print("STAGE 3: MULTI-CLASS XGBOOST TRAINING")
    print("=" * 70)

    # Compute per-class sample weights for imbalance (CAPPED + sqrt dampened)
    class_counts = np.bincount(y_train, minlength=num_classes)
    max_count = class_counts.max()
    raw_weights = max_count / np.maximum(class_counts, 1)
    # SOFTENED: Multiplier reduced from 3 to 1.5, Cap reduced from 50 to 10
    # This prioritizes Benign Precision by reducing the "cost" of missing rare attacks
    class_weights = np.minimum(np.sqrt(raw_weights) * 1.5, 10.0)
    class_weights[list(le.classes_).index('Benign')] = 1.0  # Benign always 1.0
    sample_weights = class_weights[y_train]

    print(f"\nClass weights:")
    for i, cls in enumerate(le.classes_):
        print(f"  {cls:20s}: weight={class_weights[i]:.1f}")

    # Train/eval split
    indices = np.random.RandomState(SEED).permutation(len(X_train_scaled))
    split = int(len(indices) * 0.9)
    train_idx, eval_idx = indices[:split], indices[split:]

    dtrain = xgb.DMatrix(X_train_scaled[train_idx], label=y_train[train_idx],
                         weight=sample_weights[train_idx], feature_names=feature_names)
    deval = xgb.DMatrix(X_train_scaled[eval_idx], label=y_train[eval_idx],
                        weight=sample_weights[eval_idx], feature_names=feature_names)

    params = {
        'objective': 'multi:softprob',
        'num_class': num_classes,
        'tree_method': 'hist',
        'device': 'cuda',
        'max_depth': 10,
        'learning_rate': 0.05,
        'eval_metric': 'mlogloss',
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 5,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'seed': SEED
    }

    print(f"\nTraining {num_classes}-class XGBoost on GPU...")
    bst = xgb.train(
        params, dtrain,
        num_boost_round=500,
        evals=[(dtrain, 'train'), (deval, 'eval')],
        early_stopping_rounds=30,
        verbose_eval=50
    )

    model_path = os.path.join(MODEL_DIR, "xgboost_flow_v4.json")
    bst.save_model(model_path)
    print(f"\nModel saved: {model_path} (best iter: {bst.best_iteration})")

    # Training metrics
    train_probs = bst.predict(dtrain)
    train_preds = train_probs.argmax(axis=1)
    train_acc = accuracy_score(y_train[train_idx], train_preds)
    print(f"Training Accuracy: {train_acc:.4f}")

    # ============================================================
    # STAGE 4: Evaluation
    # ============================================================
    print("\n" + "=" * 70)
    print("STAGE 4: TEST SET EVALUATION")
    print("=" * 70)

    # Load test data
    X_test_list, labels_test_list = [], []
    for f in tqdm(test_files, desc="Loading test data"):
        try:
            df = pd.read_parquet(f)
            if len(df) == 0: continue
            X_test_list.append(engineer_features(df).values.astype(np.float32))
            labels_test_list.append(df['label'].values)
        except:
            continue

    X_test = np.vstack(X_test_list)
    labels_test = np.concatenate(labels_test_list)

    # Handle unseen labels in test (shouldn't happen but be safe)
    y_test = np.array([le.transform([l])[0] if l in le.classes_ else -1 for l in labels_test])
    valid_mask = y_test >= 0
    X_test = X_test[valid_mask]
    y_test = y_test[valid_mask]
    labels_test = labels_test[valid_mask]

    X_test_scaled = np.nan_to_num(scaler.transform(X_test), nan=0.0, posinf=10.0, neginf=-10.0)
    dtest = xgb.DMatrix(X_test_scaled, feature_names=feature_names)

    test_probs = bst.predict(dtest)
    test_preds = test_probs.argmax(axis=1)

    test_acc = accuracy_score(y_test, test_preds)
    test_f1_macro = f1_score(y_test, test_preds, average='macro')
    test_f1_weighted = f1_score(y_test, test_preds, average='weighted')

    # Confidence-Filtered Results (Priority: Precision)
    # Only classify as attack if higher than 90% confidence
    high_conf_preds = test_preds.copy()
    max_probs = test_probs.max(axis=1)
    benign_idx = list(le.classes_).index('Benign')
    high_conf_preds[max_probs < 0.9] = benign_idx
    
    test_acc_90 = accuracy_score(y_test, high_conf_preds)
    test_f1_w_90 = f1_score(y_test, high_conf_preds, average='weighted')

    print(f"\nTest samples: {len(X_test):,}")
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS")
    print(f"{'='*60}")
    print(f"Accuracy:         {test_acc:.4f}")
    print(f"F1 (macro):       {test_f1_macro:.4f}")
    print(f"F1 (weighted):    {test_f1_weighted:.4f}")
    print(f"\n--- 90% Confidence Threshold Results ---")
    print(f"Accuracy (90%):   {test_acc_90:.4f}")
    print(f"F1 (weighted,90%):{test_f1_w_90:.4f}")

    # Classification report
    target_names = [le.classes_[i] for i in sorted(np.unique(y_test))]
    report = classification_report(y_test, test_preds, target_names=target_names, digits=4, zero_division=0)
    print(f"\n{report}")

    # Per-class recall
    print(f"{'='*60}")
    print(f"PER-CLASS RECALL")
    print(f"{'='*60}")
    attack_recalls = {}
    for i, cls in enumerate(le.classes_):
        mask = y_test == i
        if mask.sum() > 0:
            recall = (test_preds[mask] == i).mean()
            attack_recalls[cls] = recall
            print(f"  {cls:20s}: {recall:.4f} ({(test_preds[mask]==i).sum():>8,}/{mask.sum():>8,})")

    # Binary attack recall (any non-benign correctly identified as non-benign)
    benign_idx = list(le.classes_).index('Benign')
    is_attack_true = y_test != benign_idx
    is_attack_pred = test_preds != benign_idx
    binary_attack_recall = is_attack_pred[is_attack_true].mean() if is_attack_true.sum() > 0 else 0
    binary_benign_recall = (~is_attack_pred[~is_attack_true]).mean() if (~is_attack_true).sum() > 0 else 0
    print(f"\n  Binary Attack Recall: {binary_attack_recall:.4f}")
    print(f"  Binary Benign Recall: {binary_benign_recall:.4f}")

    # ============================================================
    # STAGE 5: Visualizations
    # ============================================================
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Multi-class confusion matrix
    cm = confusion_matrix(y_test, test_preds)
    plt.figure(figsize=(14, 11))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=le.classes_, yticklabels=le.classes_)
    plt.xlabel('Predicted'); plt.ylabel('True')
    plt.title(f'XGBoost v4 Multi-Class Confusion Matrix (N={len(y_test):,})')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "xgboost_v4_confusion_matrix.png"), dpi=150)
    plt.close()

    # Feature importance
    importance = bst.get_score(importance_type='gain')
    if importance:
        sorted_imp = sorted(importance.items(), key=lambda x: -x[1])[:15]
        plt.figure(figsize=(12, 8))
        names = [x[0] for x in sorted_imp]
        values = [x[1] for x in sorted_imp]
        colors = ['#e74c3c' if any(k in n for k in ['port', 'dst_is', 'proto', 'log_', 'is_', 'cv', 'bytes_per', 'both_', 'low_', 'unusual', 'zero_', 'large_', 'rate_x']) else '#3498db' for n in names]
        plt.barh(range(len(names)), values, color=colors)
        plt.yticks(range(len(names)), names)
        plt.xlabel('Gain')
        plt.title('XGBoost v4 Multi-Class - Feature Importance')
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, "xgboost_v4_feature_importance.png"), dpi=150)
        plt.close()

        print(f"\n{'='*60}")
        print(f"TOP 15 FEATURES")
        print(f"{'='*60}")
        for name, gain in sorted_imp:
            print(f"  {name:30s}: {gain:>10.2f}")

    # Overfitting
    print(f"\n{'='*60}")
    print(f"OVERFITTING CHECK")
    print(f"{'='*60}")
    print(f"  Train Accuracy: {train_acc:.4f}")
    print(f"  Test Accuracy:  {test_acc:.4f}")
    print(f"  Gap:            {abs(train_acc - test_acc):.4f}")

    # Save report
    report_path = os.path.join(RESULTS_DIR, "xgboost_v4_evaluation_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"XGBOOST v4: ATTACK-PRIORITY + MULTI-CLASS\n")
        f.write(f"Generated: {datetime.now()}\n{'='*60}\n\n")
        f.write(f"Features: {len(feature_names)} | Classes: {num_classes}\n")
        f.write(f"Training: {len(X_train):,} | Test: {len(X_test):,}\n\n")
        f1_90 = f1_score(y_test, high_conf_preds, average='weighted')
        benign_recall_90 = (~(high_conf_preds != benign_idx)[y_test == benign_idx]).mean()

        f.write(f"Accuracy: {test_acc:.4f}\n")
        f.write(f"F1 (macro): {test_f1_macro:.4f}\n")
        f.write(f"F1 (weighted): {test_f1_weighted:.4f}\n")
        f.write(f"Accuracy (90% Conf): {test_acc_90:.4f}\n")
        f.write(f"F1 (90% Conf): {f1_90:.4f}\n")
        f.write(f"Benign Recall (90% Conf): {benign_recall_90:.4f}\n")
        f.write(f"Binary Attack Recall: {binary_attack_recall:.4f}\n")
        f.write(f"Binary Benign Recall: {binary_benign_recall:.4f}\n\n")
        f.write(report + "\n")
        f.write("Per-Class Recall:\n")
        for cls, recall in attack_recalls.items():
            f.write(f"  {cls}: {recall:.4f}\n")
        f.write(f"\nConfusion Matrix:\n{cm}\n")

    print(f"\nReport saved: {report_path}")
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
