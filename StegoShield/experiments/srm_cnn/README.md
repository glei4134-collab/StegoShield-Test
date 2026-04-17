# SRM-CNN 隐写检测

基于 Spatial Rich Model (SRM) 和 CNN 的隐写检测系统。

## 📁 项目结构

```
srm_cnn/
├── srm_filters.py      # SRM 滤波器实现
├── model.py            # CNN 模型定义
├── dataset.py          # 数据集处理
├── train.py            # 训练脚本
├── test.py             # 测试脚本
├── requirements.txt    # 依赖包
├── dataset/
│   ├── cover/         # 原始图片
│   ├── stego/          # 隐写图片
│   └── download_bossbase.sh  # 数据集下载脚本
└── checkpoints/       # 训练模型保存目录
```

## 🚀 快速开始

### 1. 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 准备数据集

**方式 1: 下载 Bossbase (推荐)**
```bash
# 运行下载脚本
bash dataset/download_bossbase.sh

# 手动下载
wget http://dde.binguo.me/Bossbase-1.01.zip
unzip Bossbase-1.01.zip
```

**方式 2: 快速测试 (使用合成数据)**
```bash
# 使用合成数据测试，不需要真实数据集
python train.py --synthetic --num_samples 500
```

### 3. 训练模型

```bash
# 基本训练
python train.py --data_dir ./dataset --epochs 50 --batch_size 16

# 使用 GPU
python train.py --data_dir ./dataset --epochs 50 --batch_size 32

# 使用更大的模型
python train.py --data_dir ./dataset --model srmnet_v2 --epochs 100
```

### 4. 测试模型

```bash
# 测试训练好的模型
python test.py --model_path ./checkpoints/best_model.pth --data_dir ./dataset

# 保存结果
python test.py --model_path ./checkpoints/best_model.pth --data_dir ./dataset --save_results
```

## 📊 模型选择

| 模型 | 参数量 | 适用场景 |
|------|--------|---------|
| `srmnet` | ~2.5M | 快速训练，推荐 |
| `srmnet_v2` | ~5M | 更深，更准确 |
| `yenet` | ~1.5M | 轻量级 |

## 🔧 参数说明

### 训练参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--data_dir` | `./dataset` | 数据集目录 |
| `--model` | `srmnet` | 模型架构 |
| `--img_size` | `256` | 图像尺寸 |
| `--batch_size` | `16` | 批次大小 |
| `--epochs` | `50` | 训练轮数 |
| `--lr` | `0.001` | 学习率 |
| `--output_dir` | `./checkpoints` | 输出目录 |

### 测试参数

| 参数 | 说明 |
|------|------|
| `--model_path` | 训练好的模型路径 |
| `--data_dir` | 测试数据集目录 |
| `--save_results` | 保存结果到 JSON |

## 📈 显存需求

| 模型 | Batch Size | 显存需求 |
|------|-----------|---------|
| srmnet | 16 | ~4GB |
| srmnet | 32 | ~6GB |
| srmnet_v2 | 16 | ~6GB |
| srmnet_v2 | 32 | ~10GB |

推荐使用 **A800 80GB** 或 **L20 48GB** GPU。

## 🎯 预期性能

在 Bossbase 数据集上:

| 指标 | 预期值 |
|------|--------|
| Accuracy | 80-90% |
| Precision | 75-85% |
| Recall | 80-90% |
| F1 | 78-85% |

## 🔍 使用预训练模型

训练完成后，模型保存在:
- `./checkpoints/best_model.pth` - 最佳模型
- `./checkpoints/checkpoint_epoch_*.pth` - 检查点

## 📝 API 集成

训练好的模型可以集成到 StegoShield 后端:

```python
import torch
from model import get_model

# 加载模型
model = get_model('srmnet', num_classes=2)
checkpoint = torch.load('checkpoints/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# 预测
def predict(image_tensor):
    with torch.no_grad():
        output = model(image_tensor)
        prob = torch.softmax(output, dim=1)
        return prob[0, 1].item()  # 返回隐写概率
```

## ⚠️ 注意事项

1. **数据集质量**: Bossbase 是标准隐写分析数据集，图片质量影响检测效果
2. **隐写算法**: 当前使用 LSB 隐写，其他隐写算法可能需要不同模型
3. **GPU 内存**: 根据 GPU 显存调整 batch_size
4. **训练时间**: 完整训练约 2-4 小时 (A800)

## 📚 参考资料

- Fridrich, J., et al. "Steganalysis in high dimensions" (SRM)
- Ye, J., et al. "Deep CNN for Steganalysis" (YeNet)
- Bossbase Dataset: http://dde.binguo.me/

## 📄 许可证

MIT License
