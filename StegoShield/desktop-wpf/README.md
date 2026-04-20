# StegoShield Pro - C# WPF 桌面应用

## 🎯 项目简介

这是一个使用 C# WPF (.NET 8) 构建的原生 Windows 桌面应用程序，具有与 QQ/微信 相同的原生 Windows 界面效果。

## ✨ 主要特性

- **原生 Windows 界面** - 使用标准 Windows 控件
- **现代化设计** - 卡片式布局，渐变色标题栏
- **用户认证** - 登录/注册功能
- **积分系统** - 用户积分和使用次数统计
- **VIP功能** - VIP用户专属功能
- **API集成** - 与 Python Flask 后端无缝对接

## 🛠️ 技术栈

- **框架**: .NET 8.0 + WPF
- **UI**: XAML + MVVM 模式
- **HTTP客户端**: System.Net.Http
- **JSON解析**: Newtonsoft.Json
- **后端通信**: REST API

## 📁 项目结构

```
desktop-wpf/
├── StegoShield.Desktop.sln          # 解决方案文件
└── StegoShield.Desktop/
    ├── StegoShield.Desktop.csproj    # 项目文件
    ├── App.xaml                      # 应用程序入口
    ├── App.xaml.cs                   # 应用程序逻辑
    ├── Models/
    │   └── User.cs                  # 用户模型
    ├── Services/
    │   └── ApiService.cs            # API服务类
    └── Views/
        ├── LoginWindow.xaml          # 登录窗口
        ├── LoginWindow.xaml.cs       # 登录窗口逻辑
        ├── MainWindow.xaml          # 主窗口
        └── MainWindow.xaml.cs       # 主窗口逻辑
```

## 🚀 快速开始

### 环境要求

- Windows 10/11
- .NET 8.0 SDK
- Python 3.8+ (用于后端)

### 构建步骤

1. **安装 .NET 8.0 SDK**
   ```bash
   # 下载地址: https://dotnet.microsoft.com/download/dotnet/8.0
   ```

2. **还原依赖**
   ```bash
   cd desktop-wpf/StegoShield.Desktop
   dotnet restore
   ```

3. **编译项目**
   ```bash
   dotnet build
   ```

4. **运行项目**
   ```bash
   dotnet run
   ```

### 发布为独立exe

```bash
cd desktop-wpf/StegoShield.Desktop
dotnet publish -c Release -r win-x64 --self-contained true
```

生成的exe文件位于:
```
bin/Release/net8.0-windows/win-x64/publish/
```

## 🎨 界面预览

### 登录窗口
- 原生 Windows 窗口样式
- 标准窗口控件（关闭、最小化）
- 用户名/密码输入框
- 登录/注册按钮
- 连接状态指示器

### 主窗口
- 自定义标题栏
- 用户信息展示
- 功能卡片网格
- VIP升级提示
- 退出按钮

## 🔧 配置说明

### API 地址配置

在 `Services/ApiService.cs` 中修改:

```csharp
private const string BaseUrl = "http://127.0.0.1:5001/api";
```

### 后端路径配置

应用程序会自动查找后端路径:
1. `../desktop/backend/run.py`
2. `./backend/run.py`

## 📋 功能列表

- ✅ 用户登录
- ✅ 用户注册
- ✅ 用户信息显示
- ✅ 积分系统
- ✅ VIP状态显示
- ✅ LSB隐写工具入口
- ✅ DCT隐写工具入口
- ✅ 数据提取工具入口
- ⏳ 批量处理功能
- ⏳ VIP升级功能

## 🎯 与 Electron 版本对比

| 特性 | Electron | C# WPF |
|------|---------|--------|
| 界面原生度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 开发难度 | ⭐⭐ | ⭐⭐⭐ |
| 性能 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 打包体积 | 较大 | 较小 |
| 跨平台 | ✅ | ❌ |

## 🔮 未来计划

- [ ] 完成 VIP 升级功能
- [ ] 添加批量处理功能
- [ ] 实现本地设置存储
- [ ] 添加系统托盘功能
- [ ] 集成通知系统

## 📄 许可证

MIT License

## 👥 贡献者

StegoShield Team

---

**🎉 感谢使用 StegoShield Pro！**
