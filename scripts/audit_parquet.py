import pandas as pd
import glob
import os

def audit_day(day_name):
    path = f"c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/processed_dataset/{day_name}/*_flows.parquet"
    files = glob.glob(path)
    if not files:
        print(f"No files found for {day_name}")
        return
    
    total_benign = 0
    attack_counts = {}
    
    for f in files:
        df = pd.read_parquet(f)
        label_col = 'label'
        if 'label' not in df.columns:
            if 'label_<lambda>' in df.columns:
                label_col = 'label_<lambda>'
            else:
                print(f"File {os.path.basename(f)} is missing 'label' column!")
                break
        
        counts = df[label_col].value_counts()

        for label, count in counts.items():
            if label == 'Benign':
                total_benign += count
            else:
                attack_counts[label] = attack_counts.get(label, 0) + count
    
    print(f"Audit Results for {day_name}:")
    print(f"  Benign: {total_benign}")
    if attack_counts:
        for label, count in attack_counts.items():
            print(f"  {label}: {count}")
    else:
        print("  Attacks: NONE FOUND")

if __name__ == "__main__":
    target_days = [
        "Wednesday-14-02-2018",
        "Wednesday-21-02-2018",
        "Thursday-15-02-2018",
        "Thursday-01-03-2018", "Friday-23-02-2018", "Friday-02-03-2018", "Friday-16-02-2018"]
    for day in target_days:
        audit_day(day)
