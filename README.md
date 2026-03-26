# 🛡️ Sarvesh NIDS Project: CIC-IDS-2018 Analyzer

Welcome to the Network Intrusion Detection System (NIDS) project. This repository is designed to download, extract, preprocess, and analyze the **CIC-IDS-2018** dataset, producing high-quality labeled data for machine learning models (XGBoost and Transformers).

---

## 📂 Project Structure Explained

### 📁 `src/` (The Engine ⚙️)
Contains the core Python logic for processing and analysis.
*   **`dataset_builder.py`**: The labeling engine. Turns raw CSVs into labeled Parquet files.
*   **`eda_labeled.py`**: The visualizer. Generates all plots and statistical reports.
*   **`diagnose_ids.py`**: The auditor. Identifies victim IPs and clock drifts.

### 📁 `scripts/` (Automation & Helpers 🛠️)
Consolidate extraction, downloading, and auxiliary utilities.
- **`extraction/`**: PowerShell scripts for `tshark` processing.
- **`run_nids_pipeline.ps1`**: The master wrapper script.
- **`legacy/`**: Earlier versions of EDA and diagnostic tools.

### 📁 `data/` (Knowledge & Logs 📄)
- **`attack_logs.csv`**: The "Cheat Sheet" containing dates, times, and target IPs for every attack.

### 📁 `extracted_features/` (Raw Features 📊)
This folder holds the CSV files created by `extract_pcap.ps1`. 
*   These are **unlabeled** raw values like IP addresses, ports, protocol IDs, and packet lengths.
*   They serve as the input for our Python preprocessing scripts.

### 📁 `processed_dataset/` (Machine Learning Ready 🚀)
The "Clean" data. Contains Parquet files ready for training. It splits data into two types:
*   **Flows (`_flows.parquet`)**: Aggregated traffic statistics. Perfect for models like **XGBoost**.
*   **Sequences (`_sequences.parquet`)**: Sliding-window time-series data. Specifically designed for **Transformer** or **LSTM** models.

### 📁 `analysis_results/` (Exploratory Data Analysis 🔍)
Visual evidence! This folder contains PNG plots generated from the data.

---

## 🔄 The Data Transformation Journey (States)

1.  **Stage 1: Raw Download (`.zip` / `.rar`)**
    *   *What we have*: Compressed archive files (e.g., `Friday-23-02-2018-pcap.zip`).
    *   *Scale*: Massive (40GB - 60GB per day).
2.  **Stage 2: Unzipped Data (`.pcap`)**
    *   *What we have*: Binary packet capture files. These are "raw wire traffic."
    *   *Location*: `C:\Users\Student\cicids2018\[Date]\pcap\`
3.  **Stage 3: Feature Extraction (`.csv`)**
    *   *What we have*: Structured text data. Every row is a packet, but there are **no labels** (we don't know if it's an attack yet).
    *   *Location*: `extracted_features/[Date]/`
4.  **Stage 4: Labeled Preprocessing (`.parquet`)**
    *   *What we have*: Binary, compressed data with **Attack Labels** added. Optimized for Python and AI training.
    *   *Location*: `processed_dataset/[Date]/`
5.  **Stage 5: EDA & Insights (`.png`)**
    *   *What we have*: Visual reports showing attack spikes, protocol usage, and traffic patterns.
    *   *Location*: `analysis_results/[Date]/`

---

## 🗺️ Data Mapping (Which file comes from where?)

The project maintains a 1-to-1 folder structure to help you track your data:

| Dataset Day | Raw Zip Source | Extracted CSV Folder | Processed Parquet Folder |
| :--- | :--- | :--- | :--- |
| **Botnet Day** | `Friday-02-03-2018-pcap.zip` | `extracted_features/Friday-02...` | `processed_dataset/Friday-02...` |
| **DDoS Day 1** | `Friday-16-02-2018-pcap.zip` | `extracted_features/Friday-16...` | `processed_dataset/Friday-16...` |
| **Brute Force** | `Friday-23-02-2018-pcap.zip` | `extracted_features/Friday-23...` | `processed_dataset/Friday-23...` |
| ... and so on | ... | ... | ... |

*   **Example**: If you want the labeled data for the **Brute Force** attack on **Feb 23**, look for `processed_dataset/Friday-23-02-2018/` and you will see the `.parquet` files generated specifically from that day's traffic.

---

## 🛠️ Key Scripts & Usage

### 🐍 `dataset_builder.py`
**What it does**: Takes the raw CSVs from `extracted_features`, looks at `attack_logs.csv` to know when attacks happened, and creates the **labeled** Parquet files in `processed_dataset`.

### 🐍 `eda_initial.py`
**What it does**: Automates the data science! It reads the extracted features and creates every plot you find in `analysis_results`.

### 📄 `attack_logs.csv`
**What it does**: This is our "Cheat Sheet." It lists the dates, times, and target IPs for every attack in the dataset. Without this, we wouldn't know which traffic is "Benign" (normal) and which is an "Attack."

---

## 📍 Dataset Location
Note that the raw, heavy dataset files (GBs of PCAPs) are stored outside this repository at `C:\Users\Student\cicids2018` to keep the codebase lightweight and clean.
