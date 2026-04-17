# StegoShield - 图片隐写工具

基于 LSB 隐写的图片隐写工具，支持文本和文件嵌入、提取，以及 AES-256 加密。

## 项目状态

**当前版本**: v2.0

**正式功能**:
- ✅ LSB 文本嵌入/提取
- ✅ LSB 文件嵌入/提取
- ✅ AES-256 加密
- ✅ 结构化 Payload
- ✅ 统一错误处理

**实验功能** (位于 `experiments/` 目录):
- 🔬 DCT 隐写
- 🔬 JPEG DCT 隐写
- 🔬 SRM+CNN 检测分析

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端运行在 `http://127.0.0.1:5001`

### 前端启动

```bash
cd frontend
python -m http.server 8080
```

访问 `http://localhost:8080/simple.html`

## 项目结构

```
StegoShield/
├── frontend/           # 正式前端
│   ├── simple.html     # 当前前端页面
│   └── css/simple.css  # 样式
│
├── backend/            # 正式后端 API
│   ├── app/
│   │   ├── routes/stego.py      # API 路由
│   │   ├── services/enhanced_stego.py  # LSB 隐写
│   │   ├── services/encryption.py      # AES 加密
│   │   ├── errors.py           # 错误码定义
│   │   ├── response.py          # 响应格式化
│   │   └── payload.py           # Payload 序列化
│   ├── config.py       # 配置
│   └── run.py          # 启动入口
│
├── experiments/        # 实验性功能
│   ├── analyze.py             # 分析接口
│   ├── dct_stego.py           # DCT 隐写
│   ├── jpeg_stego.py          # JPEG DCT
│   └── srm_cnn/               # 检测模型
│
├── tests/              # 测试脚本
│   └── test_matrix.py  # 测试矩阵
│
├── docs/               # 文档
│   └── API_CONTRACT.md # API 契约
│
└── deprecated/         # 已废弃代码
```

## API 接口

### 嵌入数据 `/api/embed`

```json
{
  "image": "base64编码的图片",
  "type": "text | file",
  "content": {
    "text": "要嵌入的文本",
    "fileName": "文件名（file类型时）",
    "fileData": "文件base64（file类型时）"
  },
  "encryption": {
    "enabled": false,
    "key": "密钥（可选）"
  },
  "method": "lsb"
}
```

### 提取数据 `/api/extract`

```json
{
  "image": "base64编码的图片",
  "decryption": {
    "enabled": false,
    "key": "密钥（启用解密时必需）"
  }
}
```

### 响应格式

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

错误响应：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### 错误码

| 错误码 | 说明 |
|--------|------|
| `INVALID_INPUT` | 输入参数无效 |
| `MISSING_IMAGE` | 缺少图片 |
| `MISSING_CONTENT` | 缺少嵌入内容 |
| `INVALID_BASE64` | Base64 编码无效 |
| `DECRYPTION_FAILED` | 解密失败（密钥错误） |
| `EXTRACTION_FAILED` | 提取失败 |
| `NO_HIDDEN_DATA` | 图片中无隐藏数据 |

## 支持的图片格式

- PNG (推荐)
- BMP
- JPEG

## 限制

| 项目 | 限制 |
|------|------|
| 图片最大尺寸 | 10MB |
| 加密密钥长度 | 4-64 字符 |
| 文件名最大长度 | 255 字符 |

## 运行测试

```bash
cd tests
pytest test_matrix.py -v
```

## 环境变量配置

复制 `backend/.env.example` 为 `.env` 并修改：

```
FLASK_DEBUG=True
FLASK_PORT=5001
SECRET_KEY=your-secret-key
MAX_CONTENT_LENGTH=10485760
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

## 协议版本

当前 API 协议版本：v2

详细协议规范请参考 [docs/API_CONTRACT.md](docs/API_CONTRACT.md)

## License

MIT
