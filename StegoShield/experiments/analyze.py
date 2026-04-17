"""
Image analysis routes — steganalysis for detecting hidden content.
"""

import os
import base64
import tempfile
from flask import Blueprint, request, jsonify

from app.services import analyzer

analyze_bp = Blueprint('analyze', __name__)


@analyze_bp.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze an image for potential hidden content.
    
    Accepts JSON: {"image": "base64_string"}
    Returns: {"success": true, "has_hidden": bool, "confidence": float}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        image_b64 = data.get('image', '')
        if not image_b64:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        # Strip data URL prefix if present (e.g. "data:image/png;base64,")
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid base64: {e}'}), 400

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
            tmp_in.write(image_bytes)
            tmp_in_path = tmp_in.name

        try:
            result = analyzer.analyze_image(tmp_in_path)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Analyzer error: {e}'}), 400
        finally:
            os.unlink(tmp_in_path)

        return jsonify({
            'success': True,
            'has_hidden': result['has_hidden'],
            'confidence': result['confidence']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@analyze_bp.route('/api/analyze-debug', methods=['POST'])
def analyze_debug():
    """Debug endpoint to inspect exactly what's being sent."""
    content_type = request.content_type
    data_len = len(request.data)
    try:
        data = request.get_json()
    except Exception as e:
        data = f'JSON parse error: {e}'
    
    return jsonify({
        'content_type': content_type,
        'data_len': data_len,
        'data_preview': str(request.data[:100]),
        'parsed_data_type': type(data).__name__,
        'parsed_data_keys': list(data.keys()) if isinstance(data, dict) else 'not a dict'
    })
