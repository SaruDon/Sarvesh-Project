"""
Full attack-distribution audit across all training days.
Calculates exact Benign:Attack ratio to calibrate pos_weight.
"""
import glob, pandas as pd

days = [
    'Friday-02-03-2018', 'Friday-16-02-2018', 'Friday-23-02-2018',
    'Thursday-01-03-2018', 'Thursday-15-02-2018', 'Thursday-22-02-2018',
    'Tuesday-20-02-2018', 'Wednesday-14-02-2018', 'Wednesday-21-02-2018'
]

print("=== ATTACK DISTRIBUTION BY DAY ===")
total_b, total_a = 0, 0
all_attack_types = {}

for day in days:
    files = glob.glob(f"processed_dataset/{day}/*_flows.parquet")
    b, a = 0, 0
    day_attacks = {}
    for f in files:
        try:
            df = pd.read_parquet(f, columns=['label'])
            c = df['label'].value_counts()
            b += c.get('Benign', 0)
            for k, v in c[c.index != 'Benign'].items():
                a += v
                day_attacks[k] = day_attacks.get(k, 0) + v
                all_attack_types[k] = all_attack_types.get(k, 0) + v
        except:
            pass
    total_b += b
    total_a += a
    ratio = f"{b/a:.0f}:1" if a > 0 else "INF (Benign-only)"
    attacks_str = ", ".join(day_attacks.keys()) if day_attacks else "NONE"
    print(f"\n  {day}")
    print(f"    Benign={b:>8,}  Attack={a:>8,}  Ratio={ratio}")
    print(f"    Attacks: {attacks_str}")

print(f"\n{'='*55}")
print(f"  TOTAL ACROSS ALL DAYS")
print(f"{'='*55}")
print(f"  Total Benign : {total_b:,}")
print(f"  Total Attack : {total_a:,}")
if total_a > 0:
    overall_ratio = total_b / total_a
    print(f"  Overall B:A  : {overall_ratio:.1f}:1")
    print(f"\n  RECOMMENDED pos_weight = {overall_ratio:.0f}")
    print(f"  Current pos_weight     = 18")
    diff = abs(overall_ratio - 18)
    if diff < 5:
        print(f"  [OK] pos_weight=18 is correctly calibrated!")
    else:
        print(f"  [FIX NEEDED] Should be ~{overall_ratio:.0f}, not 18!")
else:
    print("  NO ATTACKS FOUND IN TRAINING DATA!")

print(f"\n  All Attack Types Found:")
for k, v in sorted(all_attack_types.items(), key=lambda x: -x[1]):
    print(f"    {k:35s}: {v:,}")
