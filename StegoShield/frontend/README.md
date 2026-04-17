# StegoShield Frontend

纯前端单页应用，无需构建。

## 启动

直接用浏览器打开 `index.html` 即可（前提是后端在 `localhost:5000` 运行）。

## API 依赖

- `POST /api/embed` - 嵌入信息到图片
- `POST /api/extract` - 从图片提取隐藏信息
- `POST /api/analyze` - 分析图片隐写特征

## 功能

- **嵌入信息**：将秘密文本隐藏到图片中
- **提取信息**：从隐写图片中提取秘密文本
- **检测分析**：分析图片是否包含隐写特征

## 技术栈

- 纯 HTML5 + CSS3 + JavaScript（ES6）
- Google Fonts（Inter + JetBrains Mono）
- 无外部 JS 依赖，无框架
- 响应式设计，支持桌面和平板
