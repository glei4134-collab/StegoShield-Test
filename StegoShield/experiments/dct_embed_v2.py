"""
稳定的 DCT 域隐写实现 - PNG 版本
使用奇偶校验方式，更抗噪声
"""

import io
import numpy as np
import cv2
from PIL import Image

END_MARKER = b'###END###'

DCT_POSITIONS = [
    (4, 2), (3, 3), (2, 4),
    (4, 3), (3, 4), (4, 4),
    (5, 1), (1, 5), (5, 2), (2, 5),
]


def _int_to_bin(n: int) -> str:
    return f'{n:08b}'


def _prepare_payload(text: str) -> str:
    data = text.encode('utf-8') + END_MARKER
    return ''.join(_int_to_bin(b) for b in data)


def embed_png_dct_v2(image_path_or_file, secret_text: str) -> bytes:
    """稳定的 DCT 隐写 - 使用奇偶校验方式
    
    原理：不直接修改 LSB，而是让 DCT 系数的奇偶性对应要嵌入的比特
    这样即使系数有 ±1 的变化，奇偶性大概率保持不变
    """
    if isinstance(image_path_or_file, io.BytesIO):
        image_path_or_file.seek(0)
        img = Image.open(image_path_or_file).convert('RGB')
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    elif isinstance(image_path_or_file, Image.Image):
        img = cv2.cvtColor(np.array(image_path_or_file.convert('RGB')), cv2.COLOR_RGB2BGR)
    elif isinstance(image_path_or_file, str):
        img = cv2.imread(image_path_or_file)
    else:
        raise ValueError("Unsupported image type")
    
    if img is None:
        raise ValueError("Cannot read image")
    
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    
    h, w = y.shape
    h = (h // 8) * 8
    w = (w // 8) * 8
    y = y[:h, :w].copy()
    
    payload = _prepare_payload(secret_text)
    payload_len = len(payload)
    
    bit_index = 0
    for row in range(0, h, 8):
        for col in range(0, w, 8):
            if bit_index >= payload_len:
                break
            
            block = y[row:row+8, col:col+8].astype(np.float32) - 128
            dct_block = cv2.dct(block)
            
            target_bit = int(payload[bit_index])
            
            for pos in DCT_POSITIONS:
                if bit_index >= payload_len:
                    break
                
                i, j = pos
                current = int(dct_block[i, j])
                
                # 奇偶校验方式：使系数为偶数(0)或奇数(1)
                current_parity = current & 1
                
                if current_parity != target_bit:
                    # 需要调整：+1 或 -1
                    if current >= 0:
                        dct_block[i, j] = current + 1
                    else:
                        dct_block[i, j] = current - 1
                
                bit_index += 1
            
            idct_block = cv2.idct(dct_block) + 128
            y[row:row+8, col:col+8] = np.clip(idct_block, 0, 255).astype(np.uint8)
        
        if bit_index >= payload_len:
            break
    
    if bit_index < payload_len:
        raise ValueError(f"Image too small: need {payload_len} bits, can embed {bit_index}")
    
    y = np.clip(y, 0, 255).astype(np.uint8)
    ycrcb = cv2.merge([y, cr, cb])
    bgr = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    
    pil_img = Image.fromarray(rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    return buf.getvalue()


def extract_png_dct_v2(image_path_or_file) -> str:
    """稳定的 DCT 提取 - 奇偶校验方式"""
    if isinstance(image_path_or_file, io.BytesIO):
        image_path_or_file.seek(0)
        img = Image.open(image_path_or_file).convert('RGB')
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    elif isinstance(image_path_or_file, Image.Image):
        img = cv2.cvtColor(np.array(image_path_or_file.convert('RGB')), cv2.COLOR_RGB2BGR)
    elif isinstance(image_path_or_file, str):
        img = cv2.imread(image_path_or_file)
    else:
        raise ValueError("Unsupported image type")
    
    if img is None:
        raise ValueError("Cannot read image")
    
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    
    h, w = y.shape
    h = (h // 8) * 8
    w = (w // 8) * 8
    y = y[:h, :w]
    
    bits = []
    for row in range(0, h, 8):
        for col in range(0, w, 8):
            block = y[row:row+8, col:col+8].astype(np.float32) - 128
            dct_block = cv2.dct(block)
            
            for pos in DCT_POSITIONS:
                i, j = pos
                value = int(dct_block[i, j])
                parity = value & 1
                bits.append(str(parity))
    
    bits_str = ''.join(bits)
    
    chars = []
    for i in range(0, len(bits_str) - 7, 8):
        char_bits = bits_str[i:i+8]
        if len(char_bits) == 8:
            chars.append(int(char_bits, 2))
    
    data = bytes(chars)
    pos = data.find(END_MARKER)
    if pos == -1:
        return data.decode('utf-8', errors='replace').rstrip('\x00')
    return data[:pos].decode('utf-8', errors='replace')


if __name__ == '__main__':
    import os
    test_dir = r"c:\Users\17544\.openclaw\workspace\main\StegoShield\test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    test_img = os.path.join(test_dir, "test_v2.png")
    output_img = os.path.join(test_dir, "dct_v2_output.png")
    
    from PIL import Image
    import numpy as np
    
    # 使用固定的测试图像
    img = Image.fromarray(np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8))
    img.save(test_img)
    
    test_msg = "Hello DCT V2!"
    print(f"Testing DCT V2 with message: {test_msg}")
    
    result = embed_png_dct_v2(test_img, test_msg)
    with open(output_img, 'wb') as f:
        f.write(result)
    
    print(f"Saved to {output_img}")
    
    extracted = extract_png_dct_v2(output_img)
    print(f"Extracted: '{extracted}'")
    print(f"Match: {extracted == test_msg}")