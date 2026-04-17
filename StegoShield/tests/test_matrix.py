"""
StegoShield API 测试矩阵

测试覆盖：
1. 嵌入功能（文本/文件 × 加密/不加密）
2. 提取功能（正确密钥/错误密钥/无密钥）
3. 错误处理（无效输入/缺失参数）
4. 端到端流程
"""

import base64
import io
import json
import pytest
import numpy as np
from PIL import Image
import sys
sys.path.insert(0, '..')


@pytest.fixture
def client():
    """使用 Flask test client"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        yield c


def create_test_image(size=(256, 256)):
    """创建测试图片"""
    arr = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def image_to_base64(image_bytes):
    """图片转 base64"""
    return base64.b64encode(image_bytes).decode('utf-8')


class TestEmbed:
    """嵌入功能测试"""

    def test_embed_text_no_encrypt(self, client):
        """测试：嵌入文本（不加密）"""
        image = create_test_image()
        payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {'text': 'Hello World'},
            'encryption': {'enabled': False},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'data' in result
        assert 'image' in result['data']

    def test_embed_text_with_encrypt(self, client):
        """测试：嵌入文本（加密）"""
        image = create_test_image()
        payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {'text': 'Secret Message'},
            'encryption': {'enabled': True},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['data']['encryption']['enabled'] is True
        assert 'key' in result['data']['encryption']

    def test_embed_file_no_encrypt(self, client):
        """测试：嵌入文件（不加密）"""
        image = create_test_image()
        file_content = b'Test file content for steganography'
        file_b64 = base64.b64encode(file_content).decode('utf-8')

        payload = {
            'image': image_to_base64(image),
            'type': 'file',
            'content': {
                'fileName': 'test.txt',
                'fileData': file_b64
            },
            'encryption': {'enabled': False},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True

    def test_embed_file_with_encrypt(self, client):
        """测试：嵌入文件（加密）"""
        image = create_test_image()
        file_content = b'Test file content for steganography'
        file_b64 = base64.b64encode(file_content).decode('utf-8')

        payload = {
            'image': image_to_base64(image),
            'type': 'file',
            'content': {
                'fileName': 'test.pdf',
                'fileData': file_b64
            },
            'encryption': {'enabled': True},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['data']['encryption']['enabled'] is True


class TestExtract:
    """提取功能测试"""

    def test_extract_text_roundtrip(self, client):
        """测试：文本嵌入-提取往返"""
        image = create_test_image()
        original_text = 'Hello World Test'

        embed_payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {'text': original_text},
            'encryption': {'enabled': False},
            'method': 'lsb'
        }

        embed_response = client.post('/api/embed', json=embed_payload)
        embedded_image = embed_response.get_json()['data']['image']

        extract_payload = {
            'image': embedded_image,
            'decryption': {'enabled': False}
        }

        extract_response = client.post('/api/extract', json=extract_payload)
        assert extract_response.status_code == 200
        result = extract_response.get_json()
        assert result['success'] is True
        assert result['data']['type'] == 'text'
        assert result['data']['text'] == original_text

    def test_extract_encrypted_roundtrip(self, client):
        """测试：加密文本嵌入-提取往返"""
        image = create_test_image()
        original_text = 'Secret Message'

        embed_payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {'text': original_text},
            'encryption': {'enabled': True},
            'method': 'lsb'
        }

        embed_response = client.post('/api/embed', json=embed_payload)
        result = embed_response.get_json()
        embedded_image = result['data']['image']
        key = result['data']['encryption']['key']

        extract_payload = {
            'image': embedded_image,
            'decryption': {
                'enabled': True,
                'key': key
            }
        }

        extract_response = client.post('/api/extract', json=extract_payload)
        assert extract_response.status_code == 200
        extract_result = extract_response.get_json()
        assert extract_result['success'] is True
        assert extract_result['data']['text'] == original_text

    def test_extract_wrong_key(self, client):
        """测试：错误密钥提取"""
        image = create_test_image()
        original_text = 'Secret Message'

        embed_payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {'text': original_text},
            'encryption': {'enabled': True},
            'method': 'lsb'
        }

        embed_response = client.post('/api/embed', json=embed_payload)
        embedded_image = embed_response.get_json()['data']['image']

        extract_payload = {
            'image': embedded_image,
            'decryption': {
                'enabled': True,
                'key': 'wrong_key_12345'
            }
        }

        extract_response = client.post('/api/extract', json=extract_payload)
        assert extract_response.status_code == 400
        result = extract_response.get_json()
        assert result['success'] is False
        assert result['error']['code'] == 'DECRYPTION_FAILED'

    def test_extract_file_roundtrip(self, client):
        """测试：文件嵌入-提取往返"""
        image = create_test_image()
        original_content = b'Test file content for steganography'
        file_b64 = base64.b64encode(original_content).decode('utf-8')
        file_name = 'test.txt'

        embed_payload = {
            'image': image_to_base64(image),
            'type': 'file',
            'content': {
                'fileName': file_name,
                'fileData': file_b64
            },
            'encryption': {'enabled': False},
            'method': 'lsb'
        }

        embed_response = client.post('/api/embed', json=embed_payload)
        embedded_image = embed_response.get_json()['data']['image']

        extract_payload = {
            'image': embedded_image,
            'decryption': {'enabled': False}
        }

        extract_response = client.post('/api/extract', json=extract_payload)
        result = extract_response.get_json()
        assert result['success'] is True
        assert result['data']['type'] == 'file'
        assert result['data']['fileName'] == file_name
        extracted_data = base64.b64decode(result['data']['fileData'])
        assert extracted_data == original_content


class TestErrorHandling:
    """错误处理测试"""

    def test_missing_image(self, client):
        """测试：缺少图片"""
        payload = {
            'type': 'text',
            'content': {'text': 'test'},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert result['error']['code'] == 'MISSING_IMAGE'

    def test_missing_content(self, client):
        """测试：缺少内容"""
        image = create_test_image()
        payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_INPUT'

    def test_invalid_base64(self, client):
        """测试：无效的 Base64"""
        payload = {
            'image': 'invalid_base64!!!',
            'type': 'text',
            'content': {'text': 'test'},
            'method': 'lsb'
        }

        response = client.post('/api/embed', json=payload)
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_BASE64'

    def test_extract_missing_image(self, client):
        """测试：提取缺少图片"""
        payload = {
            'decryption': {'enabled': False}
        }

        response = client.post('/api/extract', json=payload)
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert result['error']['code'] == 'MISSING_IMAGE'

    def test_decrypt_without_key(self, client):
        """测试：启用解密但未提供密钥"""
        image = create_test_image()

        embed_payload = {
            'image': image_to_base64(image),
            'type': 'text',
            'content': {'text': 'test'},
            'encryption': {'enabled': True},
            'method': 'lsb'
        }

        embed_response = client.post('/api/embed', json=embed_payload)
        embedded_image = embed_response.get_json()['data']['image']

        extract_payload = {
            'image': embedded_image,
            'decryption': {'enabled': True}
        }

        response = client.post('/api/extract', json=extract_payload)
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert result['error']['code'] == 'INVALID_INPUT'


class TestHealthCheck:
    """健康检查测试"""

    def test_health(self, client):
        """测试：健康检查接口"""
        response = client.get('/api/health')
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['data']['status'] == 'ok'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
