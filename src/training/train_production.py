
import os
import glob
from datetime import datetime
import torch
import pytorch_lightning as L
from pytorch_lightning.callbacks import ModelCheckpoint
from src.models.seq_classifier import TransformerNIDS
from src.data.data_loader import ShardedNIDSDataset
from torch.utils.data import DataLoader

# Optimization for RTX A400 Tensor Cores
torch.set_float32_matmul_precision('high')

# Configuration
PROCESSED_DIR = "processed_dataset"
SCALER_PATH = "models/seq_scaler.joblib"
CHECKPOINT_DIR = "models/checkpoints_production"
BATCH_SIZE = 1024  # Increased from 512 -> better VRAM utilization
EPOCHS = 1         # 1 epoch is sufficient for 17M samples (audit confirmed)
# Skip days with zero attack content (wastes GPU time on pure benign data)
EXCLUDE_DAYS = ["Thursday-15-02-2018"]

def find_latest_checkpoint(checkpoint_dir):
    if not os.path.exists(checkpoint_dir):
        return None
    files = glob.glob(os.path.join(checkpoint_dir, "*.ckpt"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def train_production():
    print("="*70)
    print("STAGE 2: TRANSFORMER PRODUCTION TRAINING (17M SAMPLES)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Configuration: Stabilized Architecture [LayerNorm + AdamW]")
    print("="*70)
    
    # 1. Dataset & Loader
    dataset = ShardedNIDSDataset(PROCESSED_DIR, mode='sequence', scaler_path=SCALER_PATH,
                                  exclude_days=EXCLUDE_DAYS)
    train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=4, persistent_workers=True, pin_memory=True)
    
    # 2. Model Initialization (With Fixed Architecture)
    model = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
    
    # 3. Trainer Configuration (Full Run)
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    checkpoint_callback = ModelCheckpoint(
        dirpath=CHECKPOINT_DIR,
        filename="transformer-v4-prod-{epoch:02d}-{train_loss:.2f}",
        save_top_k=3,
        monitor="train_loss",
        save_last=True,
        every_n_train_steps=10000 # Save frequently for 17-hour safety
    )
    
    latest_ckpt = find_latest_checkpoint(CHECKPOINT_DIR)
    if latest_ckpt:
        print(f"RESUMING from checkpoint: {latest_ckpt}")
    else:
        print("Starting fresh training run with pos_weight=18 (class-balanced)")
    
    trainer = L.Trainer(
        max_epochs=EPOCHS,
        accelerator="gpu",
        devices=1,
        callbacks=[checkpoint_callback],
        precision="16-mixed",
        log_every_n_steps=50,    # More frequent logging
        enable_progress_bar=True,
        gradient_clip_val=1.0,   # Prevent loss spikes
    )
    
    # 4. Train
    print(f"Starting 17-hour production run...")
    trainer.fit(model, train_loader, ckpt_path=latest_ckpt)
    
    # 5. Save final weights
    final_path = "models/transformer_seq_v4_production_full.pth"
    torch.save(model.state_dict(), final_path)
    print(f"Production weights saved to {final_path}")
    print("="*70)

if __name__ == "__main__":
    train_production()
