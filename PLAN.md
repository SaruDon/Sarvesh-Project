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

### 📊 Dataset Processing Checklist
- [x] **Friday-02-03-2018 (Botnet)**: 
  - [x] Download PCAP
  - [x] Unzip Archive
  - [/] Feature Extraction (In progress - 3 partitions trial complete)
  - [/] EDA & Dataset Building
- [/] **Friday-16-02-2018 (DDoS)**:
  - [x] Download Logs
  - [/] Download PCAP (aria2 downloading)
- [/] **Tuesday-20-02-2018 (DDoS)**:
  - [/] Download PCAP (pcap.rar aria2 downloading)
- [ ] **Friday-23-02-2018 (Brute Force)**:
  - [x] Download Logs
  - [ ] Download PCAP (Queued)
- [ ] **Thursday Folders (Infiltration/Web)**:
  - [x] Download Logs
  - [ ] Download PCAP (Queued)
- [ ] **Wednesday Folders (DoS/SQL)**:
  - [ ] Download Logs (Queued)
  - [ ] Download PCAP (Queued)

## Future Goals
- Implement XGBoost (Flow-based) and Transformer (Sequence-based) layers.
- Generate SHAP/Attention maps for explainability.
- Scale extraction to all 380+ Botnet partitions.


