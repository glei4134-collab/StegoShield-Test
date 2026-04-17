# ===================================
# StegoShield 快速部署脚本
# ===================================

# 运行方式:
# - 本地运行: python deploy.py --local
# - Render 部署: python deploy.py --render
# - Railway 部署: python deploy.py --railway

import os
import sys
import subprocess
import shutil

PROJECT_NAME = "StegoShield"
BACKEND_DIR = "backend"
REQUIREMENTS_FILE = "requirements.txt"

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖...")
    os.chdir(BACKEND_DIR)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE], check=True)
    os.chdir("..")

def run_local():
    """本地运行"""
    print("🚀 启动本地服务器...")
    print(f"访问地址: http://127.0.0.1:5001")
    os.chdir(BACKEND_DIR)
    subprocess.run([sys.executable, "run.py"])

def setup_render():
    """配置 Render 部署"""
    print("⚙️ 配置 Render 部署...")
    
    # 创建 render.yaml
    render_config = """build_command: pip install -r requirements.txt
start_command: python run.py
stack: python
"""
    with open("render.yaml", "w", encoding="utf-8") as f:
        f.write(render_config)
    
    print("✅ Render 配置完成!")
    print("""
部署步骤:
1. 访问 https://dashboard.render.com
2. 连接你的 GitHub 仓库
3. 创建 Web Service，选择你的仓库
4. 自动检测 render.yaml，部署完成!

访问地址: https://你的项目名.onrender.com
""")

def setup_railway():
    """配置 Railway 部署"""
    print("⚙️ 配置 Railway 部署...")
    
    # 创建 railway.json
    railway_config = """{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfile": "Dockerfile.web"
  },
  "deploy": {
    "numInstances": 1
  }
}"""
    with open("railway.json", "w", encoding="utf-8") as f:
        f.write(railway_config)
    
    print("✅ Railway 配置完成!")
    print("""
部署步骤:
1. 访问 https://railway.app
2. 连接你的 GitHub 仓库
3. 创建新项目，选择你的仓库
4. 自动检测 Dockerfile，部署完成!

访问地址: https://你的项目名.railway.app
""")

def setup_github():
    """初始化 Git 并推送到 GitHub"""
    print("📝 初始化 Git...")
    
    # 初始化
    subprocess.run(["git", "init"], check=False)
    subprocess.run(["git", "add", "."], check=False)
    
    # 创建 .gitignore
    gitignore = """__pycache__/
*.pyc
.pytest_cache/
.git/
data/
*.png
*.jpg
"""
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore)
    
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", f"{PROJECT_NAME} v2.0 - 完整隐写功能"], check=False)
    
    print("""
✅ Git 初始化完成!

手动部署步骤:
1. 在 GitHub 创建新仓库: https://github.com/new
2. 复制仓库地址
3. 运行: git remote add origin 你的仓库地址
4. 运行: git push -u origin main

然后在 Render/Railway 后台部署即可!
""")

def main():
    if len(sys.argv) < 2:
        print("""
StegoShield 快速部署
====================

用法:
  python deploy.py --local      本地运行
  python deploy.py --render    配置 Render 部署
  python deploy.py --railway  配置 Railway 部署
  python deploy.py --github    初始化 Git (手动部署)
  python deploy.py --all        全部配置
""")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == "--local":
        install_dependencies()
        run_local()
    elif mode == "--render":
        setup_render()
    elif mode == "--railway":
        setup_railway()
    elif mode == "--github":
        setup_github()
    elif mode == "--all":
        install_dependencies()
        setup_render()
        setup_railway()
        setup_github()
    else:
        print(f"未知参数: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()