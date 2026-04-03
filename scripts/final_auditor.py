import pandas as pd
import glob
import os

processed_dir = "processed_dataset"
days = [d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d))]
days.sort()

# Stats storage
all_stats = []

print(f"{'Day':<25} | {'Type':<10} | {'Label':<20} | {'Count':<10}")
print("-" * 75)

for day in days:
    for mode in ["flows", "sequences"]:
        path = os.path.join(processed_dir, day, f"*_{mode}.parquet")
        files = glob.glob(path)
        if not files:
            continue
        
        all_labels = []
        schema = None
        for f in files:
            try:
                df = pd.read_parquet(f)
                label_col = 'label' if 'label' in df.columns else 'label_<lambda>'
                if label_col in df.columns:
                    all_labels.append(df[label_col].value_counts())
                
                # Check schema consistency
                if schema is None:
                    schema = set(df.columns)
            except:
                pass
                
        if all_labels:
            counts = pd.concat(all_labels).groupby(level=0).sum()
            for label, count in counts.items():
                print(f"{day:<25} | {mode:<10} | {label:<20} | {count:<10}")
                all_stats.append({'day': day, 'mode': mode, 'label': label, 'count': count, 'cols': len(schema)})

# Save summary for later use
pd.DataFrame(all_stats).to_csv("scripts/final_dataset_stats.csv", index=False)
