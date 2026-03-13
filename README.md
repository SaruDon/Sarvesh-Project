# Hybrid NIDS Project: CIC-IDS-2018 Implementation

## Project Context
Developing a state-of-the-art Hybrid Network Intrusion Detection System (NIDS) using:
1. **XGBoost Layer**: Flow-based detection.
2. **Transformer Layer**: Packet Sequence patterns.
3. **Explainability**: SHAP/Attention maps.

## Hardware & Environment
- **Workstation**: i9 + 32GB RAM.
- **Local Data Storage**: `/mnt/cicids2018/` (Mounted Windows NTFS Partition).
- **Remote Data Source**: `s3://cse-cic-ids2018/Original Network Traffic and Log data`
- **Workspace**: `/home/a10/Desktop/Sarvesh Project` (Git Root).

## Key Files
- `run_nids_pipeline.sh`: Master entry point (resumes download, extracts, runs EDA).
- `extract_pcap.sh`: Updated tshark script (includes UDP).
- `attack_logs.csv`: Official attack schedule for Friday, Mar 2, 2018.
- `eda_initial.py`: Statistical analysis.
- `dataset_builder.py`: Flow/Sequence generation.

## Current State
- **PCAP Download**: In progress on /mnt/ (approx. 2-3 hours remaining).
- **Attack Schedule**: 10:02-11:02 (Botnet), 14:00-15:00 (Botnet).

## Download Progress Reference (Snapshot 2026-03-13)
```text
[#8beb1c 16GiB/41GiB(38%) CN:8 DL:10MiB ETA:43m2s]
[#8beb1c 16GiB/41GiB(40%) CN:8 DL:11MiB ETA:37m52s]
[#8beb1c 17GiB/41GiB(41%) CN:8 DL:9.4MiB ETA:44m]
[#8beb1c 17GiB/41GiB(43%) CN:8 DL:9.8MiB ETA:41m7s]
[#8beb1c 18GiB/41GiB(44%) CN:8 DL:7.0MiB ETA:56m41s]
[#8beb1c 18GiB/41GiB(45%) CN:8 DL:11MiB ETA:34m30s]
[#8beb1c 19GiB/41GiB(46%) CN:8 DL:6.7MiB ETA:56m12s]
[#8beb1c 19GiB/41GiB(47%) CN:8 DL:5.1MiB ETA:1h12m22s]
```
