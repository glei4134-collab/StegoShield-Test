"""极限文本和压缩测试 v2"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import base64
import io
from PIL import Image
import numpy as np
from app import create_app


def create_test_image(size=(512, 512)):
    arr = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def test_extreme_text():
    """测试极限文本大小 (无压缩)"""
    print("=" * 60)
    print("极限测试: 最大文本容量 (无抗压缩)")
    print("=" * 60)
    
    arr = np.random.randint(0, 255, (2048, 2048, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    image_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    capacity = 2048 * 2048 * 3 // 8
    print(f"图片容量: {capacity/1024:.0f}KB")
    
    text_sizes = [
        ("100KB", 100 * 1024),
        ("200KB", 200 * 1024),
        ("300KB", 300 * 1024),
        ("400KB", 400 * 1024),
        ("500KB", 500 * 1024),
        ("600KB", 600 * 1024),
    ]
    
    app = create_app()
    
    for name, size in text_sizes:
        content = "A" * size
        print(f"\nTesting {name} text...")
        
        with app.test_client() as client:
            resp = client.post('/api/embed', json={
                'image': image_b64,
                'type': 'text',
                'content': {'text': content},
                'method': 'lsb',
                'compressResistant': False
            })
            
            if resp.status_code == 200:
                print(f"  ✅ OK")
            else:
                result = resp.get_json()
                print(f"  ❌ {result.get('error', {}).get('code')}")


def test_text_with_compression():
    """测试带压缩的文本容量"""
    print("\n" + "=" * 60)
    print("极限测试: 带抗压缩的文本容量")
    print("=" * 60)
    
    arr = np.random.randint(0, 255, (2048, 2048, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    image_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # 抗压缩会占用约 3 倍空间
    text_sizes = [
        ("50KB", 50 * 1024),
        ("100KB", 100 * 1024),
        ("150KB", 150 * 1024),
        ("200KB", 200 * 1024),
    ]
    
    app = create_app()
    
    for name, size in text_sizes:
        content = "A" * size
        print(f"\nTesting {name} text with compression...")
        
        with app.test_client() as client:
            resp = client.post('/api/embed', json={
                'image': image_b64,
                'type': 'text',
                'content': {'text': content},
                'method': 'lsb',
                'compressResistant': True
            })
            
            if resp.status_code == 200:
                print(f"  ✅ OK")
            else:
                result = resp.get_json()
                print(f"  ❌ {result.get('error', {}).get('code')}")


def test_extreme_compression():
    """测试极限压缩次数 (小文本)"""
    print("\n" + "=" * 60)
    print("极限测试: 最大压缩次数")
    print("=" * 60)
    
    content = "StegoShield 极限抗压测试数据" * 1000  # ~40KB
    
    arr = np.random.randint(0, 255, (2048, 2048, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    image_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    app = create_app()
    
    with app.test_client() as client:
        print(f"\n嵌入 {len(content)} bytes 文本...")
        resp = client.post('/api/embed', json={
            'image': image_b64,
            'type': 'text',
            'content': {'text': content},
            'method': 'lsb',
            'compressResistant': True
        })
        
        if not resp.get_json().get('success'):
            print(f"嵌入失败!")
            return
        
        embedded_b64 = resp.get_json()['data']['image']
        embedded_bytes = base64.b64decode(embedded_b64)
        
        print(f"压缩测试 (300+ 次)...")
        success_count = 0
        max_test = 300
        
        for i in range(1, max_test + 1):
            img = Image.open(io.BytesIO(embedded_bytes))
            buf = io.BytesIO()
            img.save(buf, format='PNG', compress_level=9)
            compressed = buf.getvalue()
            
            extract_resp = client.post('/api/extract', json={
                'image': base64.b64encode(compressed).decode('utf-8'),
                'decryption': {'enabled': False}
            })
            
            result = extract_resp.get_json()
            if result.get('success'):
                extracted = result['data'].get('text', '')
                if extracted == content:
                    success_count += 1
                    if i <= 10 or i % 50 == 0 or i == max_test:
                        print(f"  {i} 次: ✅")
                else:
                    print(f"  {i} 次: ❌ 内容损坏")
                    break
            else:
                print(f"  {i} 次: ❌")
                break
        
        print(f"\n极限结果: {success_count}/{max_test} 次")


if __name__ == '__main__':
    test_extreme_text()
    test_text_with_compression()
    test_extreme_compression()
    print("\n测试完成!")