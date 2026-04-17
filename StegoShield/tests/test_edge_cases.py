"""边界情况测试"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def client():
    """使用 Flask test client"""
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        yield c


def test_no_hidden_data(client):
    """测试：普通图片（无隐藏数据）提取"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    extract_data = {
        'image': image_b64,
        'decryption': {'enabled': False}
    }

    response = client.post('/api/extract', json=extract_data)
    result = response.get_json()

    assert response.status_code == 404
    assert result['success'] is False
    assert result['error']['code'] == 'NO_HIDDEN_DATA'
    print("✓ 无隐藏数据返回 NO_HIDDEN_DATA")


def test_content_with_end_marker(client):
    """测试：内容包含 ###END### 不会被截断"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    text_with_marker = "测试###END###内容"

    embed_data = {
        'image': image_b64,
        'type': 'text',
        'content': {'text': text_with_marker},
        'encryption': {'enabled': False},
        'method': 'lsb'
    }

    embed_response = client.post('/api/embed', json=embed_data)
    embed_result = embed_response.get_json()
    embedded_image = embed_result['data']['image']

    extract_data = {
        'image': embedded_image,
        'decryption': {'enabled': False}
    }

    extract_response = client.post('/api/extract', json=extract_data)
    extract_result = extract_response.get_json()

    assert extract_response.status_code == 200
    assert extract_result['success'] is True
    assert extract_result['data']['text'] == text_with_marker
    print("✓ 包含 ###END### 的内容不会被截断")


def test_empty_text(client):
    """测试：空文本（应该失败）"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    embed_data = {
        'image': image_b64,
        'type': 'text',
        'content': {'text': ''},
        'encryption': {'enabled': False},
        'method': 'lsb'
    }

    response = client.post('/api/embed', json=embed_data)
    result = response.get_json()

    assert response.status_code == 400
    assert result['success'] is False
    assert result['error']['code'] == 'INVALID_INPUT'
    print("✓ 空文本返回 INVALID_INPUT")


def test_large_text_in_small_image(client):
    """测试：小图片嵌入大文本"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    large_text = "x" * 100000

    embed_data = {
        'image': image_b64,
        'type': 'text',
        'content': {'text': large_text},
        'encryption': {'enabled': False},
        'method': 'lsb'
    }

    response = client.post('/api/embed', json=embed_data)
    result = response.get_json()

    assert response.status_code == 400
    assert result['success'] is False
    assert result['error']['code'] == 'PAYLOAD_TOO_LARGE'
    print("✓ 大文本返回 PAYLOAD_TOO_LARGE")


def test_file_roundtrip(client):
    """测试：文件嵌入提取往返"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    file_content = b'Hello, this is a test file content!'
    file_b64 = base64.b64encode(file_content).decode('utf-8')

    embed_data = {
        'image': image_b64,
        'type': 'file',
        'content': {
            'fileName': 'test.txt',
            'fileData': file_b64
        },
        'encryption': {'enabled': False},
        'method': 'lsb'
    }

    embed_response = client.post('/api/embed', json=embed_data)
    embed_result = embed_response.get_json()
    embedded_image = embed_result['data']['image']

    extract_data = {
        'image': embedded_image,
        'decryption': {'enabled': False}
    }

    extract_response = client.post('/api/extract', json=extract_data)
    extract_result = extract_response.get_json()

    assert extract_response.status_code == 200
    assert extract_result['success'] is True
    assert extract_result['data']['type'] == 'file'
    assert extract_result['data']['fileName'] == 'test.txt'
    extracted_content = base64.b64decode(extract_result['data']['fileData'])
    assert extracted_content == file_content
    print("✓ 文件嵌入提取往返成功")


def test_encrypted_file_roundtrip(client):
    """测试：加密文件嵌入提取往返"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    file_content = b'Encrypted file content!'
    file_b64 = base64.b64encode(file_content).decode('utf-8')

    embed_data = {
        'image': image_b64,
        'type': 'file',
        'content': {
            'fileName': 'secret.pdf',
            'fileData': file_b64
        },
        'encryption': {'enabled': True},
        'method': 'lsb'
    }

    embed_response = client.post('/api/embed', json=embed_data)
    embed_result = embed_response.get_json()
    embedded_image = embed_result['data']['image']
    key = embed_result['data']['encryption']['key']

    extract_data = {
        'image': embedded_image,
        'decryption': {'enabled': True, 'key': key}
    }

    extract_response = client.post('/api/extract', json=extract_data)
    extract_result = extract_response.get_json()

    assert extract_response.status_code == 200
    assert extract_result['success'] is True
    assert extract_result['data']['type'] == 'file'
    assert extract_result['data']['fileName'] == 'secret.pdf'
    extracted_content = base64.b64decode(extract_result['data']['fileData'])
    assert extracted_content == file_content
    print("✓ 加密文件嵌入提取往返成功")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
