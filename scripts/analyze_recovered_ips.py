import pandas as pd
import glob
import os

def analyze_day(day_name):
    path = f"extracted_features/{day_name}/*.csv"
    files = glob.glob(path)
    print(f"\nAnalyzing {day_name} ({len(files)} files)...")
    
    src_ips = pd.Series(dtype=str)
    dst_ips = pd.Series(dtype=str)
    
    # Sample first 20 files
    for f in files[:20]:
        try:
            # Try utf-16 first (for Wed-21 background)
            try:
                df = pd.read_csv(f, encoding='utf-16')
                if 'ip.src' not in df.columns: raise ValueError()
            except Exception:
                df = pd.read_csv(f, encoding='utf-8-sig')
            
            src_ips = pd.concat([src_ips, df['ip.src'].value_counts()])
            dst_ips = pd.concat([dst_ips, df['ip.dst'].value_counts()])
        except Exception:
            pass
            
    print("Top 10 Source IPs:")
    print(src_ips.groupby(src_ips.index).sum().sort_values(ascending=False).head(10))
    print("\nTop 10 Destination IPs:")
    print(dst_ips.groupby(dst_ips.index).sum().sort_values(ascending=False).head(10))

if __name__ == "__main__":
    analyze_day("Wednesday-21-02-2018")
    analyze_day("Thursday-15-02-2018")
