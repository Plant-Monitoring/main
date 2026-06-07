import torch
import torch.nn as nn
import torch.nn.functional as F

class GrowthPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.out = nn.Linear(14, 1)

    def forward(self, x):
        return self.out(x)

class ColorPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(14, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 5)
        )   

    def forward(self, x):
        return self.net(x)  
