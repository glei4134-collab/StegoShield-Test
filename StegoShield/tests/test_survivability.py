"""测试抗社交平台压缩 survivability"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import base64
import io
import zlib
from PIL import Image
import numpy as np
from app import create_app
from app.services import enhanced_stego, redundancy


def create_test_image(width=512, height=512):
    """创建测试图片"""
    arr = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def simulate_wechat_compression(image_bytes, quality=85):
    """模拟微信图片压缩"""
    img = Image.open(io.BytesIO(image_bytes))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    jpeg_data = buf.getvalue()
    
    img2 = Image.open(io.BytesIO(jpeg_data))
    buf2 = io.BytesIO()
    img2.save(buf2, format='PNG')
    return buf2.getvalue()


def simulate_screenshot_save(image_bytes):
    """模拟截图保存（轻微 PNG 压缩）"""
    img = Image.open(io.BytesIO(image_bytes))
    buf = io.BytesIO()
    img.save(buf, format='PNG', compress_level=6)
    return buf.getvalue()


def test_compress_roundtrip(text, compress_resistant=True):
    """测试压缩往返"""
    app = create_app()
    
    # Embed
    image_bytes = create_test_image(512, 512)
    payload = base64.b64encode(image_bytes).decode('utf-8')
    
    with app.test_client() as client:
        embed_data = {
            'image': payload,
            'type': 'text',
            'content': {'text': text},
            'encryption': {'enabled': False},
            'method': 'lsb',
            'compressResistant': compress_resistant
        }
        
        embed_response = client.post('/api/embed', json=embed_data)
        embed_result = embed_response.get_json()
        
        if not embed_result.get('success'):
            print(f"  嵌入失败: {embed_result.get('error')}")
            return False
            
        embedded_image_b64 = embed_result['data']['image']
        embedded_image = base64.b64decode(embedded_image_b64)
        
        # Apply compression
        compressed_image = simulate_wechat_compression(embedded_image)
        
        # Extract
        extract_data = {
            'image': base64.b64encode(compressed_image).decode('utf-8'),
            'decryption': {'enabled': False}
        }
        
        extract_response = client.post('/api/extract', json=extract_data)
        extract_result = extract_response.get_json()
        
        if extract_result.get('success'):
            extracted_text = extract_result['data'].get('text', '')
            if extracted_text == text:
                return True
            else:
                print(f"  内容不匹配: '{extracted_text}' != '{text}'")
                return False
        else:
            print(f"  提取失败: {extract_result.get('error', {}).get('message')}")
            return False


def test_screenshot_roundtrip(text, compress_resistant=True, times=5):
    """测试截图保存多次往返"""
    app = create_app()
    
    image_bytes = create_test_image(512, 512)
    payload = base64.b64encode(image_bytes).decode('utf-8')
    
    with app.test_client() as client:
        embed_data = {
            'image': payload,
            'type': 'text',
            'content': {'text': text},
            'encryption': {'enabled': False},
            'method': 'lsb',
            'compressResistant': compress_resistant
        }
        
        embed_response = client.post('/api/embed', json=embed_data)
        embed_result = embed_response.get_json()
        
        if not embed_result.get('success'):
            print(f"  嵌入失败: {embed_result.get('error')}")
            return False
            
        embedded_image_b64 = embed_result['data']['image']
        image = base64.b64decode(embedded_image_b64)
        
        # 多次截图保存
        for i in range(times):
            image = simulate_screenshot_save(image)
            
        # Extract
        extract_data = {
            'image': base64.b64encode(image).decode('utf-8'),
            'decryption': {'enabled': False}
        }
        
        extract_response = client.post('/api/extract', json=extract_data)
        extract_result = extract_response.get_json()
        
        if extract_result.get('success'):
            extracted_text = extract_result['data'].get('text', '')
            if extracted_text == text:
                return True
            else:
                print(f"  第{times}次后内容不匹配")
                return False
        else:
            print(f"  第{times}次后提取失败")
            return False


if __name__ == '__main__':
    test_text = "这是一条测试消息 StegoShield"
    
    print("=" * 60)
    print("测试 1: 抗压缩功能 (微信风格 JPEG 压缩)")
    print("=" * 60)
    
    print("\n[不启用抗压缩]")
    result = test_compress_roundtrip(test_text, compress_resistant=False)
    print(f"  结果: {'✅ 通过' if result else '❌ 失败'}")
    
    print("\n[启用抗压缩]")
    result = test_compress_roundtrip(test_text, compress_resistant=True)
    print(f"  结果: {'✅ 通过' if result else '❌ 失败'}")
    
    print("\n" + "=" * 60)
    print("测试 2: 截图保存多次")
    print("=" * 60)
    
    print("\n[不启用抗压缩 - 5次截图]")
    result = test_screenshot_roundtrip(test_text, compress_resistant=False, times=5)
    print(f"  结果: {'✅ 通过' if result else '❌ 失败'}")
    
    print("\n[启用抗压缩 - 5次截图]")
    result = test_screenshot_roundtrip(test_text, compress_resistant=True, times=5)
    print(f"  结果: {'✅ 通过' if result else '❌ 失败'}")
    
    print("\n[启用抗压缩 - 10次截图]")
    result = test_screenshot_roundtrip(test_text, compress_resistant=True, times=10)
    print(f"  结果: {'✅ 通过' if result else '❌ 失败'}")