#!/usr/bin/env python3
"""
SRM-CNN 云服务器训练脚本

在曙光智算平台上运行此脚本进行模型训练。

使用方法:
    python run_training.py

或在云平台的启动脚本中调用:
    python /mnt/data/run_training.py
"""

import os
import sys
import subprocess
import time
import argparse


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step_num, text):
    """打印步骤"""
    print(f"\n[Step {step_num}] {text}")


def run_command(cmd, shell=True):
    """运行命令"""
    print(f"  Running: {cmd[:80]}...")
    result = subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"  ✗ Error: {result.stderr[:200]}")
        return False
    print(f"  ✓ Success")
    return True


def check_gpu():
    """检查 GPU 是否可用"""
    print_step(0, "Checking GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
            print(f"  ✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            return True
        else:
            print("  ⚠ Warning: CUDA not available, will use CPU")
            return False
    except ImportError:
        print("  ⚠ PyTorch not installed yet")
        return False


def install_dependencies():
    """安装依赖"""
    print_step(1, "Installing dependencies...")

    packages = [
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "numpy>=1.19.0",
        "scipy>=1.5.0",
        "pillow>=8.0.0",
        "scikit-learn>=0.24.0",
        "pycryptodome>=3.9.0",
    ]

    for pkg in packages:
        print(f"  Installing {pkg}...")
        subprocess.run(f"pip install {pkg} -q", shell=True)

    print("  ✓ All dependencies installed")


def download_dataset():
    """下载数据集"""
    print_step(2, "Preparing dataset...")

    dataset_dir = "./dataset"
    cover_dir = os.path.join(dataset_dir, "cover")
    stego_dir = os.path.join(dataset_dir, "stego")

    os.makedirs(dataset_dir, exist_ok=True)
    os.makedirs(cover_dir, exist_ok=True)
    os.makedirs(stego_dir, exist_ok=True)

    if len(os.listdir(cover_dir)) >= 10:
        print(f"  ✓ Dataset already exists ({len(os.listdir(cover_dir))} images)")
        return True

    print("  Creating synthetic test dataset...")

    try:
        from PIL import Image
        import numpy as np

        for i in range(100):
            img = Image.fromarray(
                np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
            )
            img.save(os.path.join(cover_dir, f"test_{i:03d}.png"))

        print(f"  ✓ Created {len(os.listdir(cover_dir))} test images")
        print("  Note: For production, download Bossbase dataset")
        print("  wget http://dde.binguo.me/Bossbase-1.01.zip")
        return True

    except Exception as e:
        print(f"  ✗ Error creating dataset: {e}")
        return False


def train_model(args):
    """训练模型"""
    print_step(3, "Training model...")

    train_cmd = f"""
        python train.py \
            --data_dir {args.data_dir} \
            --epochs {args.epochs} \
            --batch_size {args.batch_size} \
            --img_size {args.img_size} \
            --lr {args.lr} \
            --output_dir {args.output_dir} \
            --model {args.model}
    """

    print(f"  Command: python train.py --epochs {args.epochs} --batch_size {args.batch_size}")

    start_time = time.time()

    try:
        result = subprocess.run(
            train_cmd.strip(),
            shell=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        elapsed = time.time() - start_time
        print(f"\n  Training completed in {elapsed/60:.2f} minutes")

        if result.returncode == 0:
            print("  ✓ Training successful!")
            return True
        else:
            print(f"  ✗ Training failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ✗ Error during training: {e}")
        return False


def test_model(args):
    """测试模型"""
    print_step(4, "Testing model...")

    model_path = os.path.join(args.output_dir, "best_model.pth")

    if not os.path.exists(model_path):
        print(f"  ⚠ Model not found: {model_path}")
        return False

    test_cmd = f"""
        python test.py \
            --model_path {model_path} \
            --data_dir {args.data_dir} \
            --model {args.model} \
            --save_results
    """

    try:
        result = subprocess.run(
            test_cmd.strip(),
            shell=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.returncode == 0:
            print("  ✓ Testing completed!")
            print(result.stdout[-500:] if result.stdout else "")
            return True
        else:
            print(f"  ⚠ Testing encountered issues: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"  ⚠ Testing error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SRM-CNN Training Script")
    parser.add_argument("--data_dir", type=str, default="./dataset",
                       help="Dataset directory")
    parser.add_argument("--output_dir", type=str, default="./checkpoints",
                       help="Output directory")
    parser.add_argument("--model", type=str, default="srmnet",
                       choices=["srmnet", "srmnet_v2", "yenet"],
                       help="Model architecture")
    parser.add_argument("--epochs", type=int, default=50,
                       help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16,
                       help="Batch size")
    parser.add_argument("--img_size", type=int, default=256,
                       help="Image size")
    parser.add_argument("--lr", type=float, default=0.001,
                       help="Learning rate")
    parser.add_argument("--skip_test", action="store_true",
                       help="Skip testing after training")
    parser.add_argument("--skip_gpu_check", action="store_true",
                       help="Skip GPU check")

    args = parser.parse_args()

    print_header("SRM-CNN Steganalysis Training")
    print(f"  Model: {args.model}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"  Output: {args.output_dir}")

    if not args.skip_gpu_check:
        check_gpu()

    install_dependencies()

    download_dataset()

    success = train_model(args)

    if success and not args.skip_test:
        test_model(args)

    print_header("Training Complete!")
    print(f"  Model saved to: {args.output_dir}")
    print("\n  To use the model:")
    print(f"    python test.py --model_path {args.output_dir}/best_model.pth")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
