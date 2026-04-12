import torch
import numpy as np
import sys
import os
sys.path.append('.')
from src.models.seq_classifier import TransformerNIDS

def verify_hypothesis():
    print("="*70)
    print("HYPOTHESIS VERIFICATION: MODEL HEALTH AUDIT")
    print("="*70)
    
    weights_path = 'models/transformer_seq_v4_full.pth'
    if not os.path.exists(weights_path):
        print(f"FAILED: Weights file {weights_path} not found.")
        return

    model = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
    try:
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
        print(f"Loaded hypothesis weights.")
    except Exception as e:
        print(f"Error loading weights: {e}")
        return

    model.eval()
    
    # Prove non-constant logits (is the model alive?)
    with torch.no_grad():
        x1 = torch.zeros(1, 200, 9)
        x2 = torch.randn(1, 200, 9)
        x3 = torch.ones(1, 200, 9) * 0.5
        
        l1 = model(x1).item()
        l2 = model(x2).item()
        l3 = model(x3).item()
        
        print(f"Logits Analysis:")
        print(f"  Zero Input:   {l1:.6f}")
        print(f"  Random Input: {l2:.6f}")
        print(f"  Steady Input: {l3:.6f}")
        
        var = np.var([l1, l2, l3])
        if var < 1e-4:
            print(f"\n[!!!] HYPOTHESIS FAILED: Model is still collapsed (Variance={var:.8f})")
        else:
            print(f"\n[SUCCESS] HYPOTHESIS CONFIRMED: Model is reactive and non-collapsed (Variance={var:.8f})")
            print("The architectural stabilization worked!")
    print("="*70)

if __name__ == "__main__":
    verify_hypothesis()
