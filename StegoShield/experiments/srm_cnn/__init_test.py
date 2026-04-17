"""快速测试脚本 - 验证 SRM-CNN 代码是否正确"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("SRM-CNN Quick Test")
print("=" * 60)

# Test 1: SRM Filters
print("\n[1] Testing SRM Filters...")
try:
    from srm_filters import SRMFilters, SRMLayer
    import torch

    filters = SRMFilters.get_srm_filters()
    print(f"    ✓ Found {len(filters)} SRM filters")

    srm = SRMLayer(in_channels=3)
    x = torch.randn(1, 3, 256, 256)
    y = srm(x)
    print(f"    ✓ SRM output shape: {y.shape}")
    print(f"    ✓ SRM output channels: {y.shape[1]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 2: Models
print("\n[2] Testing Models...")
try:
    from model import get_model

    models = ['srmnet', 'srmnet_v2', 'yenet']
    for name in models:
        model = get_model(name)
        x = torch.randn(1, 3, 256, 256)
        y = model(x)
        params = sum(p.numel() for p in model.parameters())
        print(f"    ✓ {name}: output={y.shape}, params={params:,}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 3: Dataset
print("\n[3] Testing Dataset...")
try:
    from dataset import SyntheticStegoDataset, TransformFactory
    import tempfile
    from PIL import Image
    import numpy as np

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(5):
            img = Image.fromarray(
                np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
            )
            img.save(os.path.join(tmpdir, f'test_{i}.png'))

        transform = TransformFactory.get_train_transform(256)
        dataset = SyntheticStegoDataset(
            root_dir=tmpdir,
            transform=transform,
            num_samples=10,
            img_size=256
        )
        print(f"    ✓ Dataset size: {len(dataset)}")

        img, label = dataset[0]
        print(f"    ✓ Sample shape: {img.shape}, label: {label}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 4: GPU Check
print("\n[4] GPU Check...")
try:
    import torch
    if torch.cuda.is_available():
        print(f"    ✓ CUDA available")
        print(f"    ✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"    ✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        print(f"    ⚠ CUDA not available, will use CPU")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Summary
print("\n" + "=" * 60)
print("Quick Test Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Download dataset: bash srm_cnn/dataset/download_bossbase.sh")
print("2. Train model: python srm_cnn/train.py --data_dir ./srm_cnn/dataset")
print("3. Test model: python srm_cnn/test.py --model_path ./checkpoints/best_model.pth")
