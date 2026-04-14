# PPT Modifier Skill

## What it does
Modify text content in PPTX files via XML-level replacement. Handles Chinese paths and encoding automatically.

## When to use
When the user asks to update text in a PowerPoint file (not create a new one from scratch).

## How it works
1. Copy file to temp path (avoids Chinese path issues)
2. Unpack PPTX → read XML
3. Replace text directly in XML strings (bypasses python-pptx run-splitting issues)
4. Repack PPTX
5. Copy back to original location
6. Validate by reading back content

## Usage
```bash
python modify_pptx.py <input.pptx> <output.pptx> <slide_index> "<old_text>" "<new_text>"
```

## Arguments
- `input.pptx`: Source PPTX path (Chinese paths supported)
- `output.pptx`: Destination PPTX path
- `slide_index`: 1-based slide number to modify, or "all" for all slides
- `old_text`: Exact text to find and replace
- `new_text`: Replacement text

## Multiple replacements at once
Create a JSON file `replacements.json`:
```json
[
  {"slide": 3, "old": "原文本", "new": "新文本"},
  {"slide": 4, "old": "原文本", "new": "新文本"}
]
```
Then run:
```bash
python modify_pptx.py <input.pptx> <output.pptx> --json replacements.json
```

## Notes
- Text replacement is done at the XML string level — no python-pptx text API involved
- Multi-run text (same paragraph split across multiple <a:t> elements) is handled correctly
- Always validates output by reading back and printing changed text
