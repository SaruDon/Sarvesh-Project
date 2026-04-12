import os
import torch
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from src.models.seq_classifier import TransformerNIDS

class HybridNIDS:
    """Cascading NIDS: XGBoost (Stage 1) -> Stealth Pattern Filter -> Transformer (Stage 2)."""
    
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

    def __init__(self, xgb_path="models/xgboost_flow_v4.json", 
                 transformer_path="models/transformer_seq_v4_full.pth", 
                 flow_scaler_path="models/flow_scaler_v4.joblib", 
                 seq_scaler_path="models/seq_scaler.joblib", 
                 device='cuda'):
        # 1. Load XGBoost (Loud attacks)
        self.xgb_model = xgb.Booster()
        if os.path.exists(xgb_path):
            self.xgb_model.load_model(xgb_path)
        else:
            print(f"WARNING: XGBoost model not found at {xgb_path}")
        
        # 2. Load Transformer (Stealthy sessions)
        self.device = device
        self.transformer = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
        if os.path.exists(transformer_path):
            self.transformer.load_state_dict(torch.load(transformer_path, map_location=device, weights_only=True))
            print(f"Loaded Transformer weights from {transformer_path}")
        else:
            print(f"WARNING: Transformer weights not found at {transformer_path}")
            
        self.transformer.to(device).eval()
        
        # 3. Load Normalizers
        self.flow_scaler = joblib.load(flow_scaler_path) if os.path.exists(flow_scaler_path) else None
        self.seq_scaler = joblib.load(seq_scaler_path) if os.path.exists(seq_scaler_path) else None
        
        # 4. Hybrid Thresholds
        self.CONFIDENCE_THRESHOLD = 0.4 # Range 0.4-0.6 is "Unsure"
        self.STEALTH_PACKET_RATE = 5.0 # < 5 pkts/sec is a stealth signature
        self.STEALTH_AVG_PAYLOAD = 100.0 # < 100 bytes is a stealth signature

    def engineer_features(self, df):
        """Standard 43-feature engineering for V4 models."""
        features = pd.DataFrame(index=df.index)

        # Baseline
        features['packet_count'] = df['frame.len_count'].fillna(0)
        features['total_bytes'] = df['frame.len_sum'].fillna(0)
        features['avg_packet_size'] = df['frame.len_mean'].fillna(0)
        features['packet_size_std'] = df['frame.len_std'].fillna(0)
        features['ttl_mean'] = df['ip.ttl_mean'].fillna(0)
        features['window_size_mean'] = df['tcp.window_size_value_mean'].fillna(0)
        features['flow_duration'] = df['flow_duration_sec'].fillna(0)
        features['packet_rate'] = df['packet_rate'].fillna(0)

        # Logs
        features['log_packet_count'] = np.log1p(features['packet_count'])
        features['log_total_bytes'] = np.log1p(features['total_bytes'])
        features['log_packet_rate'] = np.log1p(features['packet_rate'])
        features['log_duration'] = np.log1p(features['flow_duration'])

        # Rates & CV
        features['bytes_per_sec'] = features['total_bytes'] / features['flow_duration'].replace(0, 0.001)
        features['log_bytes_per_sec'] = np.log1p(features['bytes_per_sec'].clip(upper=1e9))
        features['packet_size_cv'] = (features['packet_size_std'] / features['avg_packet_size'].replace(0, 0.001)).clip(upper=100)
        
        # Indicators
        features['is_single_packet'] = (features['packet_count'] == 1).astype(np.float32)
        features['is_micro_flow'] = (features['packet_count'] <= 5).astype(np.float32)
        features['is_large_flow'] = (features['packet_count'] > 100).astype(np.float32)
        features['is_small_payload'] = (features['avg_packet_size'] < 100).astype(np.float32)

        # Proto
        proto = df['ip.proto'].fillna(0).astype(int)
        features['proto_tcp'] = (proto == 6).astype(np.float32)
        features['proto_udp'] = (proto == 17).astype(np.float32)
        features['proto_icmp'] = (proto == 1).astype(np.float32)
        features['proto_other'] = ((proto != 6) & (proto != 17) & (proto != 1)).astype(np.float32)

        # Ports
        srcport = df['tcp.srcport'].fillna(0).astype(int)
        dstport = df['tcp.dstport'].fillna(0).astype(int)

        for name, ports in self.WELL_KNOWN_PORTS.items():
            features[f'dst_is_{name}'] = dstport.isin(ports).astype(np.float32)

        features['src_ephemeral'] = (srcport > 1024).astype(np.float32)
        features['dst_ephemeral'] = (dstport > 1024).astype(np.float32)
        features['both_ephemeral'] = ((srcport > 1024) & (dstport > 1024)).astype(np.float32)
        features['dstport_value'] = dstport.clip(upper=65535).astype(np.float32)
        features['srcport_value'] = srcport.clip(upper=65535).astype(np.float32)

        # Signatures
        features['low_ttl'] = (features['ttl_mean'] < 32).astype(np.float32)
        ttl_rounded = features['ttl_mean'].round()
        features['unusual_ttl'] = (~ttl_rounded.isin([32, 64, 128, 255])).astype(np.float32)
        features['zero_window'] = (features['window_size_mean'] == 0).astype(np.float32)
        features['large_window'] = (features['window_size_mean'] > 60000).astype(np.float32)
        features['bytes_x_packets'] = np.log1p(features['total_bytes'] * features['packet_count'])
        features['rate_x_size'] = features['packet_rate'] * features['avg_packet_size'] / 1e6

        return features.fillna(0).replace([np.inf, -np.inf], 0)

    def predict(self, df_row, sequence_features=None):
        """Single-sample prediction using DataFrame row input."""
        if not isinstance(df_row, pd.DataFrame):
            # Try to convert if it's a Series
            df_row = pd.DataFrame([df_row])
            
        # 1. Engineer Features
        X_engineered = self.engineer_features(df_row)
        
        # 2. Scale
        X_scaled = self.flow_scaler.transform(X_engineered)
        
        dmatrix = xgb.DMatrix(X_scaled, feature_names=list(X_engineered.columns))
        xgb_score = self.xgb_model.predict(dmatrix)[0]
        
        # If multi-class, we take the max of attack classes or total probability
        if len(xgb_score.shape) > 0: # Multi-class
            # Benign is index 0 (usually)
            xgb_score = 1.0 - xgb_score[0]

        # Loud Attack
        if xgb_score > 0.9:
            return "ATTACK (Loud)", xgb_score
            
        # Stealth Logic
        is_stealth_prone = df_row['packet_rate'].iloc[0] < self.STEALTH_PACKET_RATE or \
                          df_row['frame.len_mean'].iloc[0] < self.STEALTH_AVG_PAYLOAD
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

    def predict_batch(self, df_flows, X_seqs_raw=None):
        """
        Vectorized prediction: Wide-Net Triage.
        Forces the Transformer to verify ALL XGBoost alerts to suppress over-confident FPs.
        """
        # 1. Engineer Features
        X_engineered = self.engineer_features(df_flows)
        feature_names = list(X_engineered.columns)
        
        # 2. Scale and run XGBoost
        X_flows_scaled = self.flow_scaler.transform(X_engineered)
        dmatrix = xgb.DMatrix(X_flows_scaled, feature_names=feature_names)
        xgb_raw = self.xgb_model.predict(dmatrix)
        
        # Handle Multi-class if necessary (1 - probability of class 0/Benign)
        if len(xgb_raw.shape) > 1:
            xgb_scores = 1.0 - xgb_raw[:, 0]
        else:
            xgb_scores = xgb_raw
        
        # 3. Initialize: Standard XGBoost prediction
        preds = np.where(xgb_scores > 0.5, 1, 0)
        transformer_triggers = 0
        
        # 4. WIDE-NET TRIAGE: Trigger Stage 2 for EVERYTHING XGBoost thinks is an attack
        # OR anything where XGBoost is moderately unsure (>0.1)
        if X_seqs_raw is not None:
            ti = np.where(xgb_scores > 0.1)[0]
            
            if len(ti) > 0:
                transformer_triggers = len(ti)
                
                # Scale sequences
                seqs_to_scale = X_seqs_raw[ti].reshape(-1, 9)
                seqs_scaled = self.seq_scaler.transform(seqs_to_scale).reshape(-1, 200, 9)
                
                # Batch through GPU
                BATCH = 2048
                all_trans_scores = []
                for start in range(0, len(seqs_scaled), BATCH):
                    batch = seqs_scaled[start:start+BATCH]
                    with torch.no_grad():
                        seq_tensor = torch.tensor(batch, dtype=torch.float32).to(self.device)
                        logits = self.transformer(seq_tensor)
                        ts = torch.sigmoid(logits).cpu().numpy()
                    all_trans_scores.append(ts)
                trans_scores = np.concatenate(all_trans_scores).flatten()
                
                # --- THE PRECISION SHIELD: SANITY CHECK FILTER ---
                for i, idx in enumerate(ti):
                    t_score = trans_scores[i]
                    x_score = xgb_scores[idx]
                    
                    # TIER 1: SANITY CHECK (VETO POWER)
                    # If the Transformer doesn't see suspicious patterns (<0.15 RAW)
                    # it Vetoes any alert from XGBoost.
                    if t_score < 0.15:
                        preds[idx] = 0
                        continue
                    
                    # TIER 2: CONSENSUS (For suspicious signals)
                    # Calibrate for 0.15 -> 0.35 range
                    t_cal = np.clip(t_score * 2.5, 0.0, 1.0)
                    combined = (0.7 * t_cal) + (0.3 * x_score)
                    
                    # Decision: Require moderate evidence (0.45) if it passed the filter
                    preds[idx] = 1 if combined > 0.45 else 0
        
        return preds, xgb_scores, transformer_triggers

if __name__ == "__main__":
    print("Testing Hybrid NIDS Batch API...")
    nids = HybridNIDS()
    print("Optimization Ready.")

