# app.py

from flask import Flask
from api.routes import api
from core.orchestrator import run_pipeline

app = Flask(__name__)
app.register_blueprint(api, url_prefix="/api")


if __name__ == "__main__":
    # Optional: run scraper once before starting API
    run_pipeline()

    app.run(host="0.0.0.0", port=5000, debug=True)