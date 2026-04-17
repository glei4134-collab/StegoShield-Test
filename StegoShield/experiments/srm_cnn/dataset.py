"""
数据集处理模块

支持：
1. 从文件夹加载图像
2. 生成隐写样本
3. 数据增强
"""

import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import numpy as np
from torchvision import transforms
import random
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from backend.app.services.dct_stego import embed
except:
    embed = None


class StegoDataset(Dataset):
    """隐写检测数据集

    目录结构：
    ├── cover/     # 原始图片
    └── stego/     # 隐写图片
    """

    def __init__(self, root_dir, transform=None, generate_stego=False, embed_text="secret"):
        """
        Args:
            root_dir: 数据集根目录
            transform: 数据变换
            generate_stego: 是否在线生成隐写图片
            embed_text: 嵌入的文本
        """
        self.root_dir = root_dir
        self.transform = transform
        self.generate_stego = generate_stego
        self.embed_text = embed_text

        self.cover_dir = os.path.join(root_dir, 'cover')
        self.stego_dir = os.path.join(root_dir, 'stego')

        if not os.path.exists(self.cover_dir):
            raise ValueError(f"Cover directory not found: {self.cover_dir}")

        self.cover_images = sorted([
            f for f in os.listdir(self.cover_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        ])

        if generate_stego:
            self.labels = [0, 1] * len(self.cover_images)
            self.image_pairs = []
            for img in self.cover_images:
                self.image_pairs.append((os.path.join(self.cover_dir, img), 0))
                self.image_pairs.append((os.path.join(self.cover_dir, img), 1))
        else:
            self.stego_images = sorted([
                f for f in os.listdir(self.stego_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
            ])

            self.image_pairs = []
            for img in self.cover_images:
                self.image_pairs.append((os.path.join(self.cover_dir, img), 0))
            for img in self.stego_images:
                self.image_pairs.append((os.path.join(self.stego_dir, img), 1))

    def __len__(self):
        return len(self.image_pairs)

    def __getitem__(self, idx):
        img_path, label = self.image_pairs[idx]

        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            image = Image.new('RGB', (256, 256), color=(128, 128, 128))

        if self.transform:
            image = self.transform(image)

        return image, label


class SyntheticStegoDataset(Dataset):
    """合成隐写数据集

    在线生成隐写图片，用于测试或小规模实验。
    """

    def __init__(self, root_dir, transform=None, num_samples=1000,
                 img_size=256, embed_ratio=0.5):
        """
        Args:
            root_dir: 原始图片目录
            transform: 数据变换
            num_samples: 总样本数
            img_size: 图像尺寸
            embed_ratio: 隐写样本比例
        """
        self.root_dir = root_dir
        self.transform = transform
        self.num_samples = num_samples
        self.img_size = img_size
        self.embed_ratio = embed_ratio

        self.image_files = sorted([
            f for f in os.listdir(root_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        ])

        if len(self.image_files) == 0:
            raise ValueError(f"No images found in {root_dir}")

        self.samples = []
        for i in range(num_samples):
            is_stego = i >= num_samples * (1 - embed_ratio)
            self.samples.append((i % len(self.image_files), is_stego))

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        img_idx, is_stego = self.samples[idx]
        img_path = os.path.join(self.root_dir, self.image_files[img_idx])

        try:
            image = Image.open(img_path).convert('RGB')
            image = image.resize((self.img_size, self.img_size), Image.LANCZOS)
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            image = Image.new('RGB', (self.img_size, self.img_size), color=(128, 128, 128))

        if is_stego:
            try:
                import io
                buf = io.BytesIO()
                image.save(buf, format='PNG')
                buf.seek(0)
                stego_bytes = embed(buf, f"stego_{idx}")
                image = Image.open(io.BytesIO(stego_bytes))
            except Exception as e:
                print(f"Error generating stego: {e}")

        if self.transform:
            image = self.transform(image)

        return image, int(is_stego)


class TransformFactory:
    """数据变换工厂"""

    @staticmethod
    def get_train_transform(img_size=256):
        return transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(5),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])

    @staticmethod
    def get_val_transform(img_size=256):
        return transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])

    @staticmethod
    def get_test_transform(img_size=256):
        return transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])


def create_dataset(dataset_type='synthetic', **kwargs):
    """创建数据集

    Args:
        dataset_type: 'synthetic', 'folder', 'bossbase'
        **kwargs: 传递给数据集构造函数的参数

    Returns:
        Dataset: PyTorch Dataset
    """
    if dataset_type == 'synthetic':
        return SyntheticStegoDataset(**kwargs)
    elif dataset_type == 'folder':
        return StegoDataset(**kwargs)
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")


if __name__ == '__main__':
    print("Dataset module test...")

    import tempfile
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        cover_dir = os.path.join(tmpdir, 'cover')
        os.makedirs(cover_dir)

        for i in range(5):
            img = Image.fromarray(
                np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            )
            img.save(os.path.join(cover_dir, f'test_{i}.png'))

        transform = TransformFactory.get_val_transform(256)

        print(f"Created {len(os.listdir(cover_dir))} test images")

        dataset = SyntheticStegoDataset(
            root_dir=cover_dir,
            transform=transform,
            num_samples=10,
            img_size=256
        )

        print(f"Dataset size: {len(dataset)}")

        for i in range(min(3, len(dataset))):
            img, label = dataset[i]
            print(f"  Sample {i}: img.shape={img.shape}, label={label}")

    print("\n✓ Dataset test passed!")
