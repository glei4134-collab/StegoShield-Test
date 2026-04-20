# StegoShield VIP API服务器测试指南

## 快速开始

### 1. 启动应用并登录VIP用户

1. 打开StegoShield桌面应用
2. 登录或注册VIP用户
3. 点击"升级到VIP"按钮激活VIP会员

### 2. 启动API服务器

1. 进入"VIP管理中心"页面
2. 点击"启动服务器"按钮
3. 服务器将在 http://localhost:5001/ 启动

### 3. 创建API密钥

1. 在"API密钥管理"区域
2. 点击"+ 生成新密钥"按钮
3. 复制生成的API密钥（只会显示一次）

## API端点

### 健康检查

**端点**: `GET /api/v1/health`  
**认证**: 不需要  
**示例**:
```bash
curl http://localhost:5001/api/v1/health
```

**响应**:
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "status": "running",
    "port": 5001,
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

### 图片隐写

**端点**: `POST /api/v1/stego/encode`  
**认证**: 需要 (X-API-Key header)  
**请求体**:
```json
{
  "ImagePath": "C:\\path\\to\\image.png",
  "Text": "要隐藏的秘密信息",
  "Algorithm": "LSB",
  "OutputPath": "C:\\path\\to\\output.png"  // 可选
}
```

**示例**:
```bash
curl -X POST http://localhost:5001/api/v1/stego/encode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"ImagePath": "C:\\test\\image.png", "Text": "Hello World", "Algorithm": "LSB"}'
```

**响应**:
```json
{
  "success": true,
  "message": "隐写成功",
  "data": {
    "output_path": "C:\\test\\output.png",
    "bytes_written": 12345,
    "algorithm": "LSB"
  }
}
```

### 提取隐藏数据

**端点**: `POST /api/v1/stego/decode`  
**认证**: 需要 (X-API-Key header)  
**请求体**:
```json
{
  "ImagePath": "C:\\path\\to\\stego_image.png",
  "Algorithm": "LSB"
}
```

**示例**:
```bash
curl -X POST http://localhost:5001/api/v1/stego/decode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"ImagePath": "C:\\test\\output.png", "Algorithm": "LSB"}'
```

**响应**:
```json
{
  "success": true,
  "message": "提取成功",
  "data": {
    "extracted_text": "Hello World",
    "confidence": 0.95,
    "algorithm": "LSB"
  }
}
```

### 获取VIP状态

**端点**: `GET /api/v1/vip/status`  
**认证**: 需要 (X-API-Key header)  
**示例**:
```bash
curl http://localhost:5001/api/v1/vip/status \
  -H "X-API-Key: your_api_key_here"
```

**响应**:
```json
{
  "success": true,
  "message": "获取VIP状态成功",
  "data": {
    "is_vip": true,
    "username": "testuser",
    "expires_at": "2025-01-01 00:00:00"
  }
}
```

### 管理API密钥

#### 获取密钥列表

**端点**: `GET /api/v1/keys`  
**认证**: 需要 (X-API-Key header)  
**示例**:
```bash
curl http://localhost:5001/api/v1/keys \
  -H "X-API-Key: your_api_key_here"
```

#### 创建新密钥

**端点**: `POST /api/v1/keys`  
**认证**: 需要 (X-API-Key header)  
**请求体**:
```json
{
  "Name": "MyApp",
  "RateLimitPerHour": 100
}
```

**示例**:
```bash
curl -X POST http://localhost:5001/api/v1/keys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"Name": "MyApp", "RateLimitPerHour": 100}'
```

#### 删除密钥

**端点**: `DELETE /api/v1/keys/{keyId}`  
**认证**: 需要 (X-API-Key header)  
**示例**:
```bash
curl -X DELETE http://localhost:5001/api/v1/keys/key_id_here \
  -H "X-API-Key: your_api_key_here"
```

## 错误响应

### 401 未授权
```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "需要提供有效的API密钥"
}
```

### 404 未找到
```json
{
  "success": false,
  "error": "NotFound",
  "message": "未找到指定的API端点"
}
```

### 429 请求过于频繁
```json
{
  "success": false,
  "error": "RateLimitExceeded",
  "message": "请求过于频繁，请稍后再试"
}
```

## 限流

- 每小时100个请求（默认）
- 响应头包含限流信息：
  - `X-RateLimit-Limit`: 总限制
  - `X-RateLimit-Remaining`: 剩余请求数
  - `X-RateLimit-Reset`: 重置时间戳

## 完整测试流程

1. **启动服务器**
   ```powershell
   # 在应用UI中点击"启动服务器"
   ```

2. **测试健康检查**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5001/api/v1/health" -Method Get
   ```

3. **准备测试图片**
   - 准备一张PNG或BMP格式的图片
   - 记录图片路径（例如：C:\test\sample.png）

4. **测试隐写**
   ```powershell
   $body = @{
       ImagePath = "C:\test\sample.png"
       Text = "这是一条测试消息"
       Algorithm = "LSB"
   } | ConvertTo-Json
   
   Invoke-RestMethod -Uri "http://localhost:5001/api/v1/stego/encode" `
       -Method Post `
       -ContentType "application/json" `
       -Headers @{ "X-API-Key" = "your_api_key" } `
       -Body $body
   ```

5. **测试提取**
   ```powershell
   $body = @{
       ImagePath = "C:\test\output.png"
       Algorithm = "LSB"
   } | ConvertTo-Json
   
   Invoke-RestMethod -Uri "http://localhost:5001/api/v1/stego/decode" `
       -Method Post `
       -ContentType "application/json" `
       -Headers @{ "X-API-Key" = "your_api_key" } `
       -Body $body
   ```

## 注意事项

1. **图片格式**: LSB算法需要PNG或BMP格式的图片
2. **数据大小**: 隐写的数据量受图片大小限制
3. **安全性**: API密钥只在创建时显示一次，请妥善保存
4. **端口占用**: 确保5001端口未被其他程序占用
5. **防火墙**: 如果需要远程访问，需要开放5001端口
