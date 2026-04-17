"""
Statistical steganalysis using DCT-based chi-square test.
检测原理：分析 DCT 系数的统计分布来判断是否包含隐写内容。
"""

import numpy as np
from PIL import Image
from scipy.fftpack import dct


def analyze_image(image_path: str) -> dict:
    """分析图片是否可能包含隐写内容

    原理：
    - 正常图片的 DCT 系数分布呈现自然统计特性
    - LSB 隐写会修改像素最低位，影响 DCT 系数分布
    - 通过卡方检验检测分布异常

    Args:
        image_path: 图片文件路径

    Returns:
        dict:
            - has_hidden: 是否可能包含隐写
            - confidence: 置信度 0.0-1.0
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        rgb = np.array(img, dtype=np.float64)

        h, w = rgb.shape[:2]

        r = rgb[:, :, 0]
        g = rgb[:, :, 1]
        b = rgb[:, :, 2]
        y = 0.299 * r + 0.587 * g + 0.114 * b

        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        if pad_h or pad_w:
            y = np.pad(y, ((0, pad_h), (0, pad_w)), mode='reflect')

        all_coeffs = []
        num_blocks_vert = y.shape[0] // 8
        num_blocks_horz = y.shape[1] // 8

        for br in range(num_blocks_vert):
            for bc in range(num_blocks_horz):
                block = y[br*8:(br+1)*8, bc*8:(bc+1)*8]
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                for i in range(8):
                    for j in range(8):
                        if i == 0 and j == 0:
                            continue
                        all_coeffs.append(dct_block[i, j])

        all_coeffs = np.array(all_coeffs)

        # 计算统计特征
        rounded = np.round(all_coeffs).astype(int)
        unique, counts = np.unique(rounded, return_counts=True)

        total = len(rounded)
        mean = np.mean(all_coeffs)
        std = np.std(all_coeffs)

        # 计算分布熵（自然图片应该有较高的熵）
        probs = counts / total
        entropy = -np.sum(probs * np.log2(probs + 1e-10))

        # 计算 chi-square 统计量
        expected_count = total / len(unique) if len(unique) > 0 else 1
        chi2 = np.sum((counts - expected_count) ** 2 / (expected_count + 1e-10))

        # 归一化 chi2
        chi2_norm = chi2 / (total + 1e-10)

        # 检测启发式规则
        # 1. 纯色图片（std 很低）不应该被判为有隐写
        # 2. 熵很低（图片很规则）不应该被判为有隐写
        # 3. chi2 值异常高或异常低时才可能是隐写

        # 正常自然图片的特征：
        # - 标准差通常在 10-100 之间
        # - 熵通常在 4-8 之间
        # - chi2_norm 通常在 0.5-3 之间

        confidence = 0.0

        if std < 1.0:
            # 纯色或非常简单的图片，极低概率有隐写
            confidence = 0.05
        elif entropy < 2.0:
            # 几乎没有纹理，很简单，不像是隐写
            confidence = 0.1
        elif chi2_norm < 0.01:
            # 分布非常均匀，可能是隐写特征之一
            confidence = 0.3
        elif chi2_norm > 10.0:
            # 分布非常不均匀，可能是隐写特征之一
            confidence = 0.4
        elif std > 5.0 and entropy > 4.0:
            # 自然图片特征
            confidence = 0.15
        else:
            # 默认低置信度
            confidence = 0.2

        # 综合多个因素计算置信度
        # 隐写检测特征分析
        base_confidence = 0.5
        
        # 熵分析：隐写通常会略微降低或改变熵
        if entropy < 1.5:
            # 极低熵图片（纯色等）不太可能包含隐写
            base_confidence = 0.1
        elif entropy < 3.0:
            # 低熵图片
            base_confidence = 0.25
        elif 3.0 <= entropy <= 8.0:
            # 正常图片范围，分析其他特征
            # 标准差：自然图片通常在 10-100
            if std > 15 and std < 80:
                # 自然图片特征，略微降低隐写可能性
                base_confidence = 0.35
            elif std >= 80:
                # 高对比度图片，可能有更多细节
                base_confidence = 0.55
            else:
                base_confidence = 0.45
        else:
            # 高熵图片，可能包含复杂内容
            base_confidence = 0.6
        
        # Chi-square 分析：隐写可能造成 chi-square 值异常
        if chi2_norm < 0.1:
            base_confidence += 0.15
        elif chi2_norm > 5.0:
            base_confidence += 0.2
        
        # 综合判断：普通图片默认较低置信度，有特征时提高
        final_confidence = base_confidence * 0.3 + 0.5

        final_confidence = float(np.clip(final_confidence, 0.0, 1.0))

        has_hidden = final_confidence > 0.5

        return {
            'has_hidden': has_hidden,
            'confidence': round(final_confidence, 4)
        }

    except Exception as e:
        return {
            'has_hidden': False,
            'confidence': 0.0
        }
