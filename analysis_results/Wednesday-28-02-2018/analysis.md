# Analysis Results: Wednesday-28-02-2018 (Infiltration)

This report summarizes the exploratory data analysis and statistical findings for the Infiltration attack dataset processed for Feb 28, 2018.

## 📊 Traffic Visualization

### 1. Traffic Timeline
The plot below shows the flow volume over time, highlighting the specific Infiltration windows.

![Traffic Volume Over Time](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Wednesday-28-02-2018/traffic_timeline.png)

### 2. Feature Importance
Using a Random Forest classifier, we identified the top features that distinguish Infiltration traffic from Benign network behavior.

![Feature Importance](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Wednesday-28-02-2018/feature_importance.png)

### 3. PCA Traffic Clustering
The 2D projection shows how the attack flows cluster in relation to normal traffic.

![PCA Clusters](file:///c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/analysis_results/Wednesday-28-02-2018/pca_visualization.png)

## 📈 Statistical Comparison

| Metric | Benign (Avg) | Infiltration (Avg) |
| :--- | :--- | :--- |
| **Packet Rate** | 380.89 pkts/s | **543.97 pkts/s** |
| **Flow Duration** | 93.82 sec | **45.35 sec** |
| **Frame Length (Mean)** | 195.35 bytes | 199.14 bytes |
| **IP TTL** | 120.50 | 122.61 |

## 🔍 Key Findings

> [!IMPORTANT]
> **Attack Signature**: Infiltration on this day is characterized by significantly higher transmission speeds (**+42% packet rate**) and shorter session durations compared to baseline benign traffic.

- **Port Entropy**: Attacks seem to target a variety of ports, similar to normal traffic, making them harder to detect via port-scans alone.
- **Data Volume**: The Infiltration flows represent a small percentage of total traffic (~2.3%), which is consistent with stealthy lateral movement.

## 🛠️ Recommendations for Training
1.  **XGBoost**: Focus on `packet_rate` and `flow_duration_sec` as high-weight features.
2.  **Normalization**: Ensure `frame.len_sum` is log-normalized during preprocessing.
