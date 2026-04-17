# StegoShield API 契约

## 概述

- **基础 URL**: `http://127.0.0.1:5001`
- **内容类型**: `application/json`
- **响应格式**: 统一 JSON 格式

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... }
}
```

### 失败响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 错误码定义

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| `INVALID_INPUT` | 输入参数无效 | 400 |
| `MISSING_IMAGE` | 缺少图片 | 400 |
| `MISSING_CONTENT` | 缺少嵌入内容 | 400 |
| `INVALID_IMAGE` | 图片格式无效 | 400 |
| `INVALID_BASE64` | Base64 编码无效 | 400 |
| `IMAGE_TOO_LARGE` | 图片过大 | 400 |
| `INVALID_METHOD` | 不支持的方法 | 400 |
| `ENCRYPTION_FAILED` | 加密失败 | 500 |
| `DECRYPTION_FAILED` | 解密失败（密钥错误或数据损坏） | 400 |
| `EXTRACTION_FAILED` | 提取失败 | 500 |
| `NO_HIDDEN_DATA` | 图片中无隐藏数据 | 404 |
| `INTERNAL_ERROR` | 内部错误 | 500 |

---

## API 接口

### 1. 嵌入数据 `/api/embed`

将文本或文件嵌入到图片中。

#### 请求

```json
{
  "image": "base64编码的图片（必需）",
  "type": "text | file",
  "content": {
    "text": "要嵌入的文本（type=text时必需）",
    "fileName": "文件名（type=file时必需）",
    "fileData": "文件的base64编码（type=file时必需）"
  },
  "encryption": {
    "enabled": false,
    "key": "加密密钥（可选，不提供则自动生成）"
  },
  "method": "lsb"
}
```

#### 请求示例

**嵌入文本（不加密）**

```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "type": "text",
  "content": {
    "text": "这是一个秘密消息"
  }
}
```

**嵌入文本（加密）**

```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "type": "text",
  "content": {
    "text": "这是一个秘密消息"
  },
  "encryption": {
    "enabled": true,
    "key": "自定义密钥"
  }
}
```

**嵌入文件**

```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "type": "file",
  "content": {
    "fileName": "document.pdf",
    "fileData": "JVBERi0xLjQK..."
  },
  "encryption": {
    "enabled": false
  }
}
```

#### 成功响应

```json
{
  "success": true,
  "data": {
    "image": "base64编码的结果图片",
    "encryption": {
      "enabled": true,
      "key": "生成的密钥（仅当启用加密且未提供密钥时）"
    }
  },
  "message": "数据嵌入成功"
}
```

#### 失败响应

```json
{
  "success": false,
  "error": {
    "code": "MISSING_CONTENT",
    "message": "未提供嵌入内容"
  }
}
```

---

### 2. 提取数据 `/api/extract`

从图片中提取隐藏的数据。

#### 请求

```json
{
  "image": "base64编码的图片（必需）",
  "decryption": {
    "enabled": false,
    "key": "解密密钥（启用解密时必需）"
  }
}
```

#### 请求示例

**提取文本（无加密）**

```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
}
```

**提取加密数据**

```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "decryption": {
    "enabled": true,
    "key": "用户的密钥"
  }
}
```

#### 成功响应

**提取文本**

```json
{
  "success": true,
  "data": {
    "type": "text",
    "text": "提取的文本内容"
  }
}
```

**提取文件**

```json
{
  "success": true,
  "data": {
    "type": "file",
    "fileName": "document.pdf",
    "fileData": "JVBERi0xLjQK...",
    "mimeType": "application/pdf"
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "error": {
    "code": "DECRYPTION_FAILED",
    "message": "解密失败，密钥可能错误或数据已损坏"
  }
}
```

---

## Payload 结构设计

### 内部格式

为了统一处理文本和文件，采用结构化的 payload 格式：

```
[HEADER][METADATA][CONTENT]
```

#### Header (16 bytes)

| 字段 | 长度 | 说明 |
|------|------|------|
| Magic | 4 | 固定值 `STG0` |
| Version | 1 | 协议版本号（当前为1）|
| Type | 1 | 0=文本, 1=文件 |
| Flags | 2 | 加密标志等 |
| Reserved | 8 | 保留字段 |

#### Metadata (变长)

**文本类型**

```
[METADATA_LENGTH(4)][TEXT_LENGTH(4)]
```

**文件类型**

```
[METADATA_LENGTH(4)][FILENAME_LENGTH(2)][FILENAME][MIME_LENGTH(2)][MIME_TYPE][CONTENT_LENGTH(4)]
```

#### Content

- 文本：原始 UTF-8 字节
- 文件：原始二进制数据

---

## 图片格式支持

| 格式 | 嵌入 | 提取 | 说明 |
|------|------|------|------|
| PNG | ✅ | ✅ | 推荐使用 |
| BMP | ✅ | ✅ | 支持 |
| JPEG | ✅ | ✅ | 可能有轻微质量损失 |

## 限制

| 项目 | 限制 |
|------|------|
| 图片最大尺寸 | 10MB |
| 单次嵌入最大容量 | 约图片大小的 10% |
| 加密密钥长度 | 4-64 字符 |
| 文件名最大长度 | 255 字符 |

---

## 变更历史

### v2 (当前)

- 统一请求/响应格式
- 添加错误码系统
- 支持结构化 payload
- 明确 type 字段区分文本/文件

### v1 (已废弃)

- 字段命名不统一
- 无错误码
- 使用 `|||` 分隔符
