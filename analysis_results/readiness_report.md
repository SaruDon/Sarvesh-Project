# Dataset Certification Readiness Report

**Total Files Certified:** 7391
**Files Normalized:** 0
**Errors Found:** 0

## 🎯 Final Attack Distribution (Flows)
| Attack Type | Flow Count |
| :--- | :--- |
| Benign | 48,612,316 |
| Botnet | 88,414 |
| DDoS-HOIC | 28,949 |
| DDoS-LOIC-HTTP | 311,068 |
| FTP-BruteForce | 237,039 |
| Infiltration | 781,137 |
| SSH-BruteForce | 1,006,885 |
| Web-Attacks | 1,154 |
| Web-XSS | 623 |

## ✅ Certification Logic
- Column `label_<lambda>` standardized to `label`.
- Sequence vectors verified at 1,800 features (200 packets x 9 properties).
- Orphans removed from project root.
