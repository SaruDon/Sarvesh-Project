"""Diagnostic: Isolate XGBoost vs Transformer on ATTACK-RICH files."""
import os, sys
sys.path.insert(0, '.')
import torch, numpy as np, pandas as pd, glob, xgboost as xgb, joblib
from src.models.seq_classifier import TransformerNIDS

# Load models
bst = xgb.Booster(); bst.load_model("models/xgboost_flow_v1.json")
flow_scaler = joblib.load("models/flow_scaler.joblib")
seq_scaler = joblib.load("models/seq_scaler.joblib")
transformer = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
transformer.load_state_dict(torch.load("models/transformer_seq_v1.pth", map_location='cuda', weights_only=True))
transformer.to('cuda').eval()

# Target attack-rich subdirectories
TEST_DIR = "processed_dataset/Golden_Test_Set"
attack_dirs = [
    os.path.join(TEST_DIR, "Thursday-01-03-2018"),  # Infiltration
    os.path.join(TEST_DIR, "Friday-23-02-2018"),     # Brute Force
    os.path.join(TEST_DIR, "Wednesday-28-02-2018"),   # Infiltration
]

all_true, labels_all = [], []
xgb_scores_all, trans_scores_all = [], []

for d in attack_dirs:
    if not os.path.exists(d):
        continue
    flow_files = glob.glob(os.path.join(d, "*_flows.parquet"))
    for flow_f in flow_files[:10]:  # up to 10 files per dir
        seq_f = flow_f.replace("_flows.parquet", "_sequences.parquet")
        try:
            df = pd.read_parquet(flow_f)
            exclude = ['ip.src','ip.dst','ip.proto','tcp.srcport','tcp.dstport','timestamp_min','timestamp_max','label']
            X = df.drop(columns=[c for c in exclude if c in df.columns]).values.astype(np.float32)
            y = df['label'].values
            
            X_scaled = flow_scaler.transform(X)
            dm = xgb.DMatrix(X_scaled)
            scores = bst.predict(dm)
            
            xgb_scores_all.extend(scores)
            all_true.extend([1 if l != 'Benign' else 0 for l in y])
            labels_all.extend(y)
            
            if os.path.exists(seq_f):
                df_seq = pd.read_parquet(seq_f)
                if len(df_seq) == len(df):
                    X_seq = np.stack(df_seq['sequence_features'].values).reshape(-1, 200, 9)
                    X_seq_scaled = seq_scaler.transform(X_seq.reshape(-1, 9)).reshape(-1, 200, 9)
                    with torch.no_grad():
                        t = torch.tensor(X_seq_scaled, dtype=torch.float32).to('cuda')
                        logits = transformer(t)
                        ts = torch.sigmoid(logits).cpu().numpy()
                    trans_scores_all.extend(ts)
                else:
                    trans_scores_all.extend([np.nan] * len(df))
            else:
                trans_scores_all.extend([np.nan] * len(df))
        except Exception as e:
            print(f"Error: {e}")

# Analysis
y = np.array(all_true)
xgb_s = np.array(xgb_scores_all[:len(y)])
trans_s = np.array(trans_scores_all[:len(y)])
labels = np.array(labels_all[:len(y)])

print(f"\n{'='*60}")
print(f"ATTACK-FOCUSED DIAGNOSTIC ({len(y)} samples)")
print(f"{'='*60}")

n_attack = y.sum()
n_benign = len(y) - n_attack
print(f"\nData: {n_benign} Benign, {n_attack} Attack")

# XGBoost alone
xgb_pred = (xgb_s > 0.5).astype(int)
xgb_tp = ((xgb_pred == 1) & (y == 1)).sum()
xgb_fp = ((xgb_pred == 1) & (y == 0)).sum()
print(f"\n--- XGBoost Alone (threshold=0.5) ---")
print(f"  Attack Recall: {xgb_tp}/{n_attack} = {xgb_tp/n_attack:.2%}" if n_attack > 0 else "  No attacks")
print(f"  False Positives: {xgb_fp}")

# Lower thresholds
for t in [0.3, 0.2, 0.1]:
    tp = ((xgb_s > t) & (y == 1)).sum()
    fp = ((xgb_s > t) & (y == 0)).sum()
    print(f"  At threshold {t}: Recall={tp/n_attack:.2%}, FP={fp}")

attack_mask = y == 1
if attack_mask.any():
    print(f"\n--- XGBoost Score Distribution for ATTACK flows ---")
    print(f"  Mean: {xgb_s[attack_mask].mean():.4f}")
    print(f"  Median: {np.median(xgb_s[attack_mask]):.4f}")
    print(f"  Min: {xgb_s[attack_mask].min():.4f}")
    print(f"  Max: {xgb_s[attack_mask].max():.4f}")
    
    for label in np.unique(labels[attack_mask]):
        lmask = labels == label
        print(f"\n  {label} (N={lmask.sum()}):")
        print(f"    XGB scores: mean={xgb_s[lmask].mean():.4f}, median={np.median(xgb_s[lmask]):.4f}")
        print(f"    XGB >0.5: {(xgb_s[lmask] > 0.5).sum()}/{lmask.sum()}")
        print(f"    XGB >0.3: {(xgb_s[lmask] > 0.3).sum()}/{lmask.sum()}")

# Transformer analysis
valid_trans = ~np.isnan(trans_s)
if valid_trans.any() and attack_mask.any():
    both = valid_trans & attack_mask
    if both.any():
        print(f"\n--- Transformer Score Distribution for ATTACK flows ---")
        print(f"  Mean: {trans_s[both].mean():.4f}")
        print(f"  Median: {np.median(trans_s[both]):.4f}")
        print(f"  >0.5: {(trans_s[both] > 0.5).sum()}/{both.sum()}")
        print(f"  >0.3: {(trans_s[both] > 0.3).sum()}/{both.sum()}")
        
        for label in np.unique(labels[both]):
            lmask = (labels == label) & valid_trans
            if lmask.any():
                print(f"\n  {label} (N={lmask.sum()}):")
                print(f"    Transformer scores: mean={trans_s[lmask].mean():.4f}, median={np.median(trans_s[lmask]):.4f}")
                print(f"    >0.5: {(trans_s[lmask] > 0.5).sum()}/{lmask.sum()}")

print(f"\n--- XGBoost Score Distribution for BENIGN flows ---")
benign_mask = y == 0
print(f"  Mean: {xgb_s[benign_mask].mean():.4f}")
print(f"  >0.5 (FP): {(xgb_s[benign_mask] > 0.5).sum()}/{benign_mask.sum()}")
