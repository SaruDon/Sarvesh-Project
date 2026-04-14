"""
Quick diagnostic: check what the Transformer is actually outputting
on a sample of Golden Test Set sequences.
"""
import torch
import numpy as np
import pandas as pd
import glob
import sys
sys.path.insert(0, ".")

from src.models.seq_classifier import TransformerNIDS

MODEL_PATH = "models/transformer_seq_v4_full.pth"
TEST_DIR = "processed_dataset/Golden_Test_Set"

print("Loading model...")
model = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu', weights_only=False))
model.eval()

# Load a sample of sequences
seq_files = glob.glob(f"{TEST_DIR}/**/*_sequences.parquet", recursive=True)[:3]

with torch.no_grad():
    all_logits = []
    all_labels = []
    for sf in seq_files:
        df = pd.read_parquet(sf)
        if 'sequence_features' not in df.columns or 'label' not in df.columns:
            continue
        seqs = np.stack(df['sequence_features'].values[:200]).reshape(-1, 200, 9)
        x = torch.tensor(seqs, dtype=torch.float32)
        logits = model(x).squeeze(-1)
        probs = torch.sigmoid(logits)
        all_logits.extend(logits.numpy().tolist())
        all_labels.extend(df['label'].values[:200].tolist())
        print(f"File: {sf.split('/')[-1]}")
        print(f"  Logit range: {logits.min():.4f} to {logits.max():.4f}")
        print(f"  Prob range:  {probs.min():.4f} to {probs.max():.4f}")
        print(f"  Mean prob:   {probs.mean():.4f}")
        attack_mask = [l != 'Benign' for l in df['label'].values[:200]]
        if any(attack_mask):
            attack_probs = probs[attack_mask]
            print(f"  Attack prob mean: {attack_probs.mean():.4f}")

print(f"\nOverall logit range: {min(all_logits):.4f} to {max(all_logits):.4f}")
print(f"Overall logit mean: {np.mean(all_logits):.4f}")
if np.std(all_logits) < 0.1:
    print("\n[COLLAPSE CONFIRMED] All logits are near-constant. Model is not discriminating.")
else:
    print(f"\n[HEALTHY] Logit std={np.std(all_logits):.4f}. Model IS discriminating.")
    print("Problem is in the THRESHOLD, not the model itself.")
