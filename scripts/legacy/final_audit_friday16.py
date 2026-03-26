import pandas as pd
import glob
import os

processed_dir = r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\processed_dataset\Friday-16-02-2018"
extract_dir = r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\extracted_features\Friday-16-02-2018"

files = glob.glob(os.path.join(processed_dir, "*_flows.parquet"))
csv_files = glob.glob(os.path.join(extract_dir, "*.csv"))

print(f"--- Data Integrity Audit: Friday-16 ---")
print(f"Total PCAP Fragments (from CSV list): {len(csv_files)}")
print(f"Total Processed Fragments (Parquet pairs): {len(files)}")

# 1. Completeness Check
if len(files) < len(csv_files):
    print(f"WARNING: Missing {len(csv_files) - len(files)} fragments in processed output!")
else:
    print("SUCCESS: Fragment parity verified.")

# 2. Statistical & Label Check
all_labels = {}
null_by_col = None
total_rows = 0

for f in files:
    df = pd.read_parquet(f)
    if null_by_col is None: null_by_col = df.isnull().sum() * 0
    null_by_col += df.isnull().sum()
    total_rows += len(df)
    
    # Label count
    label_col = 'label' if 'label' in df.columns else 'label_<lambda>'
    counts = df[label_col].value_counts().to_dict()
    for lab, count in counts.items():
        all_labels[lab] = all_labels.get(lab, 0) + count

print(f"\nFinal Statistics:")
print(f"Total Flows: {total_rows}")
print(f"Label Distribution: {all_labels}")
print(f"\nNull counts by column:")
print(null_by_col[null_by_col > 0])

# 3. Specific Attack Match
expected_attacks = ['DDoS-LOIC-HTTP', 'DDoS-HOIC']
missing_attacks = [a for a in expected_attacks if a not in all_labels]
if missing_attacks:
    print(f"ERR: Missing attack labels: {missing_attacks}")
else:
    print(f"SUCCESS: All expected attack types ({expected_attacks}) are present.")

# Check if nulls are only in expected columns (std)
std_cols = [c for c in null_by_col.index if 'std' in c]
unexpected_nulls = null_by_col.drop(std_cols, errors='ignore')
unexpected_nulls = unexpected_nulls[unexpected_nulls > 0]

if unexpected_nulls.empty and not missing_attacks:
    print("\nCONCLUSION: Data is VALID and CORRECT (Nulls are only in statistical 'std' columns).")
else:
    print("\nCONCLUSION: Unexpected data issues found:")
    print(unexpected_nulls)
