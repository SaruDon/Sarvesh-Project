import torch
import torch.nn as nn
import pytorch_lightning as L

class TransformerNIDS(L.LightningModule):
    def __init__(self, input_dim=9, d_model=64, nhead=4, num_layers=2, learning_rate=1e-3):
        super().__init__()
        self.save_hyperparameters()
        
        self.embedding = nn.Linear(input_dim, d_model)
        self.pos_encoder = nn.Parameter(torch.zeros(1, 200, d_model)) # Fixed window size 200
        
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        self.loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([10.0])) # Handle sequence imbalance
        
    def forward(self, x):
        # x: (B, 200, 9)
        x = self.embedding(x) + self.pos_encoder
        x = self.transformer(x)
        # Use simple global average pooling across time dimension
        x = x.mean(dim=1)
        return self.classifier(x).squeeze(-1)
        
    def training_step(self, batch, batch_idx):
        x, y = batch
        # Reshape flattened features back to (B, 200, 9)
        x = x.view(-1, 200, 9)
        logits = self(x)
        loss = self.loss_fn(logits, y.float())
        self.log('train_loss', loss)
        return loss
        
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.learning_rate)
