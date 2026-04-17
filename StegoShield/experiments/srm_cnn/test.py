"""
SRM-CNN 测试脚本

测试训练好的模型。
"""

import os
import sys
import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

sys.path.append(os.path.dirname(__file__))

from model import get_model
from dataset import create_dataset, TransformFactory


def load_model(model_path, model_name='srmnet', device='cpu'):
    """加载模型"""
    model = get_model(model_name, num_classes=2)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    return model, checkpoint


def test_model(model, dataloader, device):
    """测试模型"""
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)

            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs[:, 1].cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)

    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    cm = confusion_matrix(all_labels, all_preds)

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'predictions': all_preds,
        'labels': all_labels,
        'probabilities': all_probs
    }


def test(args):
    """测试主函数"""
    print("=" * 60)
    print("SRM-CNN Steganalysis Testing")
    print("=" * 60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")

    print(f"\nLoading model from: {args.model_path}")
    model, checkpoint = load_model(args.model_path, args.model, device)

    if 'val_acc' in checkpoint:
        print(f"Training validation accuracy: {checkpoint['val_acc']:.4f}")
    if 'val_f1' in checkpoint:
        print(f"Training validation F1: {checkpoint['val_f1']:.4f}")

    print(f"\nLoading test dataset from: {args.data_dir}")

    if not os.path.exists(args.data_dir):
        print(f"Error: Dataset directory not found: {args.data_dir}")
        return

    test_dataset = create_dataset(
        dataset_type='folder',
        root_dir=args.data_dir,
        transform=TransformFactory.get_test_transform(args.img_size)
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4
    )

    print(f"\nTest dataset: {len(test_dataset)} samples")
    print(f"Batch size: {args.batch_size}")

    print("\n" + "=" * 60)
    print("Testing...")
    print("=" * 60)

    results = test_model(model, test_loader, device)

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"\nAccuracy:  {results['accuracy']:.4f}")
    print(f"Precision: {results['precision']:.4f}")
    print(f"Recall:    {results['recall']:.4f}")
    print(f"F1 Score:  {results['f1']:.4f}")

    print("\nConfusion Matrix:")
    print(results['confusion_matrix'])

    print("\nClassification Report:")
    target_names = ['Cover (0)', 'Stego (1)']
    print(classification_report(
        results['labels'],
        results['predictions'],
        target_names=target_names
    ))

    if args.save_results:
        import json
        results_file = os.path.join(os.path.dirname(args.model_path), 'test_results.json')
        save_results = {
            'accuracy': float(results['accuracy']),
            'precision': float(results['precision']),
            'recall': float(results['recall']),
            'f1': float(results['f1']),
            'confusion_matrix': results['confusion_matrix'].tolist()
        }
        with open(results_file, 'w') as f:
            json.dump(save_results, f, indent=2)
        print(f"\nResults saved to: {results_file}")


def predict_image(model, image_path, device='cpu'):
    """预测单张图片

    Args:
        model: 训练好的模型
        image_path: 图片路径
        device: 计算设备

    Returns:
        dict: 预测结果
    """
    from PIL import Image

    model.eval()

    transform = TransformFactory.get_test_transform(256)
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image_tensor)
        prob = torch.softmax(output, dim=1)
        confidence, predicted = prob.max(1)

    return {
        'class': predicted.item(),
        'class_name': 'Stego' if predicted.item() == 1 else 'Cover',
        'confidence': confidence.item(),
        'probability': prob[0].cpu().numpy()
    }


def main():
    parser = argparse.ArgumentParser(description='SRM-CNN Testing')
    parser.add_argument('--model_path', type=str, required=True,
                       help='Path to trained model')
    parser.add_argument('--data_dir', type=str, default='./dataset/test',
                       help='Test dataset directory')
    parser.add_argument('--model', type=str, default='srmnet',
                       choices=['srmnet', 'srmnet_v2', 'yenet'],
                       help='Model architecture')
    parser.add_argument('--img_size', type=int, default=256,
                       help='Image size')
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Batch size')
    parser.add_argument('--save_results', action='store_true',
                       help='Save results to JSON')

    args = parser.parse_args()
    test(args)


if __name__ == '__main__':
    main()
