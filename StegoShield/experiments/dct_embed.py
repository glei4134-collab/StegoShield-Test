"""
DCT 域隐写实现
基于 DCT 变换，在图像频域中嵌入秘密信息
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
    (5, 3), (3, 5), (4, 5), (5, 4),
    (6, 1), (1, 6), (6, 2), (2, 6),
]


def _int_to_bin(n: int) -> str:
    return f'{n:08b}'


def _bin_to_int(bin_str: str) -> int:
    return int(bin_str, 2)


def _prepare_payload(text: str) -> str:
    data = text.encode('utf-8') + END_MARKER
    return ''.join(_int_to_bin(b) for b in data)


def embed_png_dct(image_path_or_file, secret_text: str) -> bytes:
    """在 PNG 图像的 DCT 系数中嵌入秘密信息"""
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
            
            for pos in DCT_POSITIONS:
                if bit_index >= payload_len:
                    break
                
                i, j = pos
                original = int(dct_block[i, j])
                original_bin = f'{original:011b}'
                new_bin = original_bin[:-1] + payload[bit_index]
                dct_block[i, j] = int(new_bin, 2)
                
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


def extract_png_dct(image_path_or_file) -> str:
    """从 PNG 图像提取 DCT 隐写数据"""
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
                lsb = value & 1
                bits.append(str(lsb))
    
    bits_str = ''.join(bits)
    
    chars = []
    for i in range(0, len(bits_str) - 7, 8):
        char_bits = bits_str[i:i+8]
        if len(char_bits) == 8:
            chars.append(_bin_to_int(char_bits))
    
    data = bytes(chars)
    pos = data.find(END_MARKER)
    if pos == -1:
        return data.decode('utf-8', errors='replace').rstrip('\x00')
    return data[:pos].decode('utf-8', errors='replace')


if __name__ == '__main__':
    import os
    
    test_dir = r"c:\Users\17544\.openclaw\workspace\main\StegoShield\test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    test_img = os.path.join(test_dir, "test.png")
    output_img = os.path.join(test_dir, "dct_output.png")
    
    from PIL import Image
    import numpy as np
    
    img = Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8))
    img.save(test_img)
    
    print(f"Testing DCT embedding...")
    result = embed_png_dct(test_img, "Hello DCT!")
    
    with open(output_img, 'wb') as f:
        f.write(result)
    
    print(f"Saved to {output_img}")
    
    extracted = extract_png_dct(output_img)
    print(f"Extracted: '{extracted}'")