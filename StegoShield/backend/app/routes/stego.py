"""
Steganography routes: embed and extract text in images.
支持可选的 AES-256 加密功能。

API 契约版本: v2
"""

import os
import base64
import tempfile
from flask import Blueprint, request

from app.services import enhanced_stego
from app.services import encryption
from app.services import redundancy
from app.services import dct_stego
from app.errors import (
    StegoError, InvalidInputError, MissingImageError, MissingContentError,
    InvalidBase64Error, EncryptionError, DecryptionError, ExtractionError,
    InternalError, PayloadTooLargeError, NoHiddenDataError, EmbedError
)
from app.response import success_response, error_response, handle_exception
from app.payload import prepare_payload, parse_payload

stego_bp = Blueprint('stego', __name__)

MAX_IMAGE_SIZE = 100 * 1024 * 1024
SUPPORTED_METHODS = ['lsb', 'dct']


@stego_bp.route('/api/embed', methods=['POST'])
def embed():
    """
    嵌入数据到图片

    请求格式 (v2):
    {
        "image": "base64编码的图片（必需）",
        "type": "text | file",
        "content": {
            "text": "要嵌入的文本（type=text时必需）",
            "fileName": "文件名（type=file时必需）",
            "fileData": "文件的base64编码（type=file时必需）"
        },
        "encryption": {
            "enabled": false,
            "key": "加密密钥（可选）"
        },
        "method": "lsb"
    }

    响应格式 (v2):
    {
        "success": true,
        "data": {
            "image": "base64编码的结果图片"
        },
        "message": "数据嵌入成功"
    }
    """
    try:
        data = request.get_json()
        if not data:
            raise InvalidInputError('未提供 JSON 数据')

        image_b64 = data.get('image', '')
        if not image_b64:
            raise MissingImageError()

        payload_type = data.get('type', 'text')
        content = data.get('content', {})

        encryption_config = data.get('encryption', {})
        use_encryption = encryption_config.get('enabled', False)
        encryption_key = encryption_config.get('key', None)

        compress_resistant = data.get('compressResistant', False)

        method = data.get('method', 'lsb')
        if method not in SUPPORTED_METHODS:
            raise InvalidInputError(f'不支持的方法: {method}，仅支持: {SUPPORTED_METHODS}')

        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception:
            raise InvalidBase64Error('图片 Base64 编码无效')

        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise InvalidInputError(f'图片过大，最大支持 {MAX_IMAGE_SIZE // (1024*1024)}MB')

        payload = prepare_payload(payload_type, content, encrypted=use_encryption)

        if use_encryption:
            try:
                payload, key = encryption.encrypt_bytes(payload, encryption_key)
                result_key = key.hex() if isinstance(key, bytes) else key
            except Exception as e:
                raise EncryptionError('加密失败')
        else:
            result_key = None

        if compress_resistant:
            payload = redundancy.encode_with_redundancy(payload)

        if method == 'dct':
            try:
                result_bytes = dct_stego.embed_with_length_prefix(image_bytes, payload, quality=75)
                result_b64 = base64.b64encode(result_bytes).decode('utf-8')
                response_data = {
                    'image': result_b64,
                    'mimeType': 'image/jpeg'
                }
            except Exception as e:
                if 'too large' in str(e).lower() or 'capacity' in str(e).lower():
                    raise PayloadTooLargeError('数据太大，超出图片容量')
                raise EmbedError('嵌入失败')
        else:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
                tmp_in.write(image_bytes)
                tmp_in_path = tmp_in.name

            try:
                result_bytes = enhanced_stego.embed_enhanced(tmp_in_path, secret_bytes=payload)
            except ValueError as e:
                error_msg = str(e)
                if 'bits' in error_msg:
                    import re
                    match = re.search(r'(\d+) bits.*?(\d+) bits', error_msg)
                    if match:
                        needed = int(match.group(1)) // 8
                        max_cap = int(match.group(2)) // 8
                        raise PayloadTooLargeError(f'数据太大: 需要约 {needed} 字节，图片容量约 {max_cap} 字节。请使用更大的图片或减少内容。')
                raise PayloadTooLargeError('数据太大，超出图片容量')
            except Exception as e:
                import traceback
                print(f"Embed error: {type(e).__name__}: {e}")
                traceback.print_exc()
                raise EmbedError(f'嵌入失败: {type(e).__name__}')
            finally:
                os.unlink(tmp_in_path)

            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            response_data = {
                'image': result_b64
            }

        if result_key:
            response_data['encryption'] = {
                'enabled': True,
                'key': result_key
            }

        if compress_resistant:
            response_data['compressResistant'] = True

        return success_response(response_data, '数据嵌入成功')

    except StegoError as e:
        return error_response(e.code, e.message, e.status_code)
    except Exception as e:
        return handle_exception(e)


@stego_bp.route('/api/extract', methods=['POST'])
def extract():
    """
    从图片提取数据

    请求格式 (v2):
    {
        "image": "base64编码的图片（必需）",
        "decryption": {
            "enabled": false,
            "key": "解密密钥（启用解密时必需）"
        }
    }

    响应格式 (v2):
    文本:
    {
        "success": true,
        "data": {
            "type": "text",
            "text": "提取的文本内容"
        }
    }

    文件:
    {
        "success": true,
        "data": {
            "type": "file",
            "fileName": "document.pdf",
            "fileData": "JVBERi0xLjQK...",
            "mimeType": "application/pdf"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            raise InvalidInputError('未提供 JSON 数据')

        image_b64 = data.get('image', '')
        if not image_b64:
            raise MissingImageError()

        decryption_config = data.get('decryption', {})
        use_decryption = decryption_config.get('enabled', False)
        decryption_key = decryption_config.get('key', None)

        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception:
            raise InvalidBase64Error('图片 Base64 编码无效')

        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise InvalidInputError(f'图片过大，最大支持 {MAX_IMAGE_SIZE // (1024*1024)}MB')

        payload = None

        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
                tmp_in.write(image_bytes)
                tmp_in_path = tmp_in.name

            try:
                payload = enhanced_stego.extract_enhanced(tmp_in_path)
            except ValueError as e:
                pass
            finally:
                os.unlink(tmp_in_path)
        except Exception:
            pass

        if payload is None:
            try:
                payload = dct_stego.extract_with_length_prefix(image_bytes)
            except Exception:
                pass

        if payload is None or len(payload) < 16:
            raise NoHiddenDataError('图片中无隐藏数据')

        payload = bytes(payload)

        # 抗压缩数据冗余编码检测
        # 尝试用冗余解码器解码，解码成功会有 CRC 校验
        if len(payload) > 50:
            try:
                decoded_payload, is_valid = redundancy.decode_with_redundancy(payload)
                if is_valid and len(decoded_payload) >= 16:
                    payload = decoded_payload
            except Exception:
                pass

        if use_decryption:
            if not decryption_key:
                raise InvalidInputError('启用解密时必须提供密钥')

            try:
                key_bytes = bytes.fromhex(decryption_key)
                payload = encryption.decrypt_bytes(payload, key_bytes)
            except ValueError as e:
                raise DecryptionError('解密失败，密钥可能错误或数据已损坏')
            except Exception as e:
                raise DecryptionError('解密失败，密钥可能错误或数据已损坏')

        result = parse_payload(payload)

        return success_response(result)

    except StegoError as e:
        return error_response(e.code, e.message, e.status_code)
    except Exception as e:
        return handle_exception(e)


@stego_bp.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    return success_response({'status': 'ok'}, '服务正常')
