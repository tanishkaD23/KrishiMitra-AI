"""Flask application for KrishiMitra AI backend serving REST APIs and the custom HTML/CSS/JS frontend."""

import json
import os
from pathlib import Path
from flask import Flask, Response, request, jsonify, send_from_directory
from dotenv import load_dotenv
try:
    from flask_cors import CORS
except ImportError:
    CORS = None

from config.settings import CONFIG, BASE_DIR

load_dotenv(BASE_DIR / ".env")
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
from src.krishisathi.gnani_voice import (
    get_gnani_voice_status,
    transcribe_speech_gnani,
    synthesize_speech_gnani,
)
from src.weather.live_weather import fetch_open_meteo_weather
from src.api.platform_services import (
    ensure_platform_tables,
    register_user,
    login_user,
    get_session_user,
    logout_user,
    create_password_reset_token,
    reset_user_password,
    list_all_users,
    get_krishischeme_intelligence,
    add_admin_scheme_record,
    assess_pmfby_claim_eligibility,
    get_insurance_history,
    fetch_nasa_power_intelligence,
)

FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), template_folder=str(FRONTEND_DIR))
if CORS:
    CORS(app)

init_db()
ensure_platform_tables()
predictor = YieldPredictor()
schemes_engine = SchemeEligibilityEngine()
voice_agent = KrishiSathiAgent()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "login.html")


@app.route("/dashboard")
def dashboard_page():
    return send_from_directory(app.static_folder, "dashboard.html")


@app.route("/forecast")
def forecast_page():
    return send_from_directory(app.static_folder, "forecast.html")


@app.route("/login")
def login_page():
    return send_from_directory(app.static_folder, "login.html")


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
        "all_india_crops": CONFIG.all_india_crops,
        "seasons": CONFIG.seasons,
        "district_crops": CONFIG.district_crops,
        "crop_seasons": CONFIG.crop_seasons,
        "supabase_url": os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or "",
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or "",
    })


@app.route("/api/auth/supabase-config")
def get_supabase_config_flask():
    return jsonify({
        "status": "success",
        "supabase_url": os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "",
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or "",
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
    include_tts = bool(data.get("include_tts", False))
    voice_gender = data.get("gender") or "female"
    voice_name = data.get("voice") or None

    rag_res = voice_agent.ask_rag(query, context, lang=lang)
    resp_payload = {
        "status": "success",
        "answer": rag_res.get("answer", ""),
        "sources": rag_res.get("sources", []),
        "retrieval_mode": rag_res.get("retrieval_mode", "general"),
        "verified": rag_res.get("verified", True),
        "lang": rag_res.get("lang", lang),
    }
    if include_tts and resp_payload["answer"]:
        tts_res = synthesize_speech_gnani(
            text=resp_payload["answer"],
            language="hi-IN" if resp_payload["lang"] == "hi" else "en-IN",
            voice=voice_name,
            gender=voice_gender,
            model="timbre-v2.5",
        )
        if tts_res.get("status") == "success":
            resp_payload["audio_base64"] = tts_res.get("audio_base64")
            resp_payload["audio_content_type"] = tts_res.get("content_type", "audio/wav")
            resp_payload["tts_model"] = tts_res.get("model", "timbre-v2.5")
            resp_payload["tts_voice"] = tts_res.get("voice")
    return jsonify(resp_payload)


@app.route("/api/krishisathi/voice-status", methods=["GET"])
@app.route("/api/voice/status", methods=["GET"])
def api_gnani_voice_status():
    """Returns Gnani.ai (Prisma STT + Timbre TTS) readiness without exposing API credentials."""
    return jsonify(get_gnani_voice_status())


@app.route("/api/krishisathi/stt", methods=["POST"])
@app.route("/api/voice/stt", methods=["POST"])
def api_gnani_stt():
    """Gnani Prisma v3.0 Speech-to-Text endpoint (proxies multipart audio to https://api.vachana.ai/stt/v3)."""
    uploaded = request.files.get("audio_file") or request.files.get("audio")
    if not uploaded:
        return jsonify({
            "status": "error",
            "error_code": "MISSING_AUDIO_FILE",
            "message": "No audio_file provided in multipart/form-data request.",
        }), 400

    audio_bytes = uploaded.read()
    filename = uploaded.filename or "recording.wav"
    language_code = request.form.get("language_code") or request.form.get("lang") or "hi-IN,en-IN"
    model = request.form.get("model") or "prisma-v3.0"
    output_format = request.form.get("format") or "codemix"
    run_rag = str(request.form.get("run_rag", "false")).lower() in ("true", "1", "yes")

    stt_result = transcribe_speech_gnani(
        audio_bytes=audio_bytes,
        filename=filename,
        language_code=language_code,
        model=model,
        output_format=output_format,
    )
    if stt_result.get("status") == "error":
        code = stt_result.get("error_code", "")
        http_status = 429 if code == "RATE_LIMIT_EXCEEDED" else (504 if code == "API_TIMEOUT" else 400)
        return jsonify(stt_result), http_status

    if run_rag and stt_result.get("transcript"):
        try:
            ctx_raw = request.form.get("context") or "{}"
            context = json.loads(ctx_raw) if isinstance(ctx_raw, str) else {}
        except Exception:
            context = {}
        detected = (stt_result.get("detected_language_code") or language_code or "hi").lower()
        chat_lang = "hi" if "hi" in detected else "en"
        rag_res = voice_agent.ask_rag(stt_result["transcript"], context, lang=chat_lang)
        stt_result["chat"] = {
            "answer": rag_res.get("answer", ""),
            "sources": rag_res.get("sources", []),
            "retrieval_mode": rag_res.get("retrieval_mode", "general"),
            "verified": rag_res.get("verified", True),
            "lang": rag_res.get("lang", chat_lang),
        }

    return jsonify(stt_result)


@app.route("/api/krishisathi/tts", methods=["POST"])
@app.route("/api/voice/tts", methods=["POST"])
def api_gnani_tts():
    """Gnani Timbre v2.5 Text-to-Speech endpoint (proxies JSON to https://api.vachana.ai/api/v1/tts/inference)."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text") or ""
    language = data.get("language") or data.get("lang") or "hi-IN"
    voice = data.get("voice")
    gender = data.get("gender") or "female"
    model = data.get("model") or "timbre-v2.5"
    speed = float(data.get("speed") or 1.0)
    response_format = (data.get("response_format") or "binary").lower()

    tts_result = synthesize_speech_gnani(
        text=text,
        language=language,
        voice=voice,
        gender=gender,
        model=model,
        speed=speed,
    )
    if tts_result.get("status") == "error":
        code = tts_result.get("error_code", "")
        http_status = 429 if code == "RATE_LIMIT_EXCEEDED" else (504 if code == "API_TIMEOUT" else 400)
        return jsonify(tts_result), http_status

    if response_format == "json":
        return jsonify({
            "status": "success",
            "audio_base64": tts_result["audio_base64"],
            "content_type": tts_result["content_type"],
            "model": tts_result["model"],
            "voice": tts_result["voice"],
            "language": tts_result["language"],
        })

    return Response(
        tts_result["audio_bytes"],
        mimetype=tts_result["content_type"],
        headers={
            "X-Gnani-Model": tts_result["model"],
            "X-Gnani-Voice": tts_result["voice"],
            "X-Gnani-Language": tts_result["language"],
        },
    )


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


@app.route("/api/dataset-coverage")
def api_dataset_coverage():
    cov_path = BASE_DIR / "models" / "all_india_coverage_report.json"
    eval_path = BASE_DIR / "models" / "all_india_evaluation_report.json"
    cov_data = {}
    eval_data = {}
    if cov_path.exists():
        with open(cov_path, "r", encoding="utf-8") as f:
            cov_data = json.load(f)
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
    return jsonify({
        "status": "success",
        "coverage": cov_data,
        "evaluation": eval_data,
        "supported_states": CONFIG.supported_states,
        "state_districts": CONFIG.state_districts,
        "all_india_crops": CONFIG.all_india_crops,
        "seasons": CONFIG.seasons,
        "district_crops": CONFIG.district_crops,
        "crop_seasons": CONFIG.crop_seasons,
        "supabase_url": os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or "",
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or "",
    })


@app.route("/api/auth/register", methods=["POST"])
def flask_auth_register():
    data = request.get_json(force=True) or {}
    res = register_user(data)
    return jsonify(res), (400 if res.get("status") == "error" else 200)


@app.route("/api/auth/login", methods=["POST"])
def flask_auth_login():
    data = request.get_json(force=True) or {}
    res = login_user(data.get("email", ""), data.get("password", ""))
    return jsonify(res), (401 if res.get("status") == "error" else 200)


@app.route("/api/auth/logout", methods=["POST"])
def flask_auth_logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        data = request.get_json(silent=True) or {}
        token = data.get("token", "")
    return jsonify(logout_user(token))


@app.route("/api/auth/me")
def flask_auth_me():
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    user = get_session_user(token)
    if not user:
        return jsonify({"status": "error", "message": "Not authenticated or session expired."}), 401
    return jsonify({"status": "success", "user": user})


@app.route("/api/auth/forgot-password", methods=["POST"])
def flask_auth_forgot_password():
    data = request.get_json(force=True) or {}
    return jsonify(create_password_reset_token(data.get("email", "")))


@app.route("/api/auth/reset-password", methods=["POST"])
def flask_auth_reset_password():
    data = request.get_json(force=True) or {}
    res = reset_user_password(data.get("token", ""), data.get("new_password", ""))
    return jsonify(res), (400 if res.get("status") == "error" else 200)


@app.route("/api/admin/users")
def flask_admin_users():
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    user = get_session_user(token)
    if user and user.get("role") not in ("admin", "officer"):
        return jsonify({"status": "error", "message": "Administrator or Officer role required."}), 403
    return jsonify({"status": "success", "users": list_all_users()})


@app.route("/api/schemes/intelligence")
def flask_schemes_intelligence():
    scheme_id = request.args.get("scheme_id")
    state = request.args.get("state")
    district = request.args.get("district")
    return jsonify(get_krishischeme_intelligence(scheme_id=scheme_id, state=state, district=district))


@app.route("/api/schemes/intelligence/upload", methods=["POST"])
def flask_schemes_intelligence_upload():
    data = request.get_json(force=True) or {}
    res = add_admin_scheme_record(data)
    return jsonify(res), (400 if res.get("status") == "error" else 200)


@app.route("/api/insurance/assess", methods=["POST"])
def flask_insurance_assess():
    data = request.get_json(force=True) or {}
    return jsonify(assess_pmfby_claim_eligibility(data))


@app.route("/api/insurance/history")
def flask_insurance_history():
    user_id = request.args.get("user_id")
    state = request.args.get("state")
    return jsonify({"status": "success", "records": get_insurance_history(user_id=user_id, state=state)})


@app.route("/api/nasa/intelligence")
def flask_nasa_intelligence():
    state = request.args.get("state", "Uttar Pradesh")
    district = request.args.get("district", "Meerut")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    return jsonify(fetch_nasa_power_intelligence(
        state=state,
        district=district,
        start_date=start_date,
        end_date=end_date,
        lat=lat,
        lon=lon,
    ))


@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)
