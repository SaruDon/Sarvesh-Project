import pandas as pd
import torch
import numpy as np
import sys
import os
sys.path.append('.')
from src.models.hybrid_pipeline import HybridNIDS

def brute_force_sweep():
    try:
        nids = HybridNIDS()
        # Find three diverse files
        files = [
            'processed_dataset/Golden_Test_Set/Wednesday-28-02-2018/capDESKTOP-AN3U28N-172.31.64.115_flows.parquet',
            'processed_dataset/Golden_Test_Set/Friday-02-03-2018/capDESKTOP-AN3U28N-172.31.64.111_flows.parquet',
            'processed_dataset/Golden_Test_Set/Tuesday-20-02-2018/capDESKTOP-AN3U28N-172.31.64.65_flows.parquet'
        ]
        
        all_t_benign = []
        all_t_attack = []
        
        for file_f in files:
            file_s = file_f.replace('_flows.parquet', '_sequences.parquet')
            if not os.path.exists(file_f) or not os.path.exists(file_s): continue
            
            df_f = pd.read_parquet(file_f)
            df_s = pd.read_parquet(file_s)
            joined = df_f.join(df_s, how='inner', rsuffix='_s')
            
            benign = joined[joined['label'] == 'Benign']
            attacks = joined[joined['label'] != 'Benign']
            
            if len(benign) > 0:
                X_seq = np.stack(benign['sequence_features'].values).reshape(-1, 200, 9)
                X_scaled = nids.seq_scaler.transform(X_seq.reshape(-1,9)).reshape(-1, 200, 9)
                with torch.no_grad():
                    logits = nids.transformer(torch.tensor(X_scaled, dtype=torch.float32).to(nids.device))
                    all_t_benign.extend(torch.sigmoid(logits).cpu().numpy().tolist())
                    
            if len(attacks) > 0:
                X_seq_a = np.stack(attacks['sequence_features'].values).reshape(-1, 200, 9)
                X_scaled_a = nids.seq_scaler.transform(X_seq_a.reshape(-1,9)).reshape(-1, 200, 9)
                with torch.no_grad():
                    logits_a = nids.transformer(torch.tensor(X_scaled_a, dtype=torch.float32).to(nids.device))
                    all_t_attack.extend(torch.sigmoid(logits_a).cpu().numpy().tolist())

        t_benign = np.array(all_t_benign)
        t_attack = np.array(all_t_attack)
        
        print(f"Total Swept Samples: {len(t_benign)} Benign, {len(t_attack)} Attack")
        
        for thresh in [0.13, 0.15, 0.17, 0.19, 0.21, 0.23, 0.25]:
            fp_rate = (t_benign > thresh).mean()
            recall = (t_attack > thresh).mean()
            print(f"Thresh {thresh:.2f}: FP Rate={fp_rate:.2%}, Recall={recall:.2%}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    brute_force_sweep()
