# Phase-1: Data Understanding + Processing

## Immediate Steps
1. **Finish PCAP Download**: Let the `run_nids_pipeline.sh` script finish the download on /mnt.
2. **Extraction**: Script will automatically extract to the Windows drive (900GB free).
3. **EDA**: Run `eda_initial.py` to generate packet distribution and rate plots.

## Middle Steps
1. **Flow Building**: Use `dataset_builder.py` to create labeled Parquet files.
2. **Architecture**: Implement the XGBoost vs Transformer comparison.

## Final Goal
- Demonstrate a Hybrid model with SHAP/Attention explainability.
