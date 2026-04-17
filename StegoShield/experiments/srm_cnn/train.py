"""
SRM-CNN 训练脚本

训练隐写检测模型。
"""

import os
import sys
import argparse
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

sys.path.append(os.path.dirname(__file__))

from model import get_model
from dataset import create_dataset, TransformFactory


def train_epoch(model, dataloader, criterion, optimizer, device):
    """训练一个 epoch"""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for batch_idx, (images, labels) in enumerate(dataloader):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        _, predicted = outputs.max(1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

        if (batch_idx + 1) % 10 == 0:
            print(f"    Batch {batch_idx + 1}/{len(dataloader)}, Loss: {loss.item():.4f}")

    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)

    return avg_loss, accuracy


def validate(model, dataloader, criterion, device):
    """验证模型"""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()

            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)

    return avg_loss, accuracy, precision, recall, f1


def train(args):
    """训练主函数"""
    print("=" * 60)
    print("SRM-CNN Steganalysis Training")
    print("=" * 60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\nLoading datasets...")
    print(f"  Data directory: {args.data_dir}")

    if args.data_dir and os.path.exists(args.data_dir):
        train_dataset = create_dataset(
            dataset_type='synthetic' if args.synthetic else 'folder',
            root_dir=args.data_dir,
            transform=TransformFactory.get_train_transform(args.img_size),
            num_samples=args.num_samples,
            img_size=args.img_size
        )
    else:
        print(f"  Warning: Data directory not found, using test mode")
        import tempfile
        from PIL import Image
        tmpdir = tempfile.mkdtemp()
        for i in range(20):
            img = Image.fromarray(
                np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
            )
            img.save(os.path.join(tmpdir, f'test_{i}.png'))
        train_dataset = create_dataset(
            dataset_type='synthetic',
            root_dir=tmpdir,
            transform=TransformFactory.get_train_transform(args.img_size),
            num_samples=100,
            img_size=args.img_size
        )

    val_split = 0.2
    val_size = int(len(train_dataset) * val_split)
    train_size = len(train_dataset) - val_size

    train_dataset, val_dataset = torch.utils.data.random_split(
        train_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    val_dataset.dataset.transform = TransformFactory.get_val_transform(args.img_size)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True if torch.cuda.is_available() else False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True if torch.cuda.is_available() else False
    )

    print(f"\nDataset split:")
    print(f"  Train: {len(train_dataset)} samples")
    print(f"  Val: {len(val_dataset)} samples")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Epochs: {args.epochs}")

    print(f"\nCreating model: {args.model}")
    model = get_model(args.model, num_classes=2)
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    best_val_acc = 0
    best_model_path = os.path.join(args.output_dir, 'best_model.pth')

    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    for epoch in range(args.epochs):
        epoch_start = time.time()

        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        print("-" * 40)

        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_prec, val_rec, val_f1 = validate(model, val_loader, criterion, device)

        scheduler.step()

        epoch_time = time.time() - epoch_start

        print(f"\nResults:")
        print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
        print(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
        print(f"  Val Precision: {val_prec:.4f}, Recall: {val_rec:.4f}, F1: {val_f1:.4f}")
        print(f"  Time: {epoch_time:.2f}s")
        print(f"  LR: {optimizer.param_groups[0]['lr']:.6f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'val_f1': val_f1,
            }, best_model_path)
            print(f"  ✓ New best model saved! (Acc: {val_acc:.4f})")

        if (epoch + 1) % 5 == 0:
            checkpoint_path = os.path.join(args.output_dir, f'checkpoint_epoch_{epoch+1}.pth')
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
            }, checkpoint_path)

    print("\n" + "=" * 60)
    print("Training completed!")
    print("=" * 60)
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Model saved to: {best_model_path}")


def main():
    parser = argparse.ArgumentParser(description='SRM-CNN Training')
    parser.add_argument('--data_dir', type=str, default='./dataset',
                       help='Dataset directory')
    parser.add_argument('--output_dir', type=str, default='./checkpoints',
                       help='Output directory for checkpoints')
    parser.add_argument('--model', type=str, default='srmnet',
                       choices=['srmnet', 'srmnet_v2', 'yenet'],
                       help='Model architecture')
    parser.add_argument('--img_size', type=int, default=256,
                       help='Image size')
    parser.add_argument('--batch_size', type=int, default=16,
                       help='Batch size')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of epochs')
    parser.add_argument('--lr', type=float, default=0.001,
                       help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-4,
                       help='Weight decay')
    parser.add_argument('--num_samples', type=int, default=5000,
                       help='Number of samples for synthetic dataset')
    parser.add_argument('--synthetic', action='store_true',
                       help='Use synthetic dataset')

    args = parser.parse_args()

    train(args)


if __name__ == '__main__':
    main()
