# 复制这个到 Colab 运行

# 1. 创建训练文件
train_code = '''
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

print("创建数据集...")
X = torch.randn(1000, 3, 256, 256)  # 1000张随机图片
y = torch.randint(0, 2, (1000,))   # 标签

dataset = TensorDataset(X, y)
loader = DataLoader(dataset, batch_size=16)

print("创建模型...")
from collections import OrderedDict

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.fc = nn.Linear(32, 2)
    
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

model = SimpleCNN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

print("开始训练...")
for epoch in range(50):
    total_loss = 0
    for batch_x, batch_y in loader:
        optimizer.zero_grad()
        out = model(batch_x)
        loss = criterion(out, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    if (epoch+1) % 10 == 0:
        print(f"Epoch {epoch+1}/50, Loss: {total_loss:.4f}")

print("训练完成!")
torch.save(model.state_dict(), "model.pth")
print("模型保存到 model.pth")
'''

# 写入文件
with open('train_simple.py', 'w') as f:
    f.write(train_code)

# 运行
!python train_simple.py# 复制这个到 Colab 运行

# 1. 创建训练文件
train_code = '''
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

print("创建数据集...")
X = torch.randn(1000, 3, 256, 256)  # 1000张随机图片
y = torch.randint(0, 2, (1000,))   # 标签

dataset = TensorDataset(X, y)
loader = DataLoader(dataset, batch_size=16)

print("创建模型...")
from collections import OrderedDict

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.fc = nn.Linear(32, 2)
    
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

model = SimpleCNN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

print("开始训练...")
for epoch in range(50):
    total_loss = 0
    for batch_x, batch_y in loader:
        optimizer.zero_grad()
        out = model(batch_x)
        loss = criterion(out, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    if (epoch+1) % 10 == 0:
        print(f"Epoch {epoch+1}/50, Loss: {total_loss:.4f}")

print("训练完成!")
torch.save(model.state_dict(), "model.pth")
print("模型保存到 model.pth")
'''

# 写入文件
with open('train_simple.py', 'w') as f:
    f.write(train_code)

# 运行
!python train_simple.py# 复制这个到 Colab 运行

# 1. 创建训练文件
train_code = '''
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

print("创建数据集...")
X = torch.randn(1000, 3, 256, 256)  # 1000张随机图片
y = torch.randint(0, 2, (1000,))   # 标签

dataset = TensorDataset(X, y)
loader = DataLoader(dataset, batch_size=16)

print("创建模型...")
from collections import OrderedDict

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.fc = nn.Linear(32, 2)
    
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

model = SimpleCNN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

print("开始训练...")
for epoch in range(50):
    total_loss = 0
    for batch_x, batch_y in loader:
        optimizer.zero_grad()
        out = model(batch_x)
        loss = criterion(out, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    if (epoch+1) % 10 == 0:
        print(f"Epoch {epoch+1}/50, Loss: {total_loss:.4f}")

print("训练完成!")
torch.save(model.state_dict(), "model.pth")
print("模型保存到 model.pth")
'''

# 写入文件
with open('train_simple.py', 'w') as f:
    f.write(train_code)

# 运行
!python train_simple.py