import torch
import torch.nn as nn
import pytorch_lightning as L

class TransformerNIDS(L.LightningModule):
    def __init__(self, input_dim=9, d_model=64, nhead=4, num_layers=2, learning_rate=1e-4):
        super().__init__()
        self.save_hyperparameters()
        
        self.embedding = nn.Linear(input_dim, d_model)
        self.layer_norm = nn.LayerNorm(d_model) # Stabilization
        self.dropout = nn.Dropout(0.1)
        
        self.pos_encoder = nn.Parameter(torch.zeros(1, 200, d_model)) 
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, batch_first=True, dropout=0.1
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 1)
        )
        
        self.apply(self._init_weights) # Robust Initialization
        self.loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([5.0])) # Less aggressive bias
        
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
        
    def forward(self, x):
        # x: (B, 200, 9)
        x = self.embedding(x)
        x = self.layer_norm(x)
        x = self.dropout(x + self.pos_encoder)
        
        x = self.transformer(x)
        x = x.mean(dim=1)
        return self.classifier(x).squeeze(-1)
        
    def training_step(self, batch, batch_idx):
        x, y = batch
        x = x.view(-1, 200, 9)
        logits = self(x)
        loss = self.loss_fn(logits, y.float())
        self.log('train_loss', loss, prog_bar=True)
        return loss
        
    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.parameters(), lr=self.hparams.learning_rate, weight_decay=1e-2)
        return optimizer
