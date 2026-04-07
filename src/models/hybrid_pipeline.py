import os
import torch
import numpy as np
import xgboost as xgb
import joblib
from src.models.seq_classifier import TransformerNIDS

class HybridNIDS:
    """Cascading NIDS: XGBoost (Stage 1) -> Stealth Pattern Filter -> Transformer (Stage 2)."""
    def __init__(self, xgb_path, transformer_path, flow_scaler_path, seq_scaler_path, device='cuda'):
        # 1. Load XGBoost (Loud attacks)
        self.xgb_model = xgb.Booster()
        self.xgb_model.load_model(xgb_path)
        
        # 2. Load Transformer (Stealthy sessions)
        self.device = device
        self.transformer = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
        if os.path.exists(transformer_path):
            self.transformer.load_state_dict(torch.load(transformer_path, map_location=device, weights_only=True))
            print(f"Loaded Transformer weights from {transformer_path}")
        else:
            print("WARNING: Transformer weights not found.")
            
        self.transformer.to(device).eval()
        
        # 3. Load Normalizers
        self.flow_scaler = joblib.load(flow_scaler_path)
        self.seq_scaler = joblib.load(seq_scaler_path)
        
        # 4. Hybrid Thresholds
        self.CONFIDENCE_THRESHOLD = 0.4 # Range 0.4-0.6 is "Unsure"
        self.STEALTH_PACKET_RATE = 5.0 # < 5 pkts/sec is a stealth signature
        self.STEALTH_AVG_PAYLOAD = 100.0 # < 100 bytes is a stealth signature

    def predict(self, flow_features, sequence_features=None):
        """Single-sample prediction (Legacy/Convenience)"""
        # Apply scaling
        flow_scaled = self.flow_scaler.transform(flow_features.reshape(1, -1))
        
        dmatrix = xgb.DMatrix(flow_scaled)
        xgb_score = self.xgb_model.predict(dmatrix)[0]
        
        # Loud Attack
        if xgb_score > 0.9:
            return "ATTACK (Loud)", xgb_score
            
        # Stealth Logic
        is_stealth_prone = flow_features[7] < self.STEALTH_PACKET_RATE or \
                          flow_features[2] < self.STEALTH_AVG_PAYLOAD
        is_unsure = 0.4 < xgb_score < 0.6
        
        if (is_unsure or is_stealth_prone) and sequence_features is not None:
            # Scale sequence
            seq_scaled = self.seq_scaler.transform(sequence_features.reshape(-1, 9)).reshape(200, 9)
            with torch.no_grad():
                seq_tensor = torch.tensor(seq_scaled, dtype=torch.float32).unsqueeze(0).to(self.device)
                logit = self.transformer(seq_tensor)
                trans_score = torch.sigmoid(logit).item()
                
            final_score = (0.7 * trans_score) + (0.3 * xgb_score)
            if final_score > 0.5:
                return "ATTACK (Stealth - Transformer Verified)", final_score
            else:
                return "BENIGN (Transformer Verified)", final_score

        return ("ATTACK (XGBoost)" if xgb_score > 0.5 else "BENIGN (XGBoost)"), xgb_score

    def predict_batch(self, X_flows_raw, X_seqs_raw=None):
        """Vectorized prediction: XGBoost for loud attacks, Transformer for everything else."""
        n = len(X_flows_raw)
        
        # 1. Scale and run XGBoost on all flows
        X_flows_scaled = self.flow_scaler.transform(X_flows_raw)
        dmatrix = xgb.DMatrix(X_flows_scaled)
        xgb_scores = self.xgb_model.predict(dmatrix)
        
        # 2. Initialize: XGBoost-only predictions
        preds = np.where(xgb_scores > 0.5, 1, 0)
        transformer_triggers = 0
        
        # 3. Loud attacks stay as XGBoost result (shortcut)
        loud_mask = xgb_scores > 0.9
        
        # 4. Everything else goes through Transformer if sequences available
        if X_seqs_raw is not None:
            # All non-loud samples get Transformer verification
            ti = np.where(~loud_mask)[0]
            if len(ti) > 0:
                transformer_triggers = len(ti)
                
                # Scale sequences: (N, 200, 9) -> (N*200, 9) -> scale -> (N, 200, 9)
                seqs_to_scale = X_seqs_raw[ti].reshape(-1, 9)
                seqs_scaled = self.seq_scaler.transform(seqs_to_scale).reshape(-1, 200, 9)
                
                # Batch through GPU (process in chunks to avoid OOM)
                BATCH = 2048
                all_trans_scores = []
                for start in range(0, len(seqs_scaled), BATCH):
                    batch = seqs_scaled[start:start+BATCH]
                    with torch.no_grad():
                        seq_tensor = torch.tensor(batch, dtype=torch.float32).to(self.device)
                        logits = self.transformer(seq_tensor)
                        scores = torch.sigmoid(logits).cpu().numpy()
                    all_trans_scores.append(scores)
                trans_scores = np.concatenate(all_trans_scores)
                
                # Combined score: Transformer-primary (0.6) + XGBoost-secondary (0.4)
                combined = (0.6 * trans_scores) + (0.4 * xgb_scores[ti])
                preds[ti] = np.where(combined > 0.5, 1, 0)
        
        return preds, xgb_scores, transformer_triggers

if __name__ == "__main__":
    print("Testing Hybrid NIDS Batch API...")
    nids = HybridNIDS(
        xgb_path="models/xgboost_flow_v1.json",
        transformer_path="models/transformer_seq_v1.pth",
        flow_scaler_path="models/flow_scaler.joblib",
        seq_scaler_path="models/seq_scaler.joblib"
    )
    print("Optimization Ready.")
