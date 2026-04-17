"""
SRM-CNN 训练脚本

训练隐写检测模型。
"""

import argparse
import copy
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, Subset

sys.path.append(os.path.dirname(__file__))

from dataset import TransformFactory, create_dataset
from model import get_model


def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    for batch_idx, (images, labels) in enumerate(dataloader):
        images = images.to(device)
        labels = labels.to(device, dtype=torch.long)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        _, predicted = outputs.max(1)
        all_preds.extend(predicted.detach().cpu().numpy())
        all_labels.extend(labels.detach().cpu().numpy())

        if (batch_idx + 1) % 10 == 0:
            print(f"    Batch {batch_idx + 1}/{len(dataloader)}, Loss: {loss.item():.4f}")

    avg_loss = total_loss / max(1, len(dataloader))
    accuracy = accuracy_score(all_labels, all_preds)
    return avg_loss, accuracy


@torch.no_grad()
def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device, dtype=torch.long)

        outputs = model(images)
        loss = criterion(outputs, labels)

        total_loss += loss.item()
        _, predicted = outputs.max(1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / max(1, len(dataloader))
    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    return avg_loss, accuracy, precision, recall, f1


def split_dataset(base_dataset, img_size, val_split=0.2, seed=42):
    dataset_len = len(base_dataset)
    val_size = max(1, int(dataset_len * val_split))
    train_size = dataset_len - val_size
    if train_size <= 0:
        raise ValueError("Dataset too small to split into train/val.")

    indices = list(range(dataset_len))
    generator = torch.Generator().manual_seed(seed)
    perm = torch.randperm(dataset_len, generator=generator).tolist()
    train_indices = perm[:train_size]
    val_indices = perm[train_size:]

    train_dataset = copy.deepcopy(base_dataset)
    val_dataset = copy.deepcopy(base_dataset)
    train_dataset.transform = TransformFactory.get_train_transform(img_size)
    val_dataset.transform = TransformFactory.get_val_transform(img_size)

    return Subset(train_dataset, train_indices), Subset(val_dataset, val_indices)


def build_dataset(args):
    print(f"\nLoading datasets...")
    print(f"  Data directory: {args.data_dir}")

    if args.synthetic:
        if not args.data_dir or not os.path.exists(args.data_dir):
            raise ValueError("Synthetic mode requires --data_dir pointing to a folder of source images.")
        base_dataset = create_dataset(
            dataset_type='synthetic',
            root_dir=args.data_dir,
            transform=TransformFactory.get_train_transform(args.img_size),
            num_samples=args.num_samples,
            img_size=args.img_size,
            embed_ratio=args.embed_ratio,
            seed=args.seed,
        )
    else:
        if not args.data_dir or not os.path.exists(args.data_dir):
            raise ValueError("Folder mode requires --data_dir containing cover/ and stego/.")
        base_dataset = create_dataset(
            dataset_type='folder',
            root_dir=args.data_dir,
            transform=TransformFactory.get_train_transform(args.img_size),
            require_pairs=args.require_pairs,
        )

    return split_dataset(base_dataset, img_size=args.img_size, val_split=args.val_split, seed=args.seed)


def train(args):
    print("=" * 60)
    print("SRM-CNN Steganalysis Training")
    print("=" * 60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

    os.makedirs(args.output_dir, exist_ok=True)
    train_dataset, val_dataset = build_dataset(args)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    print(f"\nDataset split:")
    print(f"  Train: {len(train_dataset)} samples")
    print(f"  Val: {len(val_dataset)} samples")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Epochs: {args.epochs}")

    print(f"\nCreating model: {args.model}")
    model = get_model(args.model, num_classes=2).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    best_val_acc = -1.0
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
                'args': vars(args),
            }, best_model_path)
            print(f"  ✓ New best model saved! (Acc: {val_acc:.4f})")

        if (epoch + 1) % args.save_every == 0:
            checkpoint_path = os.path.join(args.output_dir, f'checkpoint_epoch_{epoch+1}.pth')
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'args': vars(args),
            }, checkpoint_path)

    print("\n" + "=" * 60)
    print("Training completed!")
    print("=" * 60)
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Model saved to: {best_model_path}")


def main():
    parser = argparse.ArgumentParser(description='SRM-CNN Training')
    parser.add_argument('--data_dir', type=str, default='./dataset', help='Dataset directory')
    parser.add_argument('--output_dir', type=str, default='./checkpoints', help='Output directory for checkpoints')
    parser.add_argument('--model', type=str, default='srmnet', choices=['srmnet', 'srmnet_v2', 'yenet'], help='Model architecture')
    parser.add_argument('--img_size', type=int, default=256, help='Image size')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='Weight decay')
    parser.add_argument('--num_samples', type=int, default=5000, help='Number of samples for synthetic dataset')
    parser.add_argument('--embed_ratio', type=float, default=0.5, help='Positive ratio in synthetic mode')
    parser.add_argument('--val_split', type=float, default=0.2, help='Validation split ratio')
    parser.add_argument('--num_workers', type=int, default=4, help='Dataloader workers')
    parser.add_argument('--save_every', type=int, default=5, help='Checkpoint save frequency')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--synthetic', action='store_true', help='Use synthetic dataset')
    parser.add_argument('--require_pairs', action='store_true', help='Require matched cover/stego filenames in folder mode')
    args = parser.parse_args()
    train(args)


if __name__ == '__main__':
    main()
