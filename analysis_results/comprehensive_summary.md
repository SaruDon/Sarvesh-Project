# Comprehensive Dataset Analysis Results

This report provides a summary of all processed datasets in the CIC-IDS-2018 project. Each day has been analyzed for label distribution, feature statistics, and cluster separation (PCA).

## 📊 Label Distribution Summary

| Dataset Day | Benign Count | Attack Type | Attack Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Friday-02-03-2018** | 7,352,685 | Botnet | 88,414 | ✅ Complete |
| **Friday-16-02-2018** | 5,067,902 | DDoS-HOIC/LOIC | 57,156 | ✅ Complete |
| **Thursday-01-03-2018** | 6,963,202 | Infiltration | 607,573 | ✅ Complete |
| **Wednesday-14-02-2018** | 3,763,818 | Brute Force (FTP/SSH) | 1,243,924 | ✅ Complete |
| **Thursday-22-02-2018** | 6,412,915 | Web-XSS | 623 | ✅ Partial (Morning missing) |
| **Wednesday-21-02-2018** | 517,273 | DDoS-HOIC | 233 | ✅ Partial |
| **Thursday-15-02-2018** | 4,688,402 | - | 0 | ℹ️ Benign-Only |
| **Friday-23-02-2018** | 3,491 | Web-Attacks | 1,154 | ⚠️ Incomplete (To be re-run) |
| **Tuesday-20-02-2018** | - | DDoS | - | ❌ MISSING (Queued) |

## 🔍 Detailed Visual Reports (EDA)

Click below to view the detailed analysis for each day (plots include Label Distribution, Feature Boxplots, Correlation Heatmaps, and PCA Clusters):

- [Friday-02-03-2018 (Botnet)](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Friday-02-03-2018/)
- [Friday-16-02-2018 (DDoS)](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Friday-16-02-2018/)
- [Thursday-01-03-2018 (Infiltration)](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Thursday-01-03-2018/)
- [Thursday-22-02-2018 (Web Attacks)](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Thursday-22-02-2018/)
- [Wednesday-14-02-2018 (Brute Force)](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Wednesday-14-02-2018/)
- [Wednesday-21-02-2018 (DDoS)](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Wednesday-21-02-2018/)

---
**Next Step:** Proceeding to Disk Cleanup (recovering 90GB) and processing **Tuesday-20-02-2018** to complete the DDoS dataset.
