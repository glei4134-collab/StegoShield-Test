# StegoShield 项目结构

## 目录说明

```
StegoShield/
├── frontend/           # 正式前端（当前使用）
│   ├── simple.html     # 当前正式前端页面
│   ├── css/simple.css # 当前正式样式
│   └── README.md
│
├── backend/            # 正式后端 API
│   ├── app/
│   │   ├── routes/stego.py      # 正式 API 路由
│   │   ├── services/enhanced_stego.py  # LSB 核心隐写
│   │   └── services/encryption.py      # AES 加密
│   ├── run.py          # 后端启动入口
│   └── config.py       # 配置
│
├── experiments/        # 实验性功能（不保证稳定性）
│   ├── analyze.py             # 分析接口
│   ├── analyzer.py           # 分析服务
│   ├── dct_stego.py           # DCT 隐写
│   ├── jpeg_stego.py          # JPEG DCT 隐写
│   ├── dct_embed*.py          # DCT 变体实现
│   ├── srm_cnn/               # SRM+CNN 检测模型
│   ├── dataset_modified/      # 数据集处理
│   └── models/                # 预训练模型
│
├── deprecated/         # 已废弃的代码
│   ├── index.html      # 旧前端
│   ├── js/             # 旧 JS 架构
│   └── css/style.css   # 旧样式
│
├── tests/              # 测试脚本
│   ├── test_*.py       # 各种测试文件
│   ├── read_docx.py    # DOCX 读取测试
│   └── run_test_dct.py # DCT 测试运行器
│
├── data/               # 测试数据
│   ├── test_images/    # 测试图片
│   └── uploads/        # 临时上传文件
│
├── docs/               # 文档
│   └── PROJECT_NOTES.md
│
├── Dockerfile          # Docker 部署
└── README.md           # 项目说明
```

## 正式功能（Stable）

- **前端**: `frontend/simple.html`
- **后端 API**: `backend/app/routes/stego.py`
- **LSB 隐写**: `backend/app/services/enhanced_stego.py`
- **AES 加密**: `backend/app/services/encryption.py`

### 支持的功能

- LSB 文本嵌入/提取
- LSB 文件嵌入/提取
- AES 加密
- PNG/BMP 图片支持

## 实验功能（Experimental）

以下功能位于 `experiments/` 目录，不保证稳定性：

- DCT 隐写
- JPEG DCT 隐写
- SRM+CNN 检测分析
- 分析接口 `/api/analyze`

## 快速启动

### 后端

```bash
cd backend
python run.py
```

后端运行在 `http://127.0.0.1:5001`

### 前端

使用任意静态服务器：

```bash
cd frontend
python -m http.server 8080
```

访问 `http://localhost:8080/simple.html`
