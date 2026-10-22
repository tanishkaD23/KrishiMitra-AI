"""Root entrypoint to run KrishiMitra AI with Flask backend and SQLite database.
Usage:
    python app.py
"""

import os
from src.api.flask_app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting KrishiMitra AI Flask Backend on http://127.0.0.1:{port}")
    print(f" - Dashboard: http://127.0.0.1:{port}/dashboard")
    print(f" - Model Summary: http://127.0.0.1:{port}/model-summary")
    print(f" - REST API Health: http://127.0.0.1:{port}/api/health")
    app.run(host="0.0.0.0", port=port, debug=True)
