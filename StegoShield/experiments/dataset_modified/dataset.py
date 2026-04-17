"""
数据集处理模块

支持：
1. 从文件夹加载图像
2. 生成隐写样本
3. 数据增强
"""

import io
import os
import random
import sys
from typing import Sequence

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from backend.app.services.dct_stego import embed as dct_embed
except Exception:
    dct_embed = None


class Compose:
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, image):
        for t in self.transforms:
            image = t(image)
        return image


class Resize:
    def __init__(self, size: Sequence[int]):
        self.size = tuple(size)

    def __call__(self, image: Image.Image):
        return image.resize(self.size, Image.LANCZOS)


class RandomHorizontalFlip:
    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, image: Image.Image):
        if random.random() < self.p:
            return image.transpose(Image.FLIP_LEFT_RIGHT)
        return image


class RandomVerticalFlip:
    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, image: Image.Image):
        if random.random() < self.p:
            return image.transpose(Image.FLIP_TOP_BOTTOM)
        return image


class ToTensor:
    def __call__(self, image: Image.Image):
        arr = np.asarray(image, dtype=np.float32) / 255.0
        if arr.ndim == 2:
            arr = arr[:, :, None]
        arr = np.transpose(arr, (2, 0, 1))
        return torch.from_numpy(arr)


class Normalize:
    def __init__(self, mean, std):
        self.mean = torch.tensor(mean, dtype=torch.float32).view(-1, 1, 1)
        self.std = torch.tensor(std, dtype=torch.float32).view(-1, 1, 1)

    def __call__(self, tensor: torch.Tensor):
        return (tensor - self.mean) / self.std


class StegoDataset(Dataset):
    """隐写检测数据集

    目录结构：
    ├── cover/
    └── stego/
    """

    def __init__(self, root_dir, transform=None, require_pairs=False):
        self.root_dir = root_dir
        self.transform = transform
        self.require_pairs = require_pairs

        self.cover_dir = os.path.join(root_dir, 'cover')
        self.stego_dir = os.path.join(root_dir, 'stego')

        if not os.path.isdir(self.cover_dir):
            raise ValueError(f"Cover directory not found: {self.cover_dir}")
        if not os.path.isdir(self.stego_dir):
            raise ValueError(f"Stego directory not found: {self.stego_dir}")

        self.cover_images = sorted(self._list_images(self.cover_dir))
        self.stego_images = sorted(self._list_images(self.stego_dir))

        if not self.cover_images:
            raise ValueError(f"No cover images found in {self.cover_dir}")
        if not self.stego_images:
            raise ValueError(f"No stego images found in {self.stego_dir}")

        if require_pairs:
            common_names = sorted(set(self.cover_images) & set(self.stego_images))
            if not common_names:
                raise ValueError("No matched cover/stego filenames found.")
            self.image_pairs = [
                (os.path.join(self.cover_dir, name), 0) for name in common_names
            ] + [
                (os.path.join(self.stego_dir, name), 1) for name in common_names
            ]
        else:
            self.image_pairs = [
                (os.path.join(self.cover_dir, name), 0) for name in self.cover_images
            ] + [
                (os.path.join(self.stego_dir, name), 1) for name in self.stego_images
            ]

    @staticmethod
    def _list_images(folder):
        return [
            f for f in os.listdir(folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        ]

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

        return image, int(label)


class SyntheticStegoDataset(Dataset):
    """合成隐写数据集。

    优先使用外部 embed；不可用时使用稳定的最低位替换生成伪 stego，避免假标签。
    """

    def __init__(
        self,
        root_dir,
        transform=None,
        num_samples=1000,
        img_size=256,
        embed_ratio=0.5,
        seed: int = 42,
    ):
        self.root_dir = root_dir
        self.transform = transform
        self.num_samples = num_samples
        self.img_size = img_size
        self.embed_ratio = embed_ratio
        self.rng = random.Random(seed)

        self.image_files = sorted([
            f for f in os.listdir(root_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        ])

        if len(self.image_files) == 0:
            raise ValueError(f"No images found in {root_dir}")

        self.samples = []
        num_stego = int(round(num_samples * embed_ratio))
        labels = [0] * (num_samples - num_stego) + [1] * num_stego
        self.rng.shuffle(labels)
        for i, label in enumerate(labels):
            self.samples.append((i % len(self.image_files), label))

    def __len__(self):
        return self.num_samples

    def _fallback_embed(self, image: Image.Image, idx: int) -> Image.Image:
        arr = np.array(image).copy()
        flat = arr.reshape(-1)

        num_bits = max(1, min(flat.size // 128, 1024))
        bit_rng = np.random.default_rng(seed=idx)
        positions = bit_rng.choice(flat.size, size=num_bits, replace=False)
        bits = bit_rng.integers(0, 2, size=num_bits, dtype=np.uint8)

        flat[positions] = (flat[positions] & 0xFE) | bits
        return Image.fromarray(arr)

    def _generate_stego(self, image: Image.Image, idx: int) -> Image.Image:
        if dct_embed is not None:
            try:
                buf = io.BytesIO()
                image.save(buf, format='PNG')
                buf.seek(0)
                stego_bytes = dct_embed(buf, f"stego_{idx}")
                return Image.open(io.BytesIO(stego_bytes)).convert('RGB')
            except Exception as e:
                print(f"Warning: external embed failed, fallback to LSB mode: {e}")
        return self._fallback_embed(image, idx)

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
            image = self._generate_stego(image, idx)

        if self.transform:
            image = self.transform(image)

        return image, int(is_stego)


class TransformFactory:
    """数据变换工厂"""

    _MEAN = [0.485, 0.456, 0.406]
    _STD = [0.229, 0.224, 0.225]

    @staticmethod
    def get_train_transform(img_size=256):
        return Compose([
            Resize((img_size, img_size)),
            RandomHorizontalFlip(),
            RandomVerticalFlip(),
            ToTensor(),
            Normalize(mean=TransformFactory._MEAN, std=TransformFactory._STD),
        ])

    @staticmethod
    def get_val_transform(img_size=256):
        return Compose([
            Resize((img_size, img_size)),
            ToTensor(),
            Normalize(mean=TransformFactory._MEAN, std=TransformFactory._STD),
        ])

    @staticmethod
    def get_test_transform(img_size=256):
        return TransformFactory.get_val_transform(img_size)


def create_dataset(dataset_type='synthetic', **kwargs):
    if dataset_type == 'synthetic':
        return SyntheticStegoDataset(**kwargs)
    if dataset_type == 'folder':
        return StegoDataset(**kwargs)
    raise ValueError(f"Unknown dataset type: {dataset_type}")


if __name__ == '__main__':
    print("Dataset module test...")

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cover_dir = os.path.join(tmpdir, 'cover')
        stego_dir = os.path.join(tmpdir, 'stego')
        os.makedirs(cover_dir)
        os.makedirs(stego_dir)

        for i in range(5):
            img = Image.fromarray(
                np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            )
            img.save(os.path.join(cover_dir, f'test_{i}.png'))
            img.save(os.path.join(stego_dir, f'test_{i}.png'))

        dataset = StegoDataset(
            root_dir=tmpdir,
            transform=TransformFactory.get_val_transform(256),
            require_pairs=True,
        )

        print(f"Dataset size: {len(dataset)}")
        for i in range(min(3, len(dataset))):
            img, label = dataset[i]
            print(f"  Sample {i}: img.shape={img.shape}, label={label}")

    print("\n✓ Dataset test passed!")
