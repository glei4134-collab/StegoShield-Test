from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

from app.config import Config
from app.errors import StegoError


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure upload dir exists
    Config.init_app()

    # Register blueprints
    from app.routes.stego import stego_bp
    app.register_blueprint(stego_bp)

    # 提供前端静态页面
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend')
    
    @app.route('/')
    def index():
        frontend_path = os.path.join(frontend_dir, 'simple.html')
        if os.path.exists(frontend_path):
            return send_from_directory(frontend_dir, 'simple.html')
        return '<h1>StegoShield 运行中</h1><p>API: <a href="/api/health">/api/health</a></p>'
    
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(os.path.join(frontend_dir, 'css'), filename)

    # 实验功能（可选加载）
    # from app.routes.analyze import analyze_bp
    # app.register_blueprint(analyze_bp)

    # Error handlers
    @app.errorhandler(StegoError)
    def handle_stego_error(e):
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': '资源不存在'
            }
        }), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '服务器内部错误'
            }
        }), 500

    return app
