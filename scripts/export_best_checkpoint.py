"""
Export the best Epoch-1 checkpoint weights to the .pth file
that evaluate_final.py expects.
"""
import torch
import glob
import os
import sys
sys.path.insert(0, ".")

from src.models.seq_classifier import TransformerNIDS

# Best checkpoint - Epoch 1, lowest loss (0.15)
BEST_CKPT = "models/checkpoints_production/transformer-v4-prod-epoch=01-train_loss=0.15.ckpt"
OUTPUT_PATH = "models/transformer_seq_v4_full.pth"

if not os.path.exists(BEST_CKPT):
    print(f"ERROR: Checkpoint not found: {BEST_CKPT}")
    print("Available checkpoints:")
    for f in glob.glob("models/checkpoints_production/*.ckpt"):
        print(f"  {f}")
    sys.exit(1)

print(f"Loading best checkpoint: {BEST_CKPT}")
model = TransformerNIDS.load_from_checkpoint(BEST_CKPT, input_dim=9, d_model=64, nhead=4, num_layers=2)
model.eval()

# Export just the state dict (what evaluate_final.py loads)
torch.save(model.state_dict(), OUTPUT_PATH)
print(f"[OK] Exported to: {OUTPUT_PATH}")
print("     This is your BEST model from Epoch 1 (loss=0.15)")
print("     Ready for evaluation on the 6.8M Golden Test Set.")
