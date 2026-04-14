# -*- coding: utf-8 -*-
"""
PPT Text Modifier - XML-level replacement for PPTX files.
Handles Chinese paths and encoding automatically.
"""
import sys
import os
import json
import shutil
import tempfile
import re
from pathlib import Path

# Try to import pptx, handle absence gracefully
try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'

# ── Path helpers ──────────────────────────────────────────────────────────────

def get_temp_dir(suffix='_pptx_unpack'):
    """Create a temp directory, return path. Caller must remove it."""
    return tempfile.mkdtemp(suffix=suffix)

def get_temp_file(suffix='.pptx'):
    """Create a temp file, return path. Caller must remove it."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path

def copy_to_temp(src):
    """Copy file to temp location, return temp path."""
    tmp = get_temp_file()
    shutil.copy2(src, tmp)
    return tmp

def copy_to_dst(tmp, dst):
    """Copy temp file to destination."""
    os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
    shutil.copy2(tmp, dst)

# ── PPTX unpack/repack ────────────────────────────────────────────────────────

def unpack_pptx(pptx_path, unpack_dir):
    """Unpack PPTX to directory."""
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX not found: {pptx_path}")
    if os.path.exists(unpack_dir):
        shutil.rmtree(unpack_dir)
    os.makedirs(unpack_dir)
    import zipfile
    with zipfile.ZipFile(pptx_path, 'r') as z:
        z.extractall(unpack_dir)
    return unpack_dir

def repack_pptx(unpack_dir, output_path):
    """Repack directory to PPTX."""
    import zipfile
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(unpack_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, unpack_dir)
                z.write(file_path, arcname)

# ── Text replacement in XML ──────────────────────────────────────────────────

def replace_in_xml(xml_content, old_text, new_text):
    """Replace all occurrences of old_text in XML content string."""
    count = xml_content.count(old_text)
    if count == 0:
        return xml_content, 0
    new_content = xml_content.replace(old_text, new_text)
    return new_content, count

def modify_slide(xml_path, old_text, new_text):
    """Replace text in a single slide XML file."""
    if not os.path.exists(xml_path):
        return 0
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content, count = replace_in_xml(content, old_text, new_text)
    if count > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    return count

def modify_all_slides(unpack_dir, old_text, new_text):
    """Apply replacement to all slide XML files."""
    slides_dir = os.path.join(unpack_dir, 'ppt', 'slides')
    total = 0
    for fname in os.listdir(slides_dir):
        if fname.startswith('slide') and fname.endswith('.xml'):
            path = os.path.join(slides_dir, fname)
            total += modify_slide(path, old_text, new_text)
    return total

# ── Validation ────────────────────────────────────────────────────────────────

def validate_slide(pptx_path, slide_index):
    """Read and return text content of a specific slide."""
    if not HAS_PPTX:
        return "pptx library not available for validation"
    try:
        tmp = copy_to_temp(pptx_path)
        prs = Presentation(tmp)
        os.unlink(tmp)
        slide = prs.slides[slide_index - 1]
        lines = []
        for shape in slide.shapes:
            t = ''.join(x.text for x in shape._element.iter('{%s}t' % NS) if x.text).strip()
            if t:
                lines.append(t)
        return '\n'.join(lines)
    except Exception as e:
        return f"Validation error: {e}"

def validate_all_slides(pptx_path):
    """Read all slide texts for validation."""
    if not HAS_PPTX:
        return "pptx library not available"
    try:
        tmp = copy_to_temp(pptx_path)
        prs = Presentation(tmp)
        os.unlink(tmp)
        lines = []
        for i, slide in enumerate(prs.slides):
            lines.append(f"=== Slide {i+1} ===")
            for shape in slide.shapes:
                t = ''.join(x.text for x in shape._element.iter('{%s}t' % NS) if x.text).strip()
                if t:
                    lines.append('  ' + t[:80])
        return '\n'.join(lines)
    except Exception as e:
        return f"Validation error: {e}"

# ── Main workflow ─────────────────────────────────────────────────────────────

def modify_pptx(input_path, output_path, old_text, new_text, target_slide=None):
    """Full workflow: copy → unpack → modify → repack → validate."""
    tmp_input = copy_to_temp(input_path)
    unpack_dir = get_temp_dir(suffix='_pptx_unpack')
    unpack_pptx(tmp_input, unpack_dir)
    os.unlink(tmp_input)

    if target_slide and str(target_slide).lower() != 'all':
        slide_file = os.path.join(unpack_dir, 'ppt', 'slides', f'slide{target_slide}.xml')
        count = modify_slide(slide_file, old_text, new_text)
    else:
        count = modify_all_slides(unpack_dir, old_text, new_text)

    if count == 0:
        print(f"WARNING: '{old_text[:30]}' not found")
    else:
        print(f"Replaced '{old_text[:30]}' ({count} occurrence(s))")

    tmp_output = get_temp_file(suffix='.pptx')
    repack_pptx(unpack_dir, tmp_output)
    shutil.rmtree(unpack_dir)
    copy_to_dst(tmp_output, output_path)
    os.unlink(tmp_output)
    return count

def modify_from_json(input_path, output_path, json_path):
    """Apply multiple replacements from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        replacements = json.load(f)

    tmp_input = copy_to_temp(input_path)
    unpack_dir = get_temp_dir(suffix='_pptx_unpack')
    unpack_pptx(tmp_input, unpack_dir)
    os.unlink(tmp_input)

    total = 0
    for rep in replacements:
        slide = rep.get('slide', 'all')
        old_text = rep['old']
        new_text = rep['new']

        if slide == 'all' or slide is None:
            count = modify_all_slides(unpack_dir, old_text, new_text)
        else:
            slide_file = os.path.join(unpack_dir, 'ppt', 'slides', f'slide{slide}.xml')
            count = modify_slide(slide_file, old_text, new_text)

        status = "OK" if count > 0 else "MISS"
        print(f"{status:4s}  slide={str(slide):4s}  {old_text[:30]}")
        total += count

    tmp_output = get_temp_file(suffix='.pptx')
    repack_pptx(unpack_dir, tmp_output)
    shutil.rmtree(unpack_dir)
    copy_to_dst(tmp_output, output_path)
    os.unlink(tmp_output)
    print(f"\nTotal replacements: {total}")
    return total

# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single:  python modify_pptx.py <in.pptx> <out.pptx> <old> <new> [slide]")
        print("  JSON:    python modify_pptx.py <in.pptx> <out.pptx> --json <replacements.json>")
        sys.exit(1)

    input_pptx = sys.argv[1]
    output_pptx = sys.argv[2]

    if len(sys.argv) >= 4 and sys.argv[3] == '--json':
        modify_from_json(input_pptx, output_pptx, sys.argv[4])
    elif len(sys.argv) >= 5:
        old_text = sys.argv[3]
        new_text = sys.argv[4]
        target_slide = sys.argv[5] if len(sys.argv) >= 6 else 'all'
        modify_pptx(input_pptx, output_pptx, old_text, new_text, target_slide)
    else:
        print("Invalid arguments")
        sys.exit(1)
