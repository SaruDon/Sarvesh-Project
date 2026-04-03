import os
import glob
import shutil
import random
from tqdm import tqdm

PROCESSED_DIR = "processed_dataset"
TEST_SET_DIR = os.path.join(PROCESSED_DIR, "Golden_Test_Set")
SPLIT_RATIO = 0.10 # 10% for testing

def perform_stratified_split():
    os.makedirs(TEST_SET_DIR, exist_ok=True)
    
    # Identify all day folders (excluding the test set itself)
    days = [d for d in os.listdir(PROCESSED_DIR) 
            if os.path.isdir(os.path.join(PROCESSED_DIR, d)) and d != "Golden_Test_Set" and d != "pcap"]
    
    print(f"Starting stratified split across {len(days)} dataset days...")
    
    total_moved = 0
    
    for day in days:
        day_path = os.path.join(PROCESSED_DIR, day)
        # Find all flow files in this day
        flow_files = glob.glob(os.path.join(day_path, "*_flows.parquet"))
        
        # Calculate how many to move (10%)
        num_to_move = max(1, int(len(flow_files) * SPLIT_RATIO))
        files_to_move = random.sample(flow_files, num_to_move)
        
        # Prepare target day directory in Test Set
        target_day_dir = os.path.join(TEST_SET_DIR, day)
        os.makedirs(target_day_dir, exist_ok=True)
        
        for flow_f in tqdm(files_to_move, desc=f"Moving {day}"):
            # 1. Move Flow File
            seq_f = flow_f.replace("_flows.parquet", "_sequences.parquet")
            
            # Move both Flow and Sequence pair
            try:
                shutil.move(flow_f, os.path.join(target_day_dir, os.path.basename(flow_f)))
                if os.path.exists(seq_f):
                    shutil.move(seq_f, os.path.join(target_day_dir, os.path.basename(seq_f)))
                total_moved += 1
            except Exception as e:
                print(f"Error moving {flow_f}: {e}")
                
    print(f"\nSplit Complete. Moved {total_moved} file pairs to {TEST_SET_DIR}")

if __name__ == "__main__":
    perform_stratified_split()
