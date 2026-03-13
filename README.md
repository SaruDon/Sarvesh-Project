# Hybrid NIDS Project: CIC-IDS-2018 Implementation

## Project Context
Developing a state-of-the-art Hybrid Network Intrusion Detection System (NIDS) using:
1. **XGBoost Layer**: Flow-based detection.
2. **Transformer Layer**: Packet Sequence patterns.
3. **Explainability**: SHAP/Attention maps.

## Hardware & Environment
- **Workstation**: i9 + 32GB RAM.
- **Main Storage**: /mnt/cicids2018/ (Windows Partition).
- **Workspace**: /home/a10/Desktop/Sarvesh Project (symlinked and managed for space).

## Key Files
- `run_nids_pipeline.sh`: Master entry point (resumes download, extracts, runs EDA).
- `extract_pcap.sh`: Updated tshark script (includes UDP).
- `attack_logs.csv`: Official attack schedule for Friday, Mar 2, 2018.
- `eda_initial.py`: Statistical analysis.
- `dataset_builder.py`: Flow/Sequence generation.

## Current State
- **PCAP Download**: In progress on /mnt/ (approx. 2-3 hours remaining).
- **Attack Schedule**: 10:02-11:02 (Botnet), 14:00-15:00 (Botnet).
