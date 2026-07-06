import os
from pathlib import Path

from flask import Flask, send_from_directory

from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.practice_routes import practice_bp

ROOT = Path(__file__).parent
PORT = int(os.environ.get("PORT", "8010"))


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("MATHPRACAI_SECRET_KEY", "mathpracai-dev-secret")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(practice_bp)

    @app.get("/styles.css")
    def styles():
        return send_from_directory(ROOT / "static", "styles.css", mimetype="text/css")

    @app.get("/script.js")
    def script():
        return send_from_directory(ROOT / "static", "script.js", mimetype="text/javascript")

    return app


app = create_app()


if __name__ == "__main__":
    print(f"Local server running at http://localhost:{PORT}/", flush=True)
    app.run(host="localhost", port=PORT, debug=False)
