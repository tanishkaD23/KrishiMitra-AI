"""Flask application for KrishiMitra AI backend serving REST APIs and the custom HTML/CSS/JS frontend."""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
try:
    from flask_cors import CORS
except ImportError:
    CORS = None

from config.settings import CONFIG, BASE_DIR
from src.database.db import (
    init_db,
    get_farmer_profile,
    update_farmer_profile,
    get_farmer_plots,
    add_farmer_plot,
    delete_farmer_plot,
    get_historical_yields,
    get_model_benchmarks,
)
from src.yield_model.predict import YieldPredictor
from src.advisory.agronomic_rules import AgronomicAdvisor, PersonalisedAdvisoryEngine
from src.schemes.eligibility_engine import SchemeEligibilityEngine
from src.krishisathi.voice_agent import KrishiSathiAgent
from src.weather.live_weather import fetch_open_meteo_weather

FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), template_folder=str(FRONTEND_DIR))
if CORS:
    CORS(app)

init_db()
predictor = YieldPredictor()
schemes_engine = SchemeEligibilityEngine()
voice_agent = KrishiSathiAgent()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/dashboard")
def dashboard_page():
    return send_from_directory(app.static_folder, "dashboard.html")


@app.route("/forecast")
def forecast_page():
    return send_from_directory(app.static_folder, "forecast.html")


@app.route("/schemes")
def schemes_page():
    return send_from_directory(app.static_folder, "schemes.html")


@app.route("/krishisathi")
def krishisathi_page():
    return send_from_directory(app.static_folder, "krishisathi.html")


@app.route("/about")
@app.route("/model-summary")
def about_page():
    return send_from_directory(app.static_folder, "about.html")


@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "backend": "Flask",
        "pilot_region": CONFIG.region,
        "supported_states": CONFIG.supported_states,
        "database": "SQLite (krishimitra.db)",
    })


@app.route("/api/config")
@app.route("/api/metadata")
def get_metadata():
    return jsonify({
        "state": CONFIG.state,
        "supported_states": CONFIG.supported_states,
        "state_districts": CONFIG.state_districts,
        "state_yield_benchmarks": CONFIG.state_yield_benchmarks,
        "states": CONFIG.supported_states,
        "districts": CONFIG.state_districts,
        "crops": CONFIG.crops,
    })


@app.route("/api/states")
def get_states():
    return jsonify({
        "status": "success",
        "supported_states": CONFIG.supported_states,
        "state_districts": CONFIG.state_districts,
        "state_yield_benchmarks": CONFIG.state_yield_benchmarks,
    })


@app.route("/api/farmer", methods=["GET", "PUT", "POST"])
def farmer_endpoint():
    farmer_id = request.args.get("farmer_id", "farmer-001")
    if request.method in ("PUT", "POST"):
        data = request.get_json(force=True) or {}
        fid = data.get("farmer_id", farmer_id)
        updated = update_farmer_profile(data, farmer_id=fid)
        return jsonify({"status": "success", "farmer": updated})
    profile = get_farmer_profile(farmer_id)
    return jsonify({"status": "success", "farmer": profile})


@app.route("/api/plots", methods=["GET", "POST"])
def plots_endpoint():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        if "plot_name" in data and "name" not in data:
            data["name"] = data["plot_name"]
        if "area_acres" in data and "acres" not in data:
            data["acres"] = data["area_acres"]
        new_plot = add_farmer_plot(data)
        plots = get_farmer_plots(data.get("farmer_id", "farmer-001"))
        return jsonify({"status": "success", "plot": new_plot, "plots": plots}), 201
    farmer_id = request.args.get("farmer_id", "farmer-001")
    plots = get_farmer_plots(farmer_id)
    return jsonify({"status": "success", "plots": plots})


@app.route("/api/plots/<plot_id>", methods=["DELETE"])
def delete_plot_endpoint(plot_id):
    farmer_id = request.args.get("farmer_id", "farmer-001")
    deleted = delete_farmer_plot(plot_id, farmer_id=farmer_id)
    plots = get_farmer_plots(farmer_id)
    return jsonify({"status": "success", "deleted": deleted, "plot_id": plot_id, "plots": plots})


@app.route("/api/yield-history")
def yield_history_endpoint():
    district = request.args.get("district", "Meerut")
    crop = request.args.get("crop", "Wheat")
    state = request.args.get("state")
    records = get_historical_yields(district, crop, state=state)
    return jsonify({
        "status": "success",
        "district": district,
        "state": state or "Uttar Pradesh",
        "crop": crop,
        "records_count": len(records),
        "records": records,
    })


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True) or {}
    res = predictor.predict(data)
    return jsonify(res)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True) or {}
    y_res = predictor.predict(data)
    advisory_res = AgronomicAdvisor.get_advisory(data, y_res if y_res.get("supported") else None)
    schemes_res = schemes_engine.evaluate_eligibility(data)
    farmer_cat = schemes_engine.classify_farmer_category(float(data.get("plot_acres", 2.0)))
    return jsonify({
        "status": "success",
        "plot_input": data,
        "farmer_category": farmer_cat,
        "yield": y_res,
        "advisory": advisory_res,
        "schemes": schemes_res,
    })


@app.route("/api/advisory", methods=["GET", "POST"])
def api_advisory():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
    else:
        symptoms_str = request.args.get("symptoms", "")
        activities_str = request.args.get("activities", "")
        data = {
            "crop": request.args.get("crop", "Wheat"),
            "district": request.args.get("district", "Meerut"),
            "state": request.args.get("state", "Uttar Pradesh"),
            "growth_stage": request.args.get("stage") or request.args.get("growth_stage") or "Tillering",
            "stage": request.args.get("stage") or request.args.get("growth_stage") or "Tillering",
            "reported_symptoms": [s.strip() for s in symptoms_str.split(",") if s.strip()],
            "recent_activities": [a.strip() for a in activities_str.split(",") if a.strip()],
        }
    yield_out = predictor.predict(data) if data.get("crop", "Wheat") in CONFIG.crops else None
    adv = PersonalisedAdvisoryEngine.generate_advisory(data, yield_out)
    return jsonify(adv)


@app.route("/api/weather")
def api_weather():
    district = request.args.get("district", "Meerut")
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    return jsonify(fetch_open_meteo_weather(district, lat=lat, lon=lon))


@app.route("/api/schemes")
def api_schemes():
    crop = request.args.get("crop", "Wheat")
    acres = float(request.args.get("acres", 2.0))
    state = request.args.get("state", "Uttar Pradesh")
    district = request.args.get("district", "Meerut")
    data = {"crop": crop, "plot_acres": acres, "state": state, "district": district}
    schemes = schemes_engine.evaluate_eligibility(data)
    return jsonify({
        "status": "success",
        "farmer_category": schemes_engine.classify_farmer_category(acres),
        "schemes": schemes,
    })


@app.route("/api/krishisathi/chat", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    query = data.get("query") or data.get("message") or ""
    context = data.get("context") or {}
    lang = data.get("lang") or "hi"
    rag_res = voice_agent.ask_rag(query, context, lang=lang)
    return jsonify({
        "status": "success",
        "answer": rag_res.get("answer", ""),
        "sources": rag_res.get("sources", []),
        "retrieval_mode": rag_res.get("retrieval_mode", "general"),
        "verified": rag_res.get("verified", True),
        "lang": rag_res.get("lang", lang),
    })


@app.route("/api/model-summary")
def api_model_summary():
    summary_path = BASE_DIR / "models" / "model_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"status": "ok", "models": get_model_benchmarks()})


@app.route("/api/dashboard-data")
def api_dashboard_data():
    state = request.args.get("state", "Uttar Pradesh")
    district = request.args.get("district", "Meerut")
    crop = request.args.get("crop", "Wheat")
    farmer_id = request.args.get("farmer_id", "farmer-001")
    stage = request.args.get("stage") or request.args.get("growth_stage") or "Tillering"
    symptoms_str = request.args.get("symptoms", "")

    farmer = get_farmer_profile(farmer_id) or {"name": "Tanishka", "district": district, "state": state}
    plots = get_farmer_plots(farmer_id)
    pred = predictor.predict({"state": state, "district": district, "crop": crop, "plot_acres": 2.0})
    hist = get_historical_yields(district, crop, state=state)
    weather = fetch_open_meteo_weather(district)
    adv = PersonalisedAdvisoryEngine.generate_advisory({
        "crop": crop,
        "district": district,
        "state": state,
        "growth_stage": stage,
        "stage": stage,
        "reported_symptoms": [s.strip() for s in symptoms_str.split(",") if s.strip()],
    }, pred)
    schemes = schemes_engine.evaluate_eligibility({"crop": crop, "district": district, "state": state, "plot_acres": 2.0})

    return jsonify({
        "status": "success",
        "state": state,
        "district": district,
        "crop": crop,
        "farmer": farmer,
        "plots": plots,
        "prediction": pred,
        "historical_yields": hist,
        "forecast_points": [
            {"year": 2024, "predicted_yield_q_acre": pred.get("predicted_yield_per_acre", 16.8)},
            {"year": 2025, "predicted_yield_q_acre": round(pred.get("predicted_yield_per_acre", 16.8) * 1.02, 2)},
        ],
        "weather": weather,
        "advisory": adv,
        "schemes": schemes,
    })
