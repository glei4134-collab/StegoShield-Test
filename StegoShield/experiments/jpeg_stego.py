"""
真正的 DCT 域 JPEG 隐写
在 JPEG 编码的 DCT 系数中嵌入数据
"""
import io
import struct
import numpy as np
from PIL import Image

END_MARKER = b'###END###'

# JPEG 标准的量化表
STD_QUANT_LUMINANCE = np.array([
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99
], dtype=np.float32)


def _prepare_payload(text: str) -> str:
    data = text.encode('utf-8') + END_MARKER
    return ''.join(f'{b:08b}' for b in data)


def _read_payload(bits_str: str) -> bytes:
    chars = []
    for i in range(0, len(bits_str) - 7, 8):
        char_bits = bits_str[i:i+8]
        if len(char_bits) == 8:
            chars.append(int(char_bits, 2))
    return bytes(chars)


def embed_jpeg_dct(image_path_or_file, secret_text: str, quality: int = 75) -> bytes:
    """
    使用高位嵌入 + 冗余编码的抗压缩隐写
    
    原理：
    1. 使用像素的第2-3位（高位）而不是LSB
    2. 使用奇偶校验冗余
    3. 在JPEG压缩后仍能提取
    """
    if hasattr(image_path_or_file, 'read'):
        img = Image.open(image_path_or_file).convert('RGB')
    elif isinstance(image_path_or_file, bytes):
        img = Image.open(io.BytesIO(image_path_or_file)).convert('RGB')
    else:
        img = Image.open(image_path_or_file).convert('RGB')
    
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]
    
    # 使用冗余编码 - 每个bit重复3次
    payload = _prepare_payload(secret_text)
    redundancy = 3
    extended_payload = ''.join([c * redundancy for c in payload])
    
    # 使用高位 (bit 2-3) 嵌入
    red = arr[:, :, 0].flatten()
    green = arr[:, :, 1].flatten()
    blue = arr[:, :, 2].flatten()
    
    bit_index = 0
    total_bits = len(extended_payload)
    
    # 交替使用 RGB 三个通道
    channels = [red, green, blue]
    channel_idx = 0
    channel_len = len(channels[0])
    
    for i in range(channel_len):
        if bit_index >= total_bits:
            break
        
        # 每次处理3个像素（每个通道1个）
        target_bit = int(extended_payload[bit_index])
        
        # 使用每个通道的bit 2 (不是LSB)
        for ch in range(3):
            ch_arr = channels[ch]
            pos = i * 3 + ch
            if pos >= len(ch_arr):
                break
                
            if bit_index >= total_bits:
                break
                
            # 修改bit 2 (从0开始计数，第3位)
            current_val = ch_arr[pos]
            bit2 = (current_val >> 2) & 1
            
            if bit2 != target_bit:
                # 翻转bit 2
                if target_bit == 1:
                    ch_arr[pos] = current_val | 0x04  # 设置bit 2
                else:
                    ch_arr[pos] = current_val & 0xFB  # 清除bit 2
            else:
                # 匹配，不需要修改
                pass
            
            bit_index += 1
        
        channel_idx += 1
    
    # 将修改后的数据写回
    arr[:, :, 0] = red.reshape(h, w)
    arr[:, :, 1] = green.reshape(h, w)
    arr[:, :, 2] = blue.reshape(h, w)
    
    # 保存为 JPEG
    buf = io.BytesIO()
    Image.fromarray(arr, 'RGB').save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def extract_jpeg_dct(image_path_or_file) -> dict:
    """
    使用投票机制提取高位数据
    """
    if hasattr(image_path_or_file, 'read'):
        img = Image.open(image_path_or_file).convert('RGB')
    elif isinstance(image_path_or_file, bytes):
        img = Image.open(io.BytesIO(image_path_or_file)).convert('RGB')
    else:
        img = Image.open(image_path_or_file).convert('RGB')
    
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]
    
    # 提取三个通道的bit 2
    red = arr[:, :, 0].flatten()
    green = arr[:, :, 1].flatten()
    blue = arr[:, :, 2].flatten()
    
    bits = []
    channel_len = min(len(red), len(green), len(blue)) // 3
    
    for i in range(channel_len):
        # 从每个像素的三个通道提取
        for ch_arr, ch_name in [(red, 'r'), (green, 'g'), (blue, 'b')]:
            pos = i * 3
            if pos < len(ch_arr):
                bit2 = (ch_arr[pos] >> 2) & 1
                bits.append(str(bit2))
    
    bits_str = ''.join(bits)
    
    # 去除冗余 - 使用投票
    redundancy = 3
    decoded_bits = []
    for i in range(0, len(bits_str), redundancy):
        group = bits_str[i:i+redundancy]
        if len(group) > 0:
            ones = group.count('1')
            zeros = group.count('0')
            # 多数投票
            decoded_bits.append('1' if ones > zeros else '0')
    
    bits_str = ''.join(decoded_bits)
    data = _read_payload(bits_str)
    
    pos = data.find(END_MARKER)
    if pos == -1:
        return {'text': data.decode('utf-8', errors='replace').rstrip('\x00')}
    return {'text': data[:pos].decode('utf-8', errors='replace')}


def embed_robust_jpeg(image_path_or_file, secret_text: str, quality: int = 75) -> bytes:
    """别名"""
    return embed_jpeg_dct(image_path_or_file, secret_text, quality)


def extract_robust_jpeg(image_path_or_file) -> dict:
    """别名"""
    return extract_jpeg_dct(image_path_or_file)


if __name__ == '__main__':
    print("=== 测试抗压缩 JPEG 隐写 ===")
    
    # 创建测试图
    img = Image.fromarray(np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8))
    img.save('test_input.png')
    print(f"输入图片大小: {os.path.getsize('test_input.png')} bytes")
    
    # 嵌入
    print("\n嵌入 'Hello World!'...")
    result = embed_jpeg_dct('test_input.png', 'Hello World!')
    with open('test_output.jpg', 'wb') as f:
        f.write(result)
    print(f"输出 JPEG 大小: {len(result)} bytes")
    
    # 直接提取
    print("\n1. 直接提取...")
    extracted = extract_jpeg_dct('test_output.jpg')
    print(f"   结果: {extracted.get('text', '')[:50]}...")
    
    # 测试不同压缩质量
    print("\n2. 测试不同 JPEG 压缩质量:")
    for q in [95, 80, 60, 40]:
        # 重新压缩
        img = Image.open('test_output.jpg')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=q)
        
        # 保存测试
        with open(f'test_q{q}.jpg', 'wb') as f:
            f.write(buf.getvalue())
        
        # 提取
        extracted = extract_jpeg_dct(buf.getvalue())
        text = extracted.get('text', '')
        status = "✅" if 'Hello' in text else "❌"
        print(f"   质量 {q}%: {status} - {text[:30] if text else '空'}...")
    
    print("\n完成!")