# Dataset Completeness & Architecture Audit Report

**Date:** 2026-04-03
**Status:** ❌ ACTION REQUIRED BEFORE TRAINING

Before model training, we performed a global audit of the **57 Million Flow** dataset. While the data volume is massive and attack labels are diverse, we discovered **critical schema inconsistencies** that must be resolved to prevent model failure.

## 📊 Dataset Stats (Verified)

| Day | Attacks Captured | Flows Found | Sequences Found | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Friday-02-03** | Botnet | 7.4M | 2.2M | ✅ Ready |
| **Friday-16-02** | DDoS-HOIC/LOIC | 5.1M | 1.7M | ✅ Ready |
| **Thursday-01-03** | Infiltration | 7.5M | 2.4M | ✅ Ready |
| **Wednesday-28-02** | Infiltration | 7.5M | 2.5M | ✅ Ready |
| **Tuesday-20-02** | DDoS-LOIC-HTTP | 6.4M | **0** | ❌ ERROR (Schema Mismatch) |
| **Wednesday-14-02** | SSH/FTP Brute Force | 5.0M | 1.7M | ✅ Ready |

## ❌ Critical Issue: Schema Mismatch (Legacy Data)

Several files in `Tuesday-20-02-2018` are missing modern features added in later script versions:
- **Missing Features:** `flow_duration_sec`, `packet_rate`, `tcp.window_size_value_mean`.
- **Impact:** Attempting to train the XGBoost model on these will result in either a crash or extremely poor performance due to missing columns.
- **Cause:** These files were generated before the `dataset_builder.py` was finalized with the full feature set.

## 🧠 Architecture Audit: Capability Review

### 1. Long-Term Attack Detection (Transformers/LSTM)
- **Verdict**: **FULLY CAPABLE.**
- **Reasoning**: We have verified **over 12 million** sliding window sequences (200 packets each). These sequences contain the high-dimensional temporal patterns required for the Transformer model to "remember" long-term behavior of infiltration scripts.

### 2. Zero-Day Detection (Future State)
- **Verdict**: **REQUIRES ADD-ON TRANSFORMATION.**
- **Reasoning**: To detect attacks we've never seen before, we should implement a **Denoising Autoencoder** layer during the training phase. This model would learn the "Benign" baseline and flag any major reconstruction error as a potential Zero-Day threat.

## 🚀 Recommendation & Next Steps

> [!CAUTION]
> **DO NOT start model training yet.**

**Proposed Fix:**
1.  **Rebuild Tuesday-20**: Run `python src/dataset_builder.py --day Tuesday-20-02-2018 --force`. This will regenerate the Parquet files using the latest schema.
2.  **Verify Gaps**: Ensure Sequences are generated for all 10 days (currently Tuesday-20 sequences are missing in the stats).

**Shall I proceed with the Targeted Rebuild of the Tuesday dataset?**
