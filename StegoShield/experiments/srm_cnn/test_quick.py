"""Quick test for SRM-CNN"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing SRM-CNN...")

from srm_filters import SRMFilters, SRMLayer
import torch

filters = SRMFilters.get_srm_filters()
print(f"SRM filters: {len(filters)}")

srm = SRMLayer(in_channels=3)
x = torch.randn(1, 3, 256, 256)
y = srm(x)
print(f"SRM output: {y.shape}")

from model import get_model
model = get_model('srmnet')
y = model(x)
print(f"Model output: {y.shape}")

print("All tests passed!")
