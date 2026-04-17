"""测试解密相关错误"""
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


def test_decrypt_with_correct_key(client):
    """测试：用正确密钥提取"""
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
        'content': {'text': '这是秘密信息'},
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
    result = extract_response.get_json()

    assert extract_response.status_code == 200
    assert result['success'] is True
    assert result['data']['text'] == '这是秘密信息'
    print("✓ 正确密钥提取成功")


def test_decrypt_with_wrong_key(client):
    """测试：用错误密钥提取"""
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
        'content': {'text': '这是秘密信息'},
        'encryption': {'enabled': True},
        'method': 'lsb'
    }

    embed_response = client.post('/api/embed', json=embed_data)
    embed_result = embed_response.get_json()
    embedded_image = embed_result['data']['image']

    extract_data = {
        'image': embedded_image,
        'decryption': {'enabled': True, 'key': 'wrong_key_12345'}
    }

    extract_response = client.post('/api/extract', json=extract_data)
    result = extract_response.get_json()

    assert extract_response.status_code == 400
    assert result['success'] is False
    assert result['error']['code'] == 'DECRYPTION_FAILED'
    assert result['error']['message'] == '解密失败，密钥可能错误或数据已损坏'
    print("✓ 错误密钥返回 DECRYPTION_FAILED")


def test_decrypt_without_key(client):
    """测试：启用解密但不提供密钥"""
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
        'content': {'text': '这是秘密信息'},
        'encryption': {'enabled': True},
        'method': 'lsb'
    }

    embed_response = client.post('/api/embed', json=embed_data)
    embed_result = embed_response.get_json()
    embedded_image = embed_result['data']['image']

    extract_data = {
        'image': embedded_image,
        'decryption': {'enabled': True}
    }

    extract_response = client.post('/api/extract', json=extract_data)
    result = extract_response.get_json()

    assert extract_response.status_code == 400
    assert result['success'] is False
    assert result['error']['code'] == 'INVALID_INPUT'
    assert result['error']['message'] == '启用解密时必须提供密钥'
    print("✓ 缺少密钥返回 INVALID_INPUT")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
