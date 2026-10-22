"""Flask Application for KrishiMitra AI backend.
Serves REST APIs, integrates with SQLite database and evaluated ML models,
and hosts the custom HTML/CSS/JS frontend dashboard.
"""

import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file

from config.settings import BASE_DIR, CONFIG
from src.database.db import (
    init_db,
    get_farmer_profile,
    get_farmer_plots,
    add_farmer_plot,
    get_historical_yields,
    get_model_benchmarks
)
from src.yield_model.predict import YieldPredictor
from src.advisory.agronomic_rules import AgronomicAdvisor, PersonalisedAdvisoryEngine
from src.schemes.eligibility_engine import SchemeEligibilityEngine
from src.krishisathi.voice_agent import KrishiSathiAgent
from src.weather.live_weather import fetch_open_meteo_weather

FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

# Enable CORS (either via flask_cors or pure Flask after_request hook)
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
        return response


# Initialize engines & DB
init_db()
predictor = YieldPredictor()
schemes_engine = SchemeEligibilityEngine()
voice_agent = KrishiSathiAgent()


# =========================================================================
# 1. Frontend Route Serving
# =========================================================================

@app.route("/")
def serve_index():
    return send_file(FRONTEND_DIR / "index.html")

@app.route("/dashboard")
def serve_dashboard():
    return send_file(FRONTEND_DIR / "dashboard.html")

@app.route("/forecast")
def serve_forecast():
    return send_file(FRONTEND_DIR / "forecast.html")

@app.route("/schemes")
def serve_schemes():
    return send_file(FRONTEND_DIR / "schemes.html")

@app.route("/krishisathi")
def serve_krishisathi():
    return send_file(FRONTEND_DIR / "krishisathi.html")

@app.route("/model-summary")
def serve_model_summary():
    return send_file(FRONTEND_DIR / "model-summary.html")

@app.route("/about")
def serve_about():
    return send_file(FRONTEND_DIR / "about.html")

# Static assets fallback
@app.route("/<path:filename>")
def serve_static(filename):
    target = FRONTEND_DIR / filename
    if target.exists() and target.is_file():
        return send_file(target)
    return send_file(FRONTEND_DIR / "index.html")


# =========================================================================
# 2. REST API Endpoints
# =========================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "backend": "Flask",
        "pilot_region": CONFIG.region,
        "database": "SQLite (krishimitra.db)"
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns available pilot choices, districts, crops, and baselines."""
    return jsonify({
        "state": CONFIG.state,
        "region": CONFIG.region,
        "season": CONFIG.season,
        "districts": CONFIG.districts,
        "crops": CONFIG.crops,
        "soil_types": CONFIG.soil_types,
        "irrigation_sources": CONFIG.irrigation_sources,
        "sowing_windows": [
            "Early Rabi (Oct 15 - Oct 31)",
            "Timely Sown (Nov 01 - Nov 20)",
            "Late Sown (Nov 21 - Dec 15)",
        ],
        "yield_unit": CONFIG.yield_unit,
        "baseline_benchmarks": CONFIG.baseline_yield_benchmarks,
    })


@app.route("/api/farmer", methods=["GET"])
def get_farmer():
    """Returns profile and plot overview for the logged-in farmer."""
    farmer_id = request.args.get("farmer_id", "farmer-001")
    profile = get_farmer_profile(farmer_id)
    if not profile:
        return jsonify({"error": "Farmer not found"}), 404
    return jsonify({"status": "success", "farmer": profile})


@app.route("/api/plots", methods=["GET", "POST"])
def manage_plots():
    """GET returns farmer's registered plots; POST registers a new plot."""
    if request.method == "GET":
        farmer_id = request.args.get("farmer_id", "farmer-001")
        plots = get_farmer_plots(farmer_id)
        return jsonify({"status": "success", "plots": plots})

    # POST new plot
    data = request.get_json(force=True, silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Plot name is required"}), 400

    new_plot = add_farmer_plot(data)
    return jsonify({"status": "success", "plot": new_plot}), 201


@app.route("/api/yield-history", methods=["GET"])
def yield_history():
    """Returns real historical yields from official APY database records."""
    district = request.args.get("district", "Meerut")
    crop = request.args.get("crop", "Wheat")
    records = get_historical_yields(district, crop)
    return jsonify({
        "status": "success",
        "district": district,
        "crop": crop,
        "records_count": len(records),
        "source": "Official Uttar Pradesh APY District Records (2012-2023)",
        "records": records
    })


@app.route("/api/analyze", methods=["POST"])
def analyze_plot():
    """Composite API computing yield prediction, stage-specific advisory,

    and scheme eligibility in a single fast call.
    """
    farmer_data = request.get_json(force=True, silent=True) or {}
    try:
        # 1. Yield Prediction
        yield_output = predictor.predict(farmer_data)

        # 2. Agronomic Advisory
        advisory_output = AgronomicAdvisor.get_advisory(farmer_data, yield_output)

        # 3. Scheme Eligibility
        schemes_output = schemes_engine.evaluate_eligibility(farmer_data)
        plot_acres = float(farmer_data.get("plot_acres", 2.0))
        farmer_category = schemes_engine.classify_farmer_category(plot_acres)

        return jsonify({
            "status": "success",
            "plot_input": farmer_data,
            "farmer_category": farmer_category,
            "yield": yield_output,
            "advisory": advisory_output,
            "schemes": schemes_output,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def predict_yield():
    """Point-estimate yield prediction with confidence bounds and conversions."""
    farmer_data = request.get_json(force=True, silent=True) or {}
    try:
        yield_output = predictor.predict(farmer_data)
        return jsonify(yield_output)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/dashboard-data", methods=["GET"])
def get_dashboard_data():
    """Unified dashboard data aggregator serving real database records,

    live ML model predictions, and telemetry.
    """
    district = request.args.get("district", "Meerut")
    crop = request.args.get("crop", "Wheat")
    farmer_id = request.args.get("farmer_id", "farmer-001")
    plot_id = request.args.get("plot_id")
    stage = request.args.get("stage") or request.args.get("growth_stage")
    symptoms = request.args.get("symptoms", "")
    activities = request.args.get("activities", "")
    sowing_date = request.args.get("sowing_date")
    irrigation = request.args.get("irrigation") or request.args.get("irrigation_source")

    # 1. Farmer & Plots from DB
    farmer = get_farmer_profile(farmer_id) or {
        "name": "Tanishka",
        "district": district,
        "total_acres": 4.5,
        "plot_count": 3
    }
    plots = get_farmer_plots(farmer_id)

    # Find selected plot
    selected_plot = None
    if plot_id:
        for p in plots:
            if str(p["id"]) == str(plot_id):
                selected_plot = p
                break
    if not selected_plot and plots:
        for p in plots:
            if p["crop"].lower() == crop.lower():
                selected_plot = p
                break
        if not selected_plot:
            selected_plot = plots[0]

    active_stage = stage or (selected_plot.get("stage") if selected_plot else "Tillering")
    active_symptoms = [s.strip() for s in symptoms.split(",") if s.strip()] if symptoms else []
    active_activities = [a.strip() for a in activities.split(",") if a.strip()] if activities else []
    active_irrigation = irrigation or (selected_plot.get("irrigation_source") if selected_plot else "Tube well / Borewell")
    active_sowing_date = sowing_date or (selected_plot.get("sowing_date") if selected_plot else None)

    # 2. Live Prediction using evaluated model
    plot_input = {
        "crop": crop,
        "district": district,
        "state": "Uttar Pradesh",
        "season": "Rabi",
        "plot_acres": float(selected_plot["acres"]) if selected_plot else 2.5,
        "soil_type": selected_plot["soil_type"] if selected_plot else "Alluvial (Sandy Loam)",
        "irrigation_source": active_irrigation,
        "sowing_window": selected_plot.get("sowing_window", "Timely Sown (Nov 01 - Nov 20)") if selected_plot else "Timely Sown (Nov 01 - Nov 20)",
        "sowing_date": active_sowing_date,
        "growth_stage": active_stage,
        "stage": active_stage,
        "recent_activities": active_activities,
        "reported_symptoms": active_symptoms,
        "seasonal_rainfall_mm": 65.0,
        "march_max_temp_c": 31.5,
        "nitrogen_kg_acre": float(selected_plot.get("nitrogen_kg_acre", 48.0)) if selected_plot else 48.0,
        "phosphorus_kg_acre": float(selected_plot.get("phosphorus_kg_acre", 22.0)) if selected_plot else 22.0,
        "potassium_kg_acre": float(selected_plot.get("potassium_kg_acre", 15.0)) if selected_plot else 15.0,
        "farmer_id": farmer_id,
        "plot_id": selected_plot["id"] if selected_plot else None
    }
    prediction = predictor.predict(plot_input)

    # 3. Real Historical APY Yields from DB (2018–2023)
    history_records = get_historical_yields(district, crop)
    recent_history = [r for r in history_records if r["start_year"] >= 2018]
    if not recent_history:
        recent_history = history_records[-6:] if history_records else []

    # 4. Projected points for 2024 and 2025
    pred_q_ha = prediction.get("predicted_yield_q_ha", 40.0) if prediction.get("supported", True) else 39.0
    forecast_points = [
        {"year": "2024 (P)", "start_year": 2024, "yield_q_ha": round(pred_q_ha * 0.98, 1), "yield_q_acre": round(pred_q_ha * 0.98 / 2.47105, 1)},
        {"year": "2025 (P)", "start_year": 2025, "yield_q_ha": round(pred_q_ha, 1), "yield_q_acre": round(pred_q_ha / 2.47105, 1)},
    ]

    # 5. Live Weather (Real Open-Meteo API using district coordinates)
    weather = fetch_open_meteo_weather(district)

    # 6. Agronomic Advisory
    advisory = AgronomicAdvisor.get_advisory(plot_input, prediction if prediction.get("supported") else None)

    # 7. Schemes
    schemes = schemes_engine.evaluate_eligibility(plot_input)

    # 8. Model Benchmark Metadata
    benchmarks = get_model_benchmarks()

    return jsonify({
        "status": "success",
        "farmer": farmer,
        "plots": plots,
        "selected_plot": selected_plot,
        "prediction": prediction,
        "historical_yields": recent_history,
        "forecast_points": forecast_points,
        "weather": weather,
        "advisory": advisory,
        "schemes": schemes,
        "model_benchmarks": benchmarks,
        "pilot_scope": {
            "supported_crops": CONFIG.crops,
            "supported_districts": CONFIG.districts,
            "pilot_region": CONFIG.region
        }
    })


@app.route("/api/advisory", methods=["GET", "POST"])
def api_advisory():
    """Generates structured personalised advisory cards grounded in ICAR & IMD protocols."""
    if request.method == "POST":
        farmer_data = request.get_json(force=True, silent=True) or {}
    else:
        stage = request.args.get("stage") or request.args.get("growth_stage") or "Tillering"
        symptoms = request.args.get("symptoms", "")
        activities = request.args.get("activities", "")
        farmer_data = {
            "crop": request.args.get("crop", "Wheat"),
            "district": request.args.get("district", "Meerut"),
            "state": request.args.get("state", "Uttar Pradesh"),
            "season": request.args.get("season", "Rabi"),
            "growth_stage": stage,
            "stage": stage,
            "sowing_window": request.args.get("sowing_window", "Timely Sown (Nov 01 - Nov 20)"),
            "sowing_date": request.args.get("sowing_date"),
            "irrigation_source": request.args.get("irrigation_source") or request.args.get("irrigation") or "Tube well / Borewell",
            "soil_type": request.args.get("soil_type", "Alluvial (Sandy Loam)"),
            "march_max_temp_c": float(request.args.get("march_max_temp_c", 31.5)),
            "seasonal_rainfall_mm": float(request.args.get("seasonal_rainfall_mm", 65.0)),
            "reported_symptoms": [s.strip() for s in symptoms.split(",") if s.strip()] if symptoms else [],
            "recent_activities": [a.strip() for a in activities.split(",") if a.strip()] if activities else []
        }
    try:
        yield_out = predictor.predict(farmer_data) if farmer_data.get("crop") in CONFIG.crops else None
        advisory_output = PersonalisedAdvisoryEngine.generate_advisory(farmer_data, yield_out)
        return jsonify(advisory_output)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/krishisathi/chat", methods=["POST"])
def krishisathi_chat():
    """Voice/Chatbot assistant returning grounded agronomic advice."""
    payload = request.get_json(force=True, silent=True) or {}
    query = payload.get("query", "")
    context = payload.get("context", {})
    lang = payload.get("lang", "hi")
    try:
        answer = voice_agent.ask(query, context, lang=lang)
        return jsonify({"status": "success", "answer": answer})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/model-summary", methods=["GET"])
def get_model_summary():
    """Returns validated model evaluation summary and temporal split metadata."""
    summary_path = BASE_DIR / "models" / "model_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Model summary not found"}), 404


@app.route("/api/schemes", methods=["GET"])
def get_schemes():
    """Returns government schemes list."""
    schemes_path = BASE_DIR / "data" / "schemes" / "central_schemes.json"
    if schemes_path.exists():
        with open(schemes_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route("/api/weather", methods=["GET"])
def api_weather():
    """Fetches real-time weather from Open-Meteo for the requested district or coordinates."""
    district = request.args.get("district", "Meerut")
    lat = float(request.args.get("lat")) if request.args.get("lat") else None
    lon = float(request.args.get("lon")) if request.args.get("lon") else None
    return jsonify(fetch_open_meteo_weather(district, lat, lon))


# =========================================================================
# Entrypoint for direct Flask execution
# =========================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
