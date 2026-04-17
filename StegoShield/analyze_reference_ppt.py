"""
分析参考PPT文件，获取其风格和结构
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import os

def analyze_presentation(ppt_path):
    """分析PPT文件并返回结构和风格信息"""
    
    if not os.path.exists(ppt_path):
        print(f"文件不存在: {ppt_path}")
        return None
    
    prs = Presentation(ppt_path)
    
    analysis = {
        "slide_count": len(prs.slides),
        "slide_width": prs.slide_width.inches,
        "slide_height": prs.slide_height.inches,
        "slides": []
    }
    
    print(f"PPT信息:")
    print(f"- 幻灯片数量: {analysis['slide_count']}")
    print(f"- 尺寸: {analysis['slide_width']:.2f} x {analysis['slide_height']:.2f} 英寸")
    print(f"\n幻灯片结构:\n")
    
    for idx, slide in enumerate(prs.slides, 1):
        slide_info = {
            "index": idx,
            "title": "",
            "shapes_count": len(slide.shapes),
            "texts": []
        }
        
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        if not slide_info["title"] and len(text) < 100:
                            slide_info["title"] = text[:50]
                        slide_info["texts"].append(text[:100])
        
        analysis["slides"].append(slide_info)
        print(f"第{idx}页: {slide_info['title']}")
        print(f"  - 形状数量: {slide_info['shapes_count']}")
        if slide_info["texts"]:
            print(f"  - 主要文字: {' | '.join(slide_info['texts'][:3])}")
        print()
    
    return analysis

if __name__ == '__main__':
    ppt_path = r"C:\Users\17544\Documents\WXWork\1688854959646674\Cache\File\2026-04\专业创新创业训练答辩.pptx"
    result = analyze_presentation(ppt_path)
    
    if result:
        print("\n分析完成！")
        print(f"接下来我将基于这个PPT的风格，为您创建StegoShield项目的比赛PPT。")
        print(f"参考PPT共{result['slide_count']}页，我将创建类似结构但包含StegoShield内容的PPT。")