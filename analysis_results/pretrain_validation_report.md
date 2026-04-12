# Pre-Training Validation Report
**Generated:** 2026-04-08 10:01:28
**Pipeline:** XGBoost + Transformer Hybrid NIDS
**Dataset:** CIC-IDS-2018 (~51M flows)

## 📊 Executive Summary
| Metric | Value |
| :--- | :--- |
| Total Checks | 66 |
| Passed | 45 ✅ |
| Warnings | 17 ⚠️ |
| Failures | 4 ❌ |
| **Readiness Score** | **68.2%** |

> [!CAUTION]
> **Critical Blockers (4):**
> - Independent Attribute Tests: Test set has unseen categories
> - Label Verification: Missing attack types in training
> - Pipeline Strategy Check: File overlap detected: 266 files
> - Final Sanity Checklist: 3 critical blockers remain

> [!WARNING]
> **Warnings (17):**
> - Feature Validation: Missing values found
> - Feature Validation: High outlier rate in packet_rate: 23.0%
> - Independent Attribute Tests: 6 features have high skewness (>5)
> - Dataset Integrity Check: Duplicate row rate: 6.39%
> - Dataset Integrity Check: Class balance: Benign:Attack = inf:1
> - Label Verification: Severe class imbalance detected (>1:1000)
> - Processed Dataset Validation: 285/297 files contain NaN
> - XGBoost Model Checks: Early stopping not configured
> - Per-Dataset Testing: Friday-23-02-2018
> - Per-Dataset Testing: Thursday-01-03-2018
> - Per-Dataset Testing: Wednesday-14-02-2018
> - Per-Dataset Testing: Wednesday-28-02-2018
> - Data Coverage & Time Validation: Thursday-15-02-2018: Capture gap
> - Data Coverage & Time Validation: Thursday-22-02-2018: Capture gap
> - Edge Case Checks: Empty files: 117
> - Final Sanity Checklist: Overall Readiness Score: 71.4%
> - Final Sanity Checklist: 15 warnings to review

---

## 📊 Feature Validation

| Status | Check | Detail |
| :---: | :--- | :--- |
| ✅ | All expected flow columns present | Checked 297 files |
| ✅ | All feature columns are numeric | Types verified on sample |
| ⚠️ | Missing values found | frame.len_std:209082 |
| ⚠️ | High outlier rate in packet_rate: 23.0% | Consider clipping |
| ✅ | No redundant features (|r| > 0.95) | Correlation matrix checked |
| ✅ | No data leakage detected | Label/timestamp excluded from features |

---

## 🧪 Independent Attribute Tests

| Status | Check | Detail |
| :---: | :--- | :--- |
| ⚠️ | 6 features have high skewness (>5) | frame.len_count: 149.07; frame.len_sum: 184.52; frame.len_mean: 11.25; frame.len_std: 7.42; flow_duration_sec: 21.16 |
| ✅ | Feature-target correlation computed | frame.len_count: r=0.0020; frame.len_sum: r=0.0019; frame.len_mean: r=0.0038; frame.len_std: r=-0.0002; ip.ttl_mean: r=0.0084 |
| ✅ | Benign vs Attack distribution divergence computed | frame.len_count: KS=0.208 p=3.08e-190; frame.len_sum: KS=0.226 p=3.67e-224; frame.len_mean: KS=0.193 p=4.89e-163; frame.len_std: KS=0.197 p=2.24e-169 |
| ❌ | Test set has unseen categories | {'Botnet', 'Web-Attacks', 'DDoS-HOIC', 'Web-XSS', 'DDoS-LOIC-HTTP'} |

---

## 📦 Dataset Integrity Check

| Status | Check | Detail |
| :---: | :--- | :--- |
| ✅ | Training dataset: 2974 flow files found |  |
| ⚠️ | Duplicate row rate: 6.39% | 49,195 duplicates |
| ⚠️ | Class balance: Benign:Attack = inf:1 | Benign=1,632,298 Attack=0 |
| ✅ | All labels are valid | Labels found: {'Benign'} |
| ✅ | Test dataset: 390 flow files found |  |
| ✅ | Train/test schema match | 16 columns |
| ✅ | Test set contains 8 attack types | Botnet: 26,079, DDoS-LOIC-HTTP: 311,068, DDoS-HOIC: 28,949, Web-Attacks: 559, Infiltration: 154,969, Web-XSS: 623, SSH-BruteForce: 154,173, FTP-BruteForce: 47,985 |

---

## ⚖️ Normalization & Scaling

| Status | Check | Detail |
| :---: | :--- | :--- |
| ✅ | Flow scaler found | Features: 8 |
| ✅ | Scaler feature count matches: 8 |  |
| ✅ | Sequence scaler found | Features: 9 |
| ✅ | Sequence scaler expects 9 features (correct) |  |
| ✅ | Scaled feature distribution reasonable | Mean range: [-0.06, 0.08], Std range: [0.00, 1.17] |

---

## 🏷️ Label Verification

| Status | Check | Detail |
| :---: | :--- | :--- |
| ❌ | Missing attack types in training | Missing: {'Web-Attacks', 'Web-XSS', 'DDoS-HOIC', 'DDoS-LOIC-HTTP'} |
| ⚠️ | Severe class imbalance detected (>1:1000) | Botnet: 57,062 (1:667); DDoS-HOIC: 0 ❌; DDoS-LOIC-HTTP: 0 ❌; Infiltration: 553,860 (1:69) |
| ✅ | Binary encoding: Benign=0, non-Benign=1 | Verified in data_loader.py |
| ✅ | All attack types have entries in attack_logs.csv | 22 log entries |

---

## 🔍 Processed Dataset Validation

| Status | Check | Detail |
| :---: | :--- | :--- |
| ⚠️ | 285/297 files contain NaN | Consider imputation |
| ✅ | Flow files have expected 16 columns |  |
| ✅ | Sequence vectors are 1800-dim (200×9) | Checked 10 files |

---

## ⚙️ Pipeline Strategy Check

| Status | Check | Detail |
| :---: | :--- | :--- |
| ❌ | File overlap detected: 266 files | capEC2AMAZ-O4EL3NG-172.31.64.123_flows.parquet; capEC2AMAZ-O4EL3NG-172.31.67.45_flows.parquet; capDESKTOP-AN3U28N-172.31.66.115_flows.parquet; capEC2AMAZ-O4EL3NG-172.31.66.26_flows.parquet; capEC2AMAZ |
| ✅ | data_loader.py filters Golden_Test_Set | Exclusion logic verified |
| ✅ | Test set has 10 day subdirectories (stratified) | Friday-02-03-2018, Friday-16-02-2018, Friday-23-02-2018, Thursday-01-03-2018, Thursday-15-02-2018 |

---

## 🧠 XGBoost Model Checks

| Status | Check | Detail |
| :---: | :--- | :--- |
| ✅ | XGBoost model loads correctly | models\xgboost_flow_v1.json |
| ✅ | Objective: binary:logistic | Correct for binary classification |
| ✅ | DMatrix conversion and prediction successful | Shape: (100, 8), Preds range: [0.024, 0.029] |
| ⚠️ | Early stopping not configured | Recommend adding eval_set + early_stopping_rounds |

---

## 🧪 Per-Dataset Testing

| Status | Check | Detail |
| :---: | :--- | :--- |
| ✅ | Friday-02-03-2018 | Acc=99.79%, No attacks in test files |
| ✅ | Friday-16-02-2018 | Acc=99.67%, No attacks in test files |
| ⚠️ | Friday-23-02-2018 | Acc=74.09%, Attack Recall=0.18% (559 attacks) |
| ⚠️ | Thursday-01-03-2018 | Acc=86.11%, Attack Recall=0.08% (20,719 attacks) |
| ✅ | Thursday-15-02-2018 | Acc=99.71%, No attacks in test files |
| ✅ | Thursday-22-02-2018 | Acc=99.79%, No attacks in test files |
| ✅ | Tuesday-20-02-2018 | Acc=99.55%, No attacks in test files |
| ⚠️ | Wednesday-14-02-2018 | Acc=66.18%, Attack Recall=0.48% (57,975 attacks) |
| ✅ | Wednesday-21-02-2018 | Acc=99.78%, No attacks in test files |
| ⚠️ | Wednesday-28-02-2018 | Acc=93.62%, Attack Recall=0.04% (13,700 attacks) |

---

## 📈 Data Coverage & Time Validation

| Status | Check | Detail |
| :---: | :--- | :--- |
| ⚠️ | Thursday-15-02-2018: Capture gap | Slowloris attack window (10:59-11:40) before capture start (12:25) |
| ⚠️ | Thursday-22-02-2018: Capture gap | Web-BruteForce window (10:15-11:30) before capture start (13:25) |
| ✅ | Attack logs cover 10 dates | Dates: ['2018-02-14', '2018-02-15', '2018-02-16', '2018-02-20', '2018-02-21', '2018-02-22', '2018-02-23', '2018-02-28', '2018-03-01', '2018-03-02'] |
| ✅ | Friday-02-03-2018: Timestamps valid | 2018-03-02 12:46:48.369507074 → 2018-03-02 15:28:51.920624971 |
| ✅ | Friday-16-02-2018: Timestamps valid | 2018-02-16 12:38:01.777089119 → 2018-02-16 18:03:04.934221983 |
| ✅ | Thursday-01-03-2018: Timestamps valid | 2018-03-01 12:16:03.128762007 → 2018-03-01 15:30:08.320852041 |
| ✅ | Thursday-15-02-2018: Timestamps valid | 2018-02-15 12:24:40.849759102 → 2018-02-15 21:54:45.860704899 |
| ✅ | Thursday-22-02-2018: Timestamps valid | 2018-02-22 12:22:35.976166964 → 2018-02-22 21:30:07.993417025 |
| ✅ | Tuesday-20-02-2018: Timestamps valid | 2018-02-20 12:29:19.484513044 → 2018-02-20 18:57:15.136882067 |
| ✅ | Wednesday-14-02-2018: Timestamps valid | 2018-02-14 12:30:11.883956909 → 2018-02-14 17:38:30.390798092 |
| ✅ | Wednesday-21-02-2018: Timestamps valid | 2018-02-21 12:28:55.839029074 → 2018-02-21 21:30:07.393707991 |
| ✅ | Wednesday-28-02-2018: Timestamps valid | 2018-02-28 12:26:54.103290081 → 2018-02-28 15:23:21.259937048 |

---

## 🚨 Edge Case Checks

| Status | Check | Detail |
| :---: | :--- | :--- |
| ⚠️ | Empty files: 117 | of 2974 total |
| ✅ | Missing labels: 0 |  |
| ✅ | Single-class files: 2330 | Normal for per-host files |
| ✅ | Extreme imbalance files (>100:1): 0 |  |
| ✅ | Unexpected label values: 0 |  |

---

## ✅ Final Sanity Checklist

| Status | Check | Detail |
| :---: | :--- | :--- |
| ⚠️ | Overall Readiness Score: 71.4% | 45/63 checks passed |
| ❌ | 3 critical blockers remain | Independent Attribute Tests: Test set has unseen categories; Label Verification: Missing attack types in training; Pipeline Strategy Check: File overlap detected: 266 files |
| ⚠️ | 15 warnings to review | Feature Validation: Missing values found; Feature Validation: High outlier rate in packet_rate: 23.0%; Independent Attribute Tests: 6 features have high skewness (>5) |
