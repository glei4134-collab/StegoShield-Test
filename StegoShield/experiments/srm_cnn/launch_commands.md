# 云平台启动脚本 - 直接复制使用

## 方式一：Shell 脚本（推荐）

将以下内容复制到云平台的"启动脚本"框中：

```bash
#!/bin/bash
cd /mnt/data

# 安装依赖
pip install torch torchvision numpy scipy pillow scikit-learn pycryptodome -q

# 创建测试数据集
python3 << 'EOF'
import os
from PIL import Image
import numpy as np

cover_dir = "dataset/cover"
os.makedirs(cover_dir, exist_ok=True)

for i in range(100):
    img = Image.fromarray(np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8))
    img.save(os.path.join(cover_dir, f"test_{i:03d}.png"))

print(f"Created {len(os.listdir(cover_dir))} test images")
EOF

# 训练模型
python3 train.py \
    --data_dir ./dataset \
    --epochs 50 \
    --batch_size 16 \
    --img_size 256 \
    --lr 0.001 \
    --output_dir ./checkpoints \
    --model srmnet

# 测试模型
python3 test.py \
    --model_path ./checkpoints/best_model.pth \
    --data_dir ./dataset \
    --model srmnet \
    --save_results

echo "Training complete!"
```

## 方式二：Python 脚本

在云平台的"启动脚本"框中填写：

```bash
python3 /mnt/data/run_training.py --epochs 50 --batch_size 16 --output_dir ./checkpoints
```

## 方式三：完整版（需要上传数据集）

```bash
#!/bin/bash
cd /mnt/data

# 安装依赖
pip install torch torchvision numpy scipy pillow scikit-learn pycryptodome -q

# 下载 Bossbase 数据集（如果有链接）
# wget -O Bossbase-1.01.zip http://example.com/Bossbase-1.01.zip
# unzip -q Bossbase-1.01.zip
# mv Bossbase-1.01/* dataset/cover/

# 训练
python3 train.py \
    --data_dir ./dataset \
    --epochs 100 \
    --batch_size 32 \
    --img_size 256 \
    --lr 0.001 \
    --output_dir ./checkpoints \
    --model srmnet_v2
```

## 运行时限建议

| Epochs | 预计时间 | 推荐时限 |
|--------|---------|---------|
| 50 | 2-3 小时 | 4 小时 |
| 100 | 4-6 小时 | 8 小时 |
| 200 | 8-12 小时 | 12 小时 |

## 输出文件

训练完成后，在 `/mnt/data/checkpoints/` 目录下：
- `best_model.pth` - 最佳模型
- `checkpoint_epoch_*.pth` - 检查点

## 下载模型

训练完成后，可以从 `/mnt/data/checkpoints/best_model.pth` 下载训练好的模型。
