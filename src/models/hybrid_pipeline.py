import os
import torch
import numpy as np
import xgboost as xgb
import joblib
from src.models.seq_classifier import TransformerNIDS

class HybridNIDS:
    """Cascading NIDS: XGBoost (Stage 1) -> Stealth Pattern Filter -> Transformer (Stage 2)."""
    def __init__(self, xgb_path, transformer_path, scaler_path, device='cuda'):
        # 1. Load XGBoost (Loud attacks)
        self.xgb_model = xgb.Booster()
        self.xgb_model.load_model(xgb_path)
        
        # 2. Load Transformer (Stealthy sessions)
        self.device = device
        self.transformer = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
        if os.path.exists(transformer_path):
            self.transformer.load_state_dict(torch.load(transformer_path, map_location=device))
            print(f"Loaded Transformer weights from {transformer_path}")
        else:
            print("WARNING: Transformer weights not found. Running in XGBoost-only mode.")
            
        self.transformer.to(device).eval()
        
        # 3. Load Normalizer
        self.scaler = joblib.load(scaler_path)
        
        # 4. Hybrid Thresholds
        self.CONFIDENCE_THRESHOLD = 0.4 # Range 0.4-0.6 is "Unsure"
        self.STEALTH_PACKET_RATE = 5.0 # < 5 pkts/sec is a stealth signature
        self.STEALTH_AVG_PAYLOAD = 100.0 # < 100 bytes is a stealth signature

    def predict(self, flow_features, sequence_features=None):
        """
        Final decision logic.
        - flow_features: (8,) array of XGBoost-compatible metrics.
        - sequence_features: (200, 9) array of raw sequence packets.
        """
        # --- STAGE 1: XGBoost (Fast Filtering) ---
        dmatrix = xgb.DMatrix(flow_features.reshape(1, -1))
        xgb_score = self.xgb_model.predict(dmatrix)[0]
        
        # --- DECISION LOGIC: Cascading ---
        
        # 1. Immediate Alert (Loud Attack)
        if xgb_score > 0.9:
            return "ATTACK (Loud)", xgb_score
            
        # 2. Stealth Pattern Detection (The "Always-Verify" Rule)
        # Based on index 7 (packet_rate) and index 2 (frame.len_mean)
        is_stealth_prone = flow_features[7] < self.STEALTH_PACKET_RATE or \
                          flow_features[2] < self.STEALTH_AVG_PAYLOAD
                          
        # 3. Stage 2 Trigger: If XGBoost is "Unsure" OR if it's a Stealthy session
        is_unsure = 0.4 < xgb_score < 0.6
        
        if (is_unsure or is_stealth_prone) and sequence_features is not None:
            # --- STAGE 2: Transformer (Deep Verification) ---
            with torch.no_grad():
                seq_tensor = torch.tensor(sequence_features, dtype=torch.float32).unsqueeze(0).to(self.device)
                logit = self.transformer(seq_tensor)
                trans_score = torch.sigmoid(logit).item()
                
            # Combined Final score (Heuristic weighted)
            final_score = (0.7 * trans_score) + (0.3 * xgb_score)
            if final_score > 0.5:
                return "ATTACK (Stealth - Transformer Verified)", final_score
            else:
                return "BENIGN (Transformer Verified)", final_score

        # 4. Default: Return XGBoost result
        label = "ATTACK (XGBoost)" if xgb_score > 0.5 else "BENIGN (XGBoost)"
        return label, xgb_score

if __name__ == "__main__":
    # Test Architecture (Weights placeholder)
    print("Initializing Hybrid NIDS Architecture...")
    nids = HybridNIDS(
        xgb_path="models/xgboost_flow_v1.json",
        transformer_path="models/transformer_seq_v1.pth",
        scaler_path="models/flow_scaler.joblib"
    )
    print("Architecture Ready for Inference.")
