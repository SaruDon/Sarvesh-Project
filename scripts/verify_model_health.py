import torch
import numpy as np
import sys
import os
sys.path.append('.')
from src.models.seq_classifier import TransformerNIDS

def verify_model_health():
    try:
        model = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
        weights_path = 'models/transformer_seq_v4_full.pth'
        
        if os.path.exists(weights_path):
            model.load_state_dict(torch.load(weights_path, map_location='cpu'))
            print(f"Loaded weights from {weights_path}")
        else:
            print("No weights found!")
            return

        model.eval()
        
        # Test 1: Zero vs Random Input
        with torch.no_grad():
            x1 = torch.zeros(1, 200, 9)
            x2 = torch.randn(1, 200, 9)
            out1 = model(x1).item()
            out2 = model(x2).item()
            print(f"Zero Input Logit: {out1:.6f}")
            print(f"Random Input Logit: {out2:.6f}")
            
            if abs(out1 - out2) < 1e-4:
                print("!!! WARNING: Model output is constant! The weights are collapsed or invalid.")
            else:
                print("Model output is varying. Good.")

        # Test 2: Check weight norms
        for name, param in model.named_parameters():
            if param.requires_grad:
                print(f"Layer {name}: Mean={param.data.mean():.6f}, Std={param.data.std():.6f}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_model_health()
