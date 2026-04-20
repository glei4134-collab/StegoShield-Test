# 这个文件用于生成图标占位符
# 实际使用时请替换为真实的图标文件

import base64

# 创建一个简单的16x16 PNG图标（紫色方块）
icon_data = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAANklEQVQ4y2P4z8DwHwAMgSz/"
    + "A4wBJP8ZBCj4/x8g+f8/IPn/H0Dy/z9A8v8/QPL/P0Dy/z8AxwMA"
    + "4wEA1c8BEeE9OaEAAAAASUVORK5CYII="
)

with open('desktop/assets/icon.png', 'wb') as f:
    f.write(icon_data)

print("Icon placeholder created")
