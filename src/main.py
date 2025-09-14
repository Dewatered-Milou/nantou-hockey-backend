import os
from flask import Flask, send_from_directory  # ← 加上 send_from_directory
from flask_cors import CORS

from .routes.registration import registration_bp
from .routes.tickets import tickets_bp
from .routes.gemini import gemini_bp

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-please-change')

CORS(app)

app.register_blueprint(registration_bp, url_prefix='/api/registration')
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
app.register_blueprint(gemini_bp, url_prefix='/api/gemini')

@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    # 本機請用：python -m src.main
    app.run(host='0.0.0.0', port=5000, debug=True)
