"""Root entrypoint to run KrishiMitra AI with Flask backend across all 6 States."""
import os
from src.api.flask_app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f"KrishiMitra AI Multi-State Engine Launched")
    print(f"Running locally at: http://127.0.0.1:{port}")
    print(f"Dashboard:          http://127.0.0.1:{port}/dashboard")
    print(f"Yield Predictor:    http://127.0.0.1:{port}/forecast.html")
    print(f"Govt Schemes:       http://127.0.0.1:{port}/schemes.html")
    print(f"KrishiSathi AI:     http://127.0.0.1:{port}/krishisathi.html")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)