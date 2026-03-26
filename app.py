# app.py

from flask import Flask
from api.routes import api
from core.orchestrator import run_pipeline
import threading

app = Flask(__name__)
app.register_blueprint(api, url_prefix="/api")


def start_pipeline():
    run_pipeline()


if __name__ == "__main__":
    # Run pipeline in background thread
    threading.Thread(target=start_pipeline, daemon=True).start()

    # Start Flask server with reloader disabled so CTRL+C works
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)