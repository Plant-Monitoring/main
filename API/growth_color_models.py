import torch
import torch.nn as nn
import torch.nn.functional as F

class GrowthPredictor(nn.Module):
    def __init__(self, n_inp):
        super().__init__()
        self.out = nn.Linear(n_inp, 1) 
        self.out.load_state_dict(torch.load("weights/lr_weights.pth", weights_only=True))
        self.X_std = torch.load("weights/X_std1.pth", weights_only=True)
        self.X_mean = torch.load("weights/X_mean1.pth", weights_only=True)


    def forward(self, input_layer):
        out = self.out(input_layer)

        return out

class ColorPredictor(nn.Module):
    def __init__(self, n_inp, n_hidd):
        super().__init__()
        self.hidd = nn.Linear(n_inp, n_hidd)
        self.out = nn.Linear(n_hidd, 5)
        self.hidd.load_state_dict(torch.load("weights/color_hidd_weights.pth", weights_only=True))
        self.out.load_state_dict(torch.load("weights/color_out_weights.pth", weights_only=True))
        self.X_std = torch.load("weights/X_std2.pth", weights_only=True)
        self.X_mean = torch.load("weights/X_mean2.pth", weights_only=True)

    def forward(self, input_layer):
        x = F.relu(self.hidd(input_layer))
        out = self.out(x)

        return out