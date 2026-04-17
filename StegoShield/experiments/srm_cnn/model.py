"""
SRM-CNN 隐写检测模型

基于 Spatial Rich Model (SRM) 和 CNN 的隐写检测网络。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from srm_filters import SRMLayer


class SRMNet(nn.Module):
    """SRM-CNN 隐写检测网络"""

    def __init__(self, num_classes=2, srm_type='srm_2d'):
        super(SRMNet, self).__init__()

        self.srm = SRMLayer(in_channels=3)
        self.bn1 = nn.BatchNorm2d(33)

        self.conv1 = nn.Conv2d(33, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)

        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.conv4 = nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1)
        self.bn5 = nn.BatchNorm2d(512)
        self.pool3 = nn.MaxPool2d(2, 2)

        self.conv5 = nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1)
        self.bn6 = nn.BatchNorm2d(512)

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc1 = nn.Linear(512, 256)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.srm(x)
        x = self.bn1(x)
        x = F.relu(self.conv1(x))
        x = self.bn2(x)
        x = self.pool1(x)

        x = F.relu(self.conv2(x))
        x = self.bn3(x)
        x = F.relu(self.conv3(x))
        x = self.bn4(x)
        x = self.pool2(x)

        x = F.relu(self.conv4(x))
        x = self.bn5(x)
        x = self.pool3(x)

        x = F.relu(self.conv5(x))
        x = self.bn6(x)

        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class ResidualBlock(nn.Module):
    """基础残差块，自动处理通道投影。"""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x):
        identity = self.shortcut(x)
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = out + identity
        return F.relu(out)


class SRMNetV2(nn.Module):
    """SRM-CNN V2 - 更深的网络，使用稳定的残差块。"""

    def __init__(self, num_classes=2):
        super(SRMNetV2, self).__init__()

        self.srm = SRMLayer(in_channels=3)
        self.bn_input = nn.BatchNorm2d(33)

        self.block1 = ResidualBlock(33, 64)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.block2 = ResidualBlock(64, 128)
        self.block3 = ResidualBlock(128, 128)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.block4 = ResidualBlock(128, 256)
        self.block5 = ResidualBlock(256, 256)
        self.pool3 = nn.MaxPool2d(2, 2)

        self.block6 = ResidualBlock(256, 512)
        self.block7 = ResidualBlock(512, 512)
        self.pool4 = nn.MaxPool2d(2, 2)

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc1 = nn.Linear(512, 256)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.srm(x)
        x = self.bn_input(x)

        x = self.block1(x)
        x = self.pool1(x)

        x = self.block2(x)
        x = self.block3(x)
        x = self.pool2(x)

        x = self.block4(x)
        x = self.block5(x)
        x = self.pool3(x)

        x = self.block6(x)
        x = self.block7(x)
        x = self.pool4(x)

        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class YeNet(nn.Module):
    """YeNet - 经典隐写分析网络"""

    def __init__(self, num_classes=2):
        super(YeNet, self).__init__()

        self.srm = SRMLayer(in_channels=3)

        self.conv1 = nn.Conv2d(33, 32, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm2d(32)

        self.conv2 = nn.Conv2d(32, 32, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.dropout1 = nn.Dropout(0.3)

        self.conv3 = nn.Conv2d(32, 64, kernel_size=5, padding=2)
        self.bn3 = nn.BatchNorm2d(64)

        self.conv4 = nn.Conv2d(64, 64, kernel_size=5, padding=2)
        self.bn4 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.dropout2 = nn.Dropout(0.3)

        self.conv5 = nn.Conv2d(64, 128, kernel_size=5, padding=2)
        self.bn5 = nn.BatchNorm2d(128)

        self.conv6 = nn.Conv2d(128, 128, kernel_size=5, padding=2)
        self.bn6 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        self.dropout3 = nn.Dropout(0.3)

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc1 = nn.Linear(128, 128)
        self.dropout4 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.srm(x)

        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool1(x)
        x = self.dropout1(x)

        x = F.relu(self.bn3(self.conv3(x)))
        x = F.relu(self.bn4(self.conv4(x)))
        x = self.pool2(x)
        x = self.dropout2(x)

        x = F.relu(self.bn5(self.conv5(x)))
        x = F.relu(self.bn6(self.conv6(x)))
        x = self.pool3(x)
        x = self.dropout3(x)

        x = self.global_pool(x)
        x = x.view(x.size(0), -1)

        x = F.relu(self.fc1(x))
        x = self.dropout4(x)
        x = self.fc2(x)
        return x


def get_model(model_name='srmnet', num_classes=2):
    if model_name == 'srmnet':
        return SRMNet(num_classes=num_classes)
    if model_name == 'srmnet_v2':
        return SRMNetV2(num_classes=num_classes)
    if model_name == 'yenet':
        return YeNet(num_classes=num_classes)
    raise ValueError(f"Unknown model: {model_name}")


if __name__ == '__main__':
    print("Testing models...")

    models = {
        'SRMNet': SRMNet(),
        'SRMNetV2': SRMNetV2(),
        'YeNet': YeNet()
    }

    x = torch.randn(2, 3, 256, 256)

    for name, model in models.items():
        model.eval()
        with torch.no_grad():
            y = model(x)
        print(f"{name}:")
        print(f"  Input: {x.shape}")
        print(f"  Output: {y.shape}")
        print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")

    print("\n✓ Model test passed!")