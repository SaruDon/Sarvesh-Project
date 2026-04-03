import pandas as pd
import glob
import os

processed_dir = "processed_dataset"
days = [d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d))]
days.sort()

# Reference schemas
flow_schema = None
seq_schema = None
flow_ref_file = ""
seq_ref_file = ""

mismatches = []

print(f"Starting Schema Consistency Check...")
print("-" * 50)

for day in days:
    # Check Flows
    flow_files = glob.glob(os.path.join(processed_dir, day, "*_flows.parquet"))
    for f in flow_files:
        try:
            df = pd.read_parquet(f)
            # Standardize label col name for schema comparison if needed
            if 'label_<lambda>' in df.columns:
                df = df.rename(columns={'label_<lambda>': 'label'})
            
            current_schema = list(df.columns)
            current_schema.sort()
            
            if flow_schema is None:
                flow_schema = current_schema
                flow_ref_file = f
                print(f"Set Flow Reference Schema from {f}")
            elif current_schema != flow_schema:
                mismatches.append(f"FLOW Schema Mismatch in {f}\nExpected: {flow_schema}\nFound: {current_schema}")
        except Exception as e:
            mismatches.append(f"Error reading {f}: {e}")

    # Check Sequences
    seq_files = glob.glob(os.path.join(processed_dir, day, "*_sequences.parquet"))
    for f in seq_files:
        try:
            df = pd.read_parquet(f)
            current_schema = list(df.columns)
            current_schema.sort()
            
            if seq_schema is None:
                seq_schema = current_schema
                seq_ref_file = f
                print(f"Set Sequence Reference Schema from {f}")
            elif current_schema != seq_schema:
                mismatches.append(f"SEQ Schema Mismatch in {f}\nExpected: {seq_schema}\nFound: {current_schema}")
        except Exception as e:
            mismatches.append(f"Error reading {f}: {e}")

# Save mismatches log FIRST before printing potentially problematic chars
with open("scripts/schema_audit_log.txt", "w") as out:
    out.write("\n".join(mismatches))

print("-" * 50)
if not mismatches:
    print("SUCCESS: All schemas are consistent!")
else:
    print(f"FOUND {len(mismatches)} mismatches (logged to scripts/schema_audit_log.txt):")
    for m in mismatches[:5]: # Show first 5
        print(f"\n{m}")
