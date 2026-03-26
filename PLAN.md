# Hybrid NIDS Project: Implementation Plan & Progress

## 🎯 Project Vision & Goals

### The Problem Being Solved
We are tackling the complexity of **Network Intrusion Detection (NIDS)** at scale. Raw network traffic is massive (40GB–60GB per day) and difficult to analyze in its binary (`.pcap`) form. This project solves this by:
*   **Orchestrating Big Data**: Using tools like `aria2c` for high-speed downloads and `tshark` for optimized feature extraction.
*   **Bridging the "Label Gap"**: Using `attack_logs.csv` to accurately map timestamps and IP addresses to raw traffic, transforming "unlabeled wire data" into "machine learning features."

### End Goal
The ultimate objective is to create a **Hybrid NIDS** that uses the CIC-IDS-2018 dataset to train two distinct types of AI models:
1.  **Flow-Based (XGBoost)**: For detecting attacks based on aggregated traffic statistics (speed, volume, protocol).
2.  **Sequence-Based (Transformers/LSTM)**: For capturing long-term, time-series behaviors of attackers through session-based sliding windows.

### Final Deliverables
*   A fully automated pipeline (from S3 download to Parquet generation).
*   High-accuracy ML models for intrusion detection.
*   **Explainability (XAI)**: Using SHAP or Attention maps to explain exactly why a model flagged a certain packet as an attack.

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

## Status: Day 4 Breakthrough (2026-03-26)

### ✅ Accomplishments
1. **DDoS Labeling Milestone (Friday-16)**:
   - **Diagnosis**: Resolved 4h clock offset and victim IP mapping (`172.31.69.25`).
   - **Audit**: Verified 100% labeled Parquet build (5.1M flows).
   - **Walkthrough**: Created `walkthrough_ddos.md` with PCA and Traffic analysis.
2. **Infiltration Labeling Milestone (Thursday-01)**:
   - **Diagnosis**: Mapped stealthy attacks to `172.31.64.*` subnet with 4h UTC offset.
   - **Verification**: Captured **1,324 Infiltration flows** across 435 partitions.
   - **Walkthrough**: Created `walkthrough_infiltration.md` confirming signature separation.
3. **Massive Disk Recovery**:
   - Recovered **194.7 GB** of disk space by deleting raw archives (ZIPs), PCAPs, and CSVs for Friday-02 and Friday-16.
4. **Tooling Resilience**:
   - Updated `dataset_builder.py` with **multiprocessing** and **encoding fallback** (UTF-8-SIG/UTF-16) to handle PowerShell artifacts.

### 📊 Dataset Processing Checklist
- [x] **Friday-02-03-2018 (Botnet)**: 
  - [x] Unzip & Feature Extraction
  - [x] EDA & Dataset Building
  - [x] **CLEANUP** (Raw files deleted)
- [x] **Friday-16-02-2018 (DDoS)**:
  - [x] Unzip & Feature Extraction (100% Label Accuracy)
  - [x] EDA & Walkthrough Report
  - [x] **CLEANUP** (Raw files deleted)
- [x] **Thursday-01-03-2018 (Infiltration)**:
  - [x] Full Feature Extraction (435 files)
  - [x] Labeled Build & Analysis Report
  - [x] **WALKTHROUGH** (Visual proof generated)
- [/] **Friday-23-02-2018 (Brute Force)**:
  - [/] Unzip Archive (In Progress: 59GB)
  - [ ] Trial Extraction & Diagnosis
- [/] **Tuesday-20-02-2018 (DDoS)**:
  - [/] Download PCAP (aria2 downloading)
- [ ] **Other Folders (Queued)**:
  - [ ] Thursday-15-02-2018
  - [ ] Thursday-22-02-2018
  - [ ] Wednesday-14-02-2018 (Missing Source)

## Status: Verification (2026-03-26)

### 📊 Extraction Verification Summary

| Dataset Day | Source PCAPs (cap-prefix) | Processed Pairs (Flows + Sequences) | Status |
| :--- | :--- | :--- | :--- |
| **Friday 02-03-2018** (Botnet) | 434 files | 434 pairs (868 total) | **✅ Complete** |
| **Friday 23-02-2018** (Brute Force) | 450 files | 3 pairs (6 total) | **⚠️ Partial** |
| **Friday 16-02-2018** (DDoS) | 450 files | 1 pair (2 total) | **⚠️ Partial** |

**Details:**
- For **Friday 02-03-2018**, every `cap...` file in the source `pcap` folder has a corresponding flow and sequence parquet file in the processed directory.
- For **Friday 23-02-2018**, only 3 files (`cap...64`, `cap...66`, `cap...67`) have been processed.
- For **Friday 16-02-2018**, only the `UCAP172.31.69.25-part2` file was processed.

## 🧠 Advanced EDA Strategy (Next Steps)

To gain deeper security insights, we will implement `eda_labeled.py` to analyze the **processed Parquet files**:
1.  **Label-Based Feature Distribution**: Boxplots/Violin plots for features (`packet_rate`, `payload_ratio`) comparing Benign vs. specific Attack types.
2.  **Feature Correlation Heatmap**: Identify redundant network metrics and those strongest tied to labels.
3.  **Time-Series Attack Spikes**: Plot packet rates over time with color-coded attack labels.
4.  **Dimensionality Reduction (PCA/t-SNE)**: Visualize if attacks form distinct clusters from benign traffic.
5.  **IAT Analysis**: Analyze time gaps between packets to identify robotic attack patterns.

## 🚀 Training & Data Retention Strategy

To avoid **Catastrophic Forgetting** and maintain a balanced model while managing disk space:

*   **Golden Test Set**: Save a small portion (e.g., 5%) of *every* day's processed data in a separate folder. **Never delete this**. It ensures we can always verify the model still remembers old attack types.
*   **Shuffle Training**: Keep the highly-compressed Parquet files for training. Train on batches containing a mix of different days to maintain a balanced "baseline."
*   **Incremental Learning**: Utilize XGBoost's `process_type: 'update'` and Transformer checkpoint loading for multi-day training.

## Future Goals
- Scale extraction to high-volume partitions (e.g. `UCAP...part1.csv` is 18M+ rows).
- Implement XGBoost (Flow-based) and Transformer (Sequence-based) training scripts.
- Generate SHAP/Attention maps for explainability.


d   |stat|avg speed  |path/URI
======+====+===========+=======================================================
7742a7|OK  |    11MiB/s|C:/Users/Student/cicids2018/Thursday-01-03-2018-pcap.zip
downloaded now process it