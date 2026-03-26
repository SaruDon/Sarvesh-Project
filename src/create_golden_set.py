import os
import shutil
import random
import glob

def setup_golden_set(source_day, sample_rate=0.05):
    """
    Samples files from a specific day and copies them to the Golden Test Set.
    """
    base_dir = r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project"
    source_dir = os.path.join(base_dir, "processed_dataset", source_day)
    golden_dir = os.path.join(base_dir, "processed_dataset", "Golden_Test_Set")
    
    if not os.path.exists(golden_dir):
        os.makedirs(golden_dir)
        print(f"Created Golden Set directory: {golden_dir}")
        
    # Find all flow and sequence pairs
    all_files = glob.glob(os.path.join(source_dir, "*.parquet"))
    if not all_files:
        print(f"No processed files found in {source_dir}")
        return
        
    # We group by original filename to keep flow+sequence pairs together
    basenames = set([f.split("_flows.parquet")[0].split("_sequences.parquet")[0] for f in all_files])
    
    # Calculate how many to sample
    num_to_sample = max(1, int(len(basenames) * sample_rate))
    sampled_basenames = random.sample(list(basenames), num_to_sample)
    
    print(f"Sampling {num_to_sample} file pairs (out of {len(basenames)}) from {source_day}...")
    
    count = 0
    for base in sampled_basenames:
        # Construct exact filenames
        f_flow = base + "_flows.parquet"
        f_seq = base + "_sequences.parquet"
        
        # Copy to golden set
        for f_path in [f_flow, f_seq]:
            if os.path.exists(f_path):
                dest = os.path.join(golden_dir, os.path.basename(f_path))
                shutil.copy2(f_path, dest)
                count += 1
                
    print(f"Golden Set Update Complete: Added {count} files from {source_day}.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        setup_golden_set(sys.argv[1])
    else:
        print("Usage: python create_golden_set.py <Day-Name> (e.g. Friday-02-03-2018)")
