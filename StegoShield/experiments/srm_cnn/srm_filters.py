"""
SRM (Spatial Rich Model) 滤波器实现
用于提取图像的残差特征，是隐写分析的重要特征。

SRM 滤波器是一组高通滤波器，能够增强隐写信号同时抑制图像内容。
"""

import torch
import torch.nn as nn
import numpy as np


class SRMFilters:
    """SRM 滤波器集合

    包含多种 3x3 高通滤波器，用于提取不同方向的残差特征。
    """

    @staticmethod
    def get_srm_filters() -> list:
        """获取所有 SRM 滤波器 (仅 3x3)"""
        filters = []

        # 3x3 方向滤波器
        filters.append(np.array([
            [1, 2, 1],
            [0, 0, 0],
            [-1, -2, -1]
        ], dtype=np.float32) / 4.0)

        filters.append(np.array([
            [1, 0, -1],
            [2, 0, -2],
            [1, 0, -1]
        ], dtype=np.float32) / 4.0)

        filters.append(np.array([
            [2, 1, 0],
            [1, 0, -1],
            [0, -1, -2]
        ], dtype=np.float32) / 4.0)

        filters.append(np.array([
            [0, 1, 2],
            [-1, 0, 1],
            [-2, -1, 0]
        ], dtype=np.float32) / 4.0)

        # 边缘检测
        filters.append(np.array([
            [0, -1, 0],
            [-1, 4, -1],
            [0, -1, 0]
        ], dtype=np.float32))

        # Laplacian 变体
        filters.append(np.array([
            [-1, -1, -1],
            [-1, 8, -1],
            [-1, -1, -1]
        ], dtype=np.float32) / 8.0)

        # CuDNN 高通
        filters.append(np.array([
            [0.25, 0.5, 0.25],
            [0.5, -3, 0.5],
            [0.25, 0.5, 0.25]
        ], dtype=np.float32))

        # 中心差分
        filters.append(np.array([
            [0, 0, 0],
            [0, 1, 0],
            [0, -1, 0]
        ], dtype=np.float32))

        filters.append(np.array([
            [0, 0, 0],
            [0, 1, -1],
            [0, 0, 0]
        ], dtype=np.float32))

        # Sobel 梯度
        filters.append(np.array([
            [-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1]
        ], dtype=np.float32) / 4.0)

        filters.append(np.array([
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1]
        ], dtype=np.float32) / 4.0)

        return filters


class SRMLayer(nn.Module):
    """SRM 滤波层

    将输入图像通过多个高通滤波器，提取残差特征。
    """

    def __init__(self, in_channels=3, num_filters=None):
        super(SRMLayer, self).__init__()

        all_filters = SRMFilters.get_srm_filters()

        if num_filters is not None and num_filters < len(all_filters):
            self.filters = all_filters[:num_filters]
        else:
            self.filters = all_filters

        self.num_filters = len(self.filters)

        # 为每个滤波器创建独立的卷积层
        self.convs = nn.ModuleList()
        for _ in range(self.num_filters):
            self.convs.append(
                nn.Conv2d(in_channels, in_channels, kernel_size=3,
                         stride=1, padding=1, groups=in_channels, bias=False)
            )

        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        """初始化滤波器权重"""
        for i, conv in enumerate(self.convs):
            if i < len(self.filters):
                weight = torch.zeros_like(conv.weight.data)
                f = self.filters[i]
                f_tensor = torch.from_numpy(f).unsqueeze(0).unsqueeze(0)
                weight.copy_(f_tensor.expand(weight.shape[0], weight.shape[1], -1, -1))
                conv.weight.data = weight

    def forward(self, x):
        outputs = []
        for conv in self.convs:
            outputs.append(conv(x))
        return torch.cat(outputs, dim=1)


class SRMConv3D(nn.Module):
    """3D SRM 层

    考虑相邻通道的 3D 卷积，捕获跨通道残差。
    """

    def __init__(self, in_channels=3):
        super(SRMConv3D, self).__init__()

        self.conv3d_23 = nn.Conv3d(
            in_channels=1,
            out_channels=1,
            kernel_size=(2, 3, 3),
            stride=1,
            padding=(0, 1, 1),
            bias=False
        )

        self.conv3d_33 = nn.Conv3d(
            in_channels=1,
            out_channels=1,
            kernel_size=(3, 3, 3),
            stride=1,
            padding=(1, 1, 1),
            bias=False
        )

        self._init_weights_3d()

    def _init_weights_3d(self):
        """初始化 3D 卷积权重"""
        kernel_23 = np.zeros((2, 3, 3), dtype=np.float32)
        kernel_23[0] = np.array([[0, 0, 0], [1, -1, 0], [0, 0, 0]])
        kernel_23[1] = np.array([[0, 0, 0], [0, -1, 1], [0, 0, 0]])

        kernel_33 = np.zeros((3, 3, 3), dtype=np.float32)
        kernel_33[0] = np.array([[0, 1, 0], [0, -1, 0], [0, 0, 0]])
        kernel_33[1] = np.array([[1, 0, -1], [0, 0, 0], [0, 0, 0]])
        kernel_33[2] = np.array([[0, 0, 0], [0, -1, 0], [0, 1, 0]])

        self.conv3d_23.weight.data = torch.from_numpy(kernel_23).unsqueeze(0)
        self.conv3d_33.weight.data = torch.from_numpy(kernel_33).unsqueeze(0)

    def forward(self, x):
        """x: B x C x H x W"""
        B, C, H, W = x.shape
        outputs = []

        for c in range(C - 1):
            chunk = x[:, c:c+2, :, :].unsqueeze(1)
            out = self.conv3d_23(chunk).squeeze(1)
            outputs.append(out)

        x_3d = x.unsqueeze(1)
        out_33 = self.conv3d_33(x_3d)

        for c in range(C):
            outputs.append(out_33[:, :, c, :, :])

        return torch.cat(outputs, dim=1)


def create_srm_layer(arch='srm_2d', num_filters=None):
    """创建 SRM 层

    Args:
        arch: 'srm_2d' 或 'srm_3d'
        num_filters: 滤波器数量

    Returns:
        nn.Module: SRM 层
    """
    if arch == 'srm_2d':
        return SRMLayer(in_channels=3, num_filters=num_filters)
    elif arch == 'srm_3d':
        return SRMConv3D(in_channels=3)
    elif arch == 'srm_hybrid':
        layer_2d = SRMLayer(in_channels=3, num_filters=num_filters)
        return nn.Sequential(layer_2d, SRMConv3D(in_channels=30))
    else:
        raise ValueError(f"Unknown arch: {arch}")


if __name__ == '__main__':
    print("Testing SRM Filters...")

    filters = SRMFilters.get_srm_filters()
    print(f"Number of SRM filters: {len(filters)}")

    for i, f in enumerate(filters):
        print(f"  Filter {i}: shape={f.shape}")

    # 测试 SRM 层
    srm = SRMLayer(in_channels=3)
    x = torch.randn(1, 3, 256, 256)
    y = srm(x)
    print(f"\nSRM Layer test:")
    print(f"  Input: {x.shape}")
    print(f"  Output: {y.shape}")
    print(f"  Output channels: {y.shape[1]}")

    print("\n✓ SRM Filters test passed!")
