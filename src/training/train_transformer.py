import torch
import pytorch_lightning as L
from pytorch_lightning.callbacks import ModelCheckpoint
from src.models.seq_classifier import TransformerNIDS
from src.data.data_loader import NIDSDataset
from torch.utils.data import DataLoader

# Optimization for RTX A400 Tensor Cores
torch.set_float32_matmul_precision('medium')

# Configuration
PROCESSED_DIR = "processed_dataset"
SCALER_PATH = "models/seq_scaler.joblib"
BATCH_SIZE = 128
EPOCHS = 3

def train_stage2():
    print("Starting Stage 2 Training: Transformer (Sequence Context)...")
    
    # 1. Dataset & Loader
    # Note: Mapping 17M sequences might take a minute
    dataset = NIDSDataset(PROCESSED_DIR, mode='sequence', scaler_path=SCALER_PATH)
    
    # Take a manageable subset (e.g., 500k sequences) for this research iteration
    # Shuffling 17M flows in RAM is impossible, we'll use a subset of files or a Subset sampler
    indices = torch.randperm(len(dataset))[:500000]
    subset = torch.utils.data.Subset(dataset, indices)
    
    train_loader = DataLoader(subset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, persistent_workers=True)
    
    # 2. Model Initialization
    model = TransformerNIDS(input_dim=9, d_model=64, nhead=4, num_layers=2)
    
    # 3. Trainer
    checkpoint_callback = ModelCheckpoint(
        dirpath="models/checkpoints",
        filename="transformer-v1-{epoch:02d}-{train_loss:.2f}",
        save_top_k=1,
        monitor="train_loss"
    )
    
    trainer = L.Trainer(
        max_epochs=EPOCHS,
        accelerator="gpu",
        devices=1,
        callbacks=[checkpoint_callback],
        precision="16-mixed" # Speed up on RTX A400
    )
    
    # 4. Train
    print(f"Training on {len(subset)} sequences...")
    trainer.fit(model, train_loader)
    
    # Save final model
    torch.save(model.state_dict(), "models/transformer_seq_v1.pth")
    print("Transformer model saved.")

if __name__ == "__main__":
    train_stage2()
