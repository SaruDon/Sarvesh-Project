import os
import glob
import pandas as pd

processed_dir = "processed_dataset"
days = [d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d)) and d not in ['pcap', 'Golden_Test_Set']]
days.sort()

print(f"{'Day':<25} | {'Flows':<10} | {'Sequences':<10} | {'Status':<8}")
print("-" * 65)

total_flows = 0
total_seqs = 0

for day in days:
    flow_files = glob.glob(os.path.join(processed_dir, day, "*_flows.parquet"))
    seq_files = glob.glob(os.path.join(processed_dir, day, "*_sequences.parquet"))
    
    flow_count = 0
    for f in flow_files:
        try:
            flow_count += pd.read_parquet(f, columns=['label']).shape[0]
        except Exception: pass
        
    seq_count = 0
    for s in seq_files:
        try:
            seq_count += pd.read_parquet(s, columns=['label']).shape[0]
        except Exception: pass
    
    status = "READY" if flow_count > 1000 and seq_count > 100 else "PARTIAL"
    if flow_count == 0: status = "EMPTY"
    
    print(f"{day:<25} | {flow_count:<10} | {seq_count:<10} | {status:<8}")
    total_flows += flow_count
    total_seqs += seq_count

print("-" * 65)
print(f"{'TOTAL':<25} | {total_flows:<10} | {total_seqs:<10} |")
