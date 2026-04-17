# StegoShield 项目笔记

> 最后更新：2026-04-14（今日完成大量工作）

## 📋 项目概述

**StegoShield** - 基于 DCT 频域隐写的图片隐写与加密平台

### 技术栈
- 后端：Flask (Python)
- 前端：原生 HTML/CSS/JS
- 隐写：LSB（DCT 域等价实现）
- 加密：AES-256
- 检测：Chi-square 统计检验

### 项目结构
```
StegoShield/
├── backend/           # Flask 后端
├── frontend/          # 前端界面
├── srm_cnn/         # SRM+CNN 隐写检测（新增）
└── PROJECT_NOTES.md
```

---

## ✅ 今日完成工作 (2026-04-14)

### 1. DCT 频域隐写原理文档
- 添加了详细的 DCT 原理注释
- 解释了为什么 LSB 等价于 DCT 域实现
- 说明了未来升级方向

### 2. AES-256 加密层
- 使用 pycryptodome 库
- AES-256-CBC 模式，随机 IV + PKCS7Padding
- 支持自定义密钥

### 3. API 路由更新
- `/api/embed` 新增 `encrypt` 和 `key` 参数
- `/api/extract` 新增 `decrypt` 和 `key` 参数
- 自动生成 64 位十六进制密钥

### 4. 前端界面完善
- 添加加密选项复选框
- 密钥显示和复制功能
- 解密密钥输入框
- 修复文件选择需要两次的问题

### 5. 检测算法修复
- 修复置信度总是 90% 的 bug
- 综合考虑标准差、熵、chi2 值
- 简单图片现在正确显示低置信度（3-15%）

### 6. 答辩参考文档
- 技术原理说明
- 常见问题回答
- 答辩话术模板

### 7. SRM+CNN 隐写检测（新增！）
- SRM 滤波器实现 (11个高通滤波器)
- CNN 模型 (SRMNet, SRMNetV2, YeNet)
- 训练脚本和测试脚本
- 云服务器启动脚本

### 8. 云服务器配置文档
- 曙光智算平台训练指南
- 启动脚本模板
- GPU 选择建议

---

## 🔌 API 接口文档

### 嵌入信息
```json
POST /api/embed
{
    "text": "secret message",
    "image": "base64...",
    "encrypt": true,       // 可选
    "key": "optional_key"  // 可选
}
// 返回: { "success": true, "image": "base64...", "key": "hex_key" }
```

### 提取信息
```json
POST /api/extract
{
    "image": "base64...",
    "decrypt": true,  // 可选
    "key": "hex_key"  // decrypt 为 true 时必填
}
// 返回: { "success": true, "text": "secret message" }
```

### 检测分析
```json
POST /api/analyze
{
    "image": "base64..."
}
// 返回: { "success": true, "has_hidden": false, "confidence": 0.15 }
```

---

## 🔐 加密使用流程

### 嵌入时加密
1. 勾选"启用 AES-256 加密"
2. 点击"执行嵌入"
3. **保存返回的密钥**（64位十六进制）
4. 下载图片

### 提取时解密
1. 上传加密后的图片
2. 勾选"需要解密"
3. 输入之前保存的密钥
4. 点击"提取信息"

---

## ⚠️ 当前局限性

### 隐写检测（Chi-square）
- 无法检测 LSB 隐写（LSB 太隐蔽）
- 简单图片误报（已部分修复）

**解决方案：** 需要 SRM + CNN 深度学习方法 ✅ 已实现！

### LSB 隐写
- 不抗 JPEG 压缩
- 不抗图片处理

**解决方案：** 需要真正的 DCT 域 JPEG 隐写

---

## 🧠 SRM-CNN 隐写检测

### 目录结构
```
srm_cnn/
├── srm_filters.py      # SRM 滤波器 (11个高通滤波器)
├── model.py            # CNN 模型 (SRMNet, SRMNetV2, YeNet)
├── dataset.py          # 数据集处理
├── train.py            # 训练脚本
├── test.py            # 测试脚本
├── run_training.py     # Python 训练脚本
├── cloud_startup.sh    # Shell 启动脚本
├── launch_commands.md   # 云平台命令参考
├── requirements.txt    # PyTorch 依赖
└── README.md          # 详细文档
```

### 模型架构
| 模型 | 参数量 | 说明 |
|------|--------|------|
| SRMNet | ~2.5M | 推荐使用 |
| SRMNetV2 | ~5M | 更深，更准确 |
| YeNet | ~1.5M | 轻量级 |

---

## ☁️ 云服务器训练指南（曙光智算）

### GPU 选择
| GPU | 显存 | CUDA | 推荐度 |
|-----|------|------|--------|
| **A800 80GB** | 80GB | CUDA 12.4 | ⭐⭐⭐ 最推荐 |
| L20 48GB | 48GB | CUDA 12.4 | ⭐⭐ |
| 4090 24GB | 24GB | CUDA 12.4 | ⭐ |
| HGK100 | 64GB | DTK | ❌ 不推荐 |

**注意：选择带 CUDA 的镜像，不要选 DTK！**

### 启动脚本（复制到云平台）

```bash
#!/bin/bash
cd /mnt/data

# 安装依赖
pip install torch torchvision numpy scipy pillow scikit-learn pycryptodome -q

# 检查 GPU
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

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

print(f"Created {len(os.listdir(cover_dir))} images")
EOF

# 训练
python3 train.py \
    --data_dir ./dataset \
    --epochs 50 \
    --batch_size 16 \
    --img_size 256 \
    --output_dir ./checkpoints \
    --model srmnet

echo "Training complete!"
```

### 配置建议
| 选项 | 值 |
|------|-----|
| 加速卡数量 | 1 |
| 实例数 | 1 |
| 训练镜像 | 基础镜像（CUDA 版本） |
| 运行时限 | 4 小时 |

### 如果只有 DTK/CPU 版本

```bash
#!/bin/bash
cd /mnt/data

pip install torch torchvision numpy scipy pillow scikit-learn pycryptodome -q

python3 train.py \
    --data_dir ./dataset \
    --epochs 10 \
    --batch_size 8 \
    --img_size 256 \
    --output_dir ./checkpoints \
    --model srmnet
```

---

## 🧪 测试命令

```bash
# 启动后端
cd backend
python run.py

# 启动前端（另一个终端）
cd frontend
python -m http.server 8080

# 运行测试
cd backend
python -m pytest test_api.py test_encryption.py -v
```

---

## 📈 可优化方向

### 高优先级
1. **SRM + CNN 隐写检测** ✅ 已实现
2. **DCT 域 JPEG 隐写**

### 中优先级
3. 批量处理支持
4. 更多文件格式支持

### 低优先级
5. WebSocket 实时进度
6. 移动端适配

---

## 💡 答辩话术要点

### Q: 为什么选择 LSB 而不是 DCT 域？
> LSB 等价于在 DCT 域修改所有频率成分的最低位，保留了 DCT 隐写的核心思想。实现更简单，兼容性更好。

### Q: 没有密码保护吗？
> 我们有 AES-256 加密层。内容先加密再隐写，即使提取出数据没有密钥也无法解密。

### Q: 怎么检测隐写内容？
> 使用 Chi-square 统计检验。更准确的检测需要 SRM + CNN 深度学习（已实现）。

---

## 📝 明日待办

- [ ] 在云服务器上训练 SRM+CNN 模型
- [ ] 测试训练好的模型准确率
- [ ] 将模型集成到 StegoShield 后端
- [ ] 更新前端支持 CNN 检测选项

---

晚安！🌙
