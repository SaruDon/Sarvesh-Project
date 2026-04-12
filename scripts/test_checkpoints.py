import torch
import numpy as np
import os
import sys
sys.path.append('.')
from src.models.seq_classifier import TransformerNIDS

def test_checkpoints():
    model = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
    ckpts = [
        'models/checkpoints/transformer-v4-epoch=03-train_loss=0.29.ckpt',
        'models/checkpoints/transformer-v4-epoch=06-train_loss=0.27.ckpt',
        'models/checkpoints/transformer-v4-epoch=07-train_loss=0.30.ckpt'
    ]
    
    for ckpt in ckpts:
        if not os.path.exists(ckpt): continue
        print(f"\nTesting {ckpt}:")
        try:
            # Map-location handling for Lightning checkpoints
            d = torch.load(ckpt, map_location='cpu')
            # Look for state_dict in the lightning checkpoint
            sd = d.get('state_dict', d)
            # Remove 'model.' prefix if present
            sd = {k.replace('model.', ''): v for k, v in sd.items()}
            
            model.load_state_dict(sd, strict=False)
            model.eval()
            
            with torch.no_grad():
                x1 = torch.zeros(1, 200, 9)
                x2 = torch.randn(1, 200, 9)
                out1 = model(x1).item()
                out2 = model(x2).item()
                print(f"  Zero Input Logit: {out1:.4f}")
                print(f"  Rand Input Logit: {out2:.4f}")
                print(f"  Diff: {abs(out1-out2):.6f}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_checkpoints()
