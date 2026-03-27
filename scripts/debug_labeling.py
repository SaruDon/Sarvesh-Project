import pandas as pd
import os

def parse_attack_logs(log_path):
    logs = pd.read_csv(log_path)
    logs['start'] = pd.to_datetime(logs['Date'] + ' ' + logs['Start_Time'])
    logs['end'] = pd.to_datetime(logs['Date'] + ' ' + logs['End_Time'])
    return logs

def apply_labels(df, attack_logs, day_filter):
    df['label'] = 'Benign'
    day_logs = attack_logs[attack_logs['Date'] == day_filter]
    print(f"Applying labels for {day_filter}. Found {len(day_logs)} log entries.")
    
    for _, row in day_logs.iterrows():
        # Debug: check the mask conditions separately
        time_mask = (df['timestamp'] >= row['start']) & (df['timestamp'] <= row['end'])
        print(f"  Entry: {row['Attack_Type']} ({row['start']} to {row['end']}) target {row['Target_IP']}")
        print(f"  Rows in time range: {time_mask.sum()}")
        if time_mask.sum() > 0:
            print(f"  Sample IP.DST in range: {df.loc[time_mask, 'ip.dst'].unique()[:5]}")
            print(f"  Sample IP.SRC in range: {df.loc[time_mask, 'ip.src'].unique()[:5]}")
        
        target_mask = time_mask.copy()
        if 'Target_IP' in row and pd.notna(row['Target_IP']):
            t_ip = str(row['Target_IP'])
            # Check ip.src and ip.dst
            ip_src_mask = df['ip.src'].astype(str).str.startswith(t_ip, na=False)
            ip_dst_mask = df['ip.dst'].astype(str).str.startswith(t_ip, na=False)
            target_mask = time_mask & (ip_src_mask | ip_dst_mask)
            print(f"  IP SRC Matches: {ip_src_mask.sum()}")
            print(f"  IP DST Matches: {ip_dst_mask.sum()}")
            print(f"  Total Matches: {target_mask.sum()}")
        
        df.loc[target_mask, 'label'] = row['Attack_Type']
    return df

# Test on one specific file
csv_path = 'extracted_features/Wednesday-14-02-2018/capDESKTOP-AN3U28N-172.31.64.54.csv'
log_path = 'data/attack_logs.csv'

df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['frame.time_epoch'], unit='s')
attack_logs = parse_attack_logs(log_path)

df = apply_labels(df, attack_logs, "2018-02-14")
print("\nFinal Labels:")
print(df['label'].value_counts())
