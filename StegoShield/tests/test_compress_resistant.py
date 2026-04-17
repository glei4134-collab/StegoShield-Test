"""测试压缩抗性功能"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def client():
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        yield c


def test_embed_with_compress_resistant(client):
    """测试：启用抗压缩嵌入"""
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
        'content': {'text': '测试抗压缩消息'},
        'encryption': {'enabled': False},
        'method': 'lsb',
        'compressResistant': True
    }

    response = client.post('/api/embed', json=embed_data)
    result = response.get_json()

    assert response.status_code == 200
    assert result['success'] is True
    assert result['data']['compressResistant'] is True
    print("✓ 抗压缩嵌入成功")


def test_compress_resistant_roundtrip(client):
    """测试：抗压缩往返"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    text = '这是抗压缩测试消息'

    embed_data = {
        'image': image_b64,
        'type': 'text',
        'content': {'text': text},
        'encryption': {'enabled': False},
        'method': 'lsb',
        'compressResistant': True
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
    assert extract_result['data']['text'] == text
    print("✓ 抗压缩往返成功")


def test_compress_resistant_with_encryption(client):
    """测试：抗压缩 + 加密往返"""
    import base64
    import io
    from PIL import Image
    import numpy as np

    arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    text = '加密抗压缩消息'

    embed_data = {
        'image': image_b64,
        'type': 'text',
        'content': {'text': text},
        'encryption': {'enabled': True},
        'method': 'lsb',
        'compressResistant': True
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
    assert extract_result['data']['text'] == text
    print("✓ 抗压缩 + 加密往返成功")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])