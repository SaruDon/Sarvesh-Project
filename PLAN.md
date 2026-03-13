# Hybrid NIDS Project: Implementation Plan & Progress

## Status: Day 1 Complete (2026-03-13)

### ✅ Accomplishments
1. **Environment Setup**: 
   - Installed Python 3.12, AWS CLI, and aria2.
   - Configured global PATH for Python and Wireshark (`tshark`).
   - Created `venv` with `pandas`, `numpy`, `scapy`, `pyarrow`, `seaborn`, and `tqdm`.
2. **Data Relocation & Management**: 
   - Moved dataset to `C:\Users\Student\cicids2018` to resolve `TrustedInstaller` permission issues.
   - Verified relocation via `robocopy` migration logs.
   - Identified missing files on S3 and created `download_missing.ps1`.
3. **Wireshark Extraction Verified**:
   - Developed `extract_pcap.ps1` using native Windows `tshark`.
   - **Technical Proof**: Verified pipeline with a synthetic PCAP. Extraction successful for core features:
     ```csv
     frame.number,frame.time_relative,frame.len,ip.src,ip.dst,ip.proto,tcp.srcport,tcp.dstport,tcp.flags,udp.srcport,udp.dstport
     "1","0.000000000","40","192.168.10.5","192.168.1.10","6","1234","80","0x0002",,
     "2","0.100000000","28","192.168.10.6","192.168.1.11","17",,,,"5678","53"
     ```
4. **Automation Orchestration**:
   - Created `run_nids_pipeline.ps1` as the master orchestrator for Windows.

## Immediate Next Steps (Pending Data Completion)
1. **Full Extraction**: Run `extract_pcap.ps1` once PCAP downloads finish.
2. **Initial EDA**: Execute `eda_initial.py` to analyze extracted CSVs.
3. **Dataset Building**: Run `dataset_builder.py` to generate labeled Parquet files for training.

## Future Goals
- Implement XGBoost (Flow-based) and Transformer (Sequence-based) layers.
- Generate SHAP/Attention maps for explainability.

