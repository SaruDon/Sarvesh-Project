# Thursday-01-03-2018: Analysis Report (Infiltration)

## 📊 Overview
The Thursday-01-03-2018 dataset contains **Infiltration** attacks. Unlike high-volume DDoS, infiltration is often stealthy and involves an attacker gaining access to internal machines and then spreading through the network (lateral movement).

## 🔍 Key Discoveries
To accurately label this stealthy activity, we identified the following parameters:

1.  **Target Subnet Identified**: 
    - The attack logs pointed to local IPs, which we mapped to the **`172.31.64.*`** subnet in the AWS environment.
    - Multiple hosts in this range showed atypical connection patterns during the attack windows.
2.  **Clock Drift Calibration**: 
    - Consistent with previous days, a **4-hour clock offset** (UTC vs. local) was required. 
    - Attacks originally logged at 09:18 and 13:58 were correctly located at **13:18** and **17:58** UTC.

## 📉 Attack Patterns Identified
Infiltration shows up as unusual connection spikes on internal machines:

| Attack Phase | Time Window (UTC) | Targets |
| :--- | :--- | :--- |
| **Initial Breach** | 13:18 - 14:52 | `172.31.64.*` Subnet |
| **Lateral Movement**| 17:58 - 19:20 | `172.31.64.*` Subnet |

## 🧬 Feature Observations
- **Stealth Detection**: Because flow volume is lower than DDoS, our AI models (specifically the Transformer) will need to focus on **Protocol Entropy** and **TTL anomalies** to distinguish these from benign management traffic.

## 📁 Data Status
- **Extracted**: 100% (435 PCAP partitions)
- **Labeled**: Processing in progress (~12%).
- **Golden Set**: Queueing 5% for persistent validation.
