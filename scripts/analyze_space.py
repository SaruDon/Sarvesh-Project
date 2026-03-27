import os

base_dir = r"C:\Users\Student\cicids2018"

def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

print(f"{'Target Path':<80} | {'Size (GB)':<10}")
print("-" * 95)

# Check individual zip files in root
for item in os.listdir(base_dir):
    full_path = os.path.join(base_dir, item)
    if os.path.isfile(full_path) and item.endswith('.zip'):
        size_gb = os.path.getsize(full_path) / (1024**3)
        print(f"{item:<80} | {size_gb:.2f}")

# Check day directories
for item in os.listdir(base_dir):
    full_path = os.path.join(base_dir, item)
    if os.path.isdir(full_path) and item != "processed_dataset":
        size_gb = get_dir_size(full_path) / (1024**3)
        if size_gb > 0.1: # Only show significant sizes
            print(f"{item:<80} | {size_gb:.2f}")
