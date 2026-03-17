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

## Status: Day 2 Progress (2026-03-16)

### ✅ Accomplishments
1. **Pipeline Verification**:
   - Verified `extract_pcap.ps1`, `eda_initial.py`, and `dataset_builder.py` on synthetic data.
   - Fixed `tcp.flags` hex-to-int conversion and pandas frequency string deprecations.
2. **Real Data Processing (Botnet)**:
   - Successfully unzipped 44GB `Friday-02-03-2018-pcap.zip`.
   - Extracted features from the first 3 partitions of the real dataset.
   - Generated **16-feature flows** (XGBoost) and **200x9 sequences** (Transformer).
3. **Advanced Feature Engineering**:
   - Integrated `ip.ttl`, `tcp.window_size_value`, `packet_direction`, and `payload_ratio`.
   - Switched to **session-based sliding windows** to capture long-term attack behavior.

## Status: Day 3 Complete (2026-03-17)

### ✅ Accomplishments
1. **Large Dataset Processing (Brute Force - Friday-23)**:
   - Successfully unzipped 65GB `Friday-23-02-2018-pcap.zip` (450 PCAP files).
   - Fixed `extract_pcap.ps1` to correctly handle subfolders and trial limits.
   - Extracted features from 3 trial partitions; built labeled flows (**49,154**) and sequences (**13,778**).
2. **Analysis & Visualization**:
   - Generated **30 detailed EDA plots** for Friday-23 (Protocols, Packet Rates, Port Entropy).
   - Created visual `walkthrough.md` in the artifact directory.
3. **Data Quality & Integrity**:
   - Identified and skipped corrupted files in `Friday-16`.
   - Verified 100% labeling consistency across processed trial partitions.
4. **Project Documentation**:
   - Updated `README.md` with extensive project architecture and data mapping details.

### 📊 Dataset Processing Checklist
- [x] **Friday-02-03-2018 (Botnet)**: 
  - [x] Download PCAP
  - [x] Unzip Archive
  - [x] Feature Extraction (3 partitions trial complete)
  - [x] EDA & Dataset Building
- [x] **Friday-16-02-2018 (DDoS)**:
  - [x] Download PCAP
  - [x] Unzip Archive
  - [x] Process healthy partitions (Trial complete)
- [x] **Friday-23-02-2018 (Brute Force)**:
  - [x] Download PCAP
  - [x] Unzip Archive (65GB)
  - [x] Feature Extraction & Building (3 partitions trial complete)
  - [x] EDA Generation
- [/] **Tuesday-20-02-2018 (DDoS)**:
  - [/] Download PCAP (pcap.rar aria2 downloading)
- [ ] **Thursday-01-03-2018 (Infiltration)**:
  - [/] Download PCAP (aria2 downloading)
- [ ] **Other Folders (Queued)**:
  - [ ] Thursday-15-02-2018
  - [ ] Thursday-22-02-2018
  - [ ] Wednesday Folders

## Future Goals
- Scale extraction to high-volume partitions (e.g. `UCAP...part1.csv` is 18M+ rows).
- Implement XGBoost (Flow-based) and Transformer (Sequence-based) training scripts.
- Generate SHAP/Attention maps for explainability.


