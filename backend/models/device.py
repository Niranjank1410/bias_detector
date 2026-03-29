# backend/models/device.py
"""
Detects whether a CUDA GPU is available and returns the appropriate
device string. All models import this so they all run on the same device.
"""

import torch

def get_device() -> str:
    """Returns 'cuda' if a GPU is available, otherwise 'cpu'."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Device] Using: {device.upper()}")
    return device