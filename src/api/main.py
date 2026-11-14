"""FastAPI application for KrishiMitra AI backend serving REST APIs and the custom HTML/CSS/JS frontend."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from config.settings import CONFIG, BASE_DIR

# Load environment variables
load_dotenv(BASE_DIR / ".env")
from src.database.db import (
    init_db,
    get_farmer_profile,
    update_farmer_profile,
    get_farmer_plots,
    add_farmer_plot,
    delete_farmer_plot,
    get_historical_yields,
    get_model_benchmarks
)
from src.yield_model.predict import YieldPredictor
from src.advisory.agronomic_rules import AgronomicAdvisor, PersonalisedAdvisoryEngine
from src.schemes.eligibility_engine import SchemeEligibilityEngine
from src.krishisathi.voice_agent import KrishiSathiAgent
from src.krishisathi.gnani_voice import (
    get_gnani_voice_status,
    transcribe_speech_gnani,
    synthesize_speech_gnani,
    parse_raw_multipart_or_json,
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

app = FastAPI(
    title="KrishiMitra AI API",
    description="All-India AI-Powered Agricultural Intelligence and Decision Support Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_static_cache_middleware(request: Request, call_next):
    path = request.url.path.lower()
    if path.endswith((".html", ".js", ".css")) or path in ("/", "/dashboard", "/forecast", "/schemes", "/krishisathi", "/about", "/login"):
        # Remove conditional headers so StaticFiles never returns 304 stale cache
        request.scope["headers"] = [
            (k, v) for (k, v) in request.scope.get("headers", [])
            if k.lower() not in (b"if-none-match", b"if-modified-since")
        ]
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return await call_next(request)

# Initialize engines and database
init_db()
ensure_platform_tables()
predictor = YieldPredictor()
schemes_engine = SchemeEligibilityEngine()
voice_agent = KrishiSathiAgent()

FRONTEND_DIR = BASE_DIR / "frontend"


class FarmerPlotInput(BaseModel):
    crop: str = Field(default="Wheat", example="Wheat")
    district: str = Field(default="Meerut", example="Meerut")
    plot_acres: float = Field(default=2.0, ge=0.1, le=500.0, example=2.0)
    soil_type: str = Field(default="Alluvial (Sandy Loam)", example="Alluvial (Sandy Loam)")
    irrigation_source: str = Field(default="Tube well / Borewell", example="Tube well / Borewell")
    sowing_window: str = Field(default="Timely Sown (Nov 01 - Nov 20)", example="Timely Sown (Nov 01 - Nov 20)")
    seasonal_rainfall_mm: float = Field(default=65.0, ge=0.0, le=5000.0)
    march_max_temp_c: float = Field(default=31.5, ge=5.0, le=52.0)
    nitrogen_kg_acre: float = Field(default=48.0, ge=0.0, le=300.0)
    phosphorus_kg_acre: float = Field(default=22.0, ge=0.0, le=200.0)
    potassium_kg_acre: float = Field(default=15.0, ge=0.0, le=250.0)
    state: str = Field(default="Uttar Pradesh")
    season: Optional[str] = Field(default=None, example="Rabi")
    crop_year: Optional[int] = Field(default=None, example=2025)
    all_india_mode: Optional[bool] = Field(default=False)
    soil_ph: Optional[float] = Field(default=None)
    organic_carbon_pct: Optional[float] = Field(default=None)
    humidity_pct: Optional[float] = Field(default=None)
    growth_stage: Optional[str] = Field(default=None, example="Tillering")
    stage: Optional[str] = None
    sowing_date: Optional[str] = None
    recent_activities: Optional[List[str]] = None
    reported_symptoms: Optional[List[str]] = None
    farmer_id: Optional[str] = Field(default="farmer-001")
    plot_id: Optional[str] = None


class AdvisoryInput(BaseModel):
    crop: str = Field(default="Wheat", example="Wheat")
    district: str = Field(default="Meerut", example="Meerut")
    state: str = Field(default="Uttar Pradesh")
    season: str = Field(default="Rabi")
    growth_stage: Optional[str] = Field(default="Tillering")
    stage: Optional[str] = None
    sowing_window: Optional[str] = "Timely Sown (Nov 01 - Nov 20)"
    sowing_date: Optional[str] = None
    irrigation_source: Optional[str] = "Tube well / Borewell"
    soil_type: Optional[str] = "Alluvial (Sandy Loam)"
    seasonal_rainfall_mm: Optional[float] = 65.0
    march_max_temp_c: Optional[float] = 31.5
    nitrogen_kg_acre: Optional[float] = 48.0
    phosphorus_kg_acre: Optional[float] = 22.0
    potassium_kg_acre: Optional[float] = 15.0
    recent_activities: Optional[List[str]] = None
    reported_symptoms: Optional[List[str]] = None
    farmer_id: Optional[str] = "farmer-001"
    plot_id: Optional[str] = None


class ChatQueryInput(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    lang: Optional[str] = "hi"
    include_tts: Optional[bool] = False
    voice: Optional[str] = None
    gender: Optional[str] = "female"


class NewPlotInput(BaseModel):
    name: str
    village: Optional[str] = "Daurala"
    district: Optional[str] = "Meerut"
    state: Optional[str] = "Uttar Pradesh"
    crop: str = "Wheat"
    acres: float = 2.0
    soil_type: Optional[str] = "Alluvial (Sandy Loam)"
    irrigation_source: Optional[str] = "Tube well / Borewell"
    sowing_date: Optional[str] = None
    sowing_window: Optional[str] = "Timely Sown (Nov 01 - Nov 20)"
    stage: Optional[str] = "Tillering"
    status: Optional[str] = "Active"
    nitrogen_kg_acre: Optional[float] = 48.0
    phosphorus_kg_acre: Optional[float] = 22.0
    potassium_kg_acre: Optional[float] = 15.0
    farmer_id: Optional[str] = "farmer-001"


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "pilot_region": CONFIG.region,
        "database": "SQLite (krishimitra.db)"
    }


@app.get("/api/config")
@app.get("/api/metadata")
@app.get("/api/options")
def get_config():
    """Returns available pilot & All-India choices and baseline defaults for the frontend."""
    return {
        "state": CONFIG.state,
        "supported_states": CONFIG.supported_states,
        "state_districts": CONFIG.state_districts,
        "state_yield_benchmarks": CONFIG.state_yield_benchmarks,
        "region": CONFIG.region,
        "season": CONFIG.season,
        "seasons": CONFIG.seasons,
        "districts": CONFIG.districts,
        "crops": CONFIG.crops,
        "all_india_crops": CONFIG.all_india_crops,
        "district_crops": CONFIG.district_crops,
        "crop_seasons": CONFIG.crop_seasons,
        "soil_types": CONFIG.soil_types,
        "irrigation_sources": CONFIG.irrigation_sources,
        "sowing_windows": [
            "Early Rabi (Oct 15 - Oct 31)",
            "Timely Sown (Nov 01 - Nov 20)",
            "Late Sown (Nov 21 - Dec 15)",
        ],
        "yield_unit": CONFIG.yield_unit,
        "baseline_benchmarks": CONFIG.baseline_yield_benchmarks,
        "supabase_url": os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or "",
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or "",
    }


@app.get("/api/auth/supabase-config")
def get_supabase_config():
    """Returns public Supabase project URL and anon key for client-side Supabase Auth initialization."""
    return {
        "status": "success",
        "supabase_url": os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "",
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or "",
    }


@app.get("/api/states")
def get_states():
    """Returns all supported states, their districts, and state-level yield benchmarks."""
    return {
        "status": "success",
        "supported_states": CONFIG.supported_states,
        "state_districts": CONFIG.state_districts,
        "state_yield_benchmarks": CONFIG.state_yield_benchmarks,
    }


class FarmerUpdateInput(BaseModel):
    name: str = "Tanishka"
    phone: Optional[str] = "+91 98765 43210"
    village: Optional[str] = "Daurala"
    district: str = "Meerut"
    state: str = "Uttar Pradesh"
    preferred_lang: Optional[str] = "en"
    farmer_id: Optional[str] = "farmer-001"


@app.get("/api/farmer")
def get_farmer(farmer_id: str = "farmer-001"):
    """Returns profile and plot overview for the registered farmer."""
    profile = get_farmer_profile(farmer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {"status": "success", "farmer": profile}


@app.put("/api/farmer")
@app.post("/api/farmer")
def update_farmer(payload: FarmerUpdateInput):
    """Updates the registered farmer profile in SQLite."""
    fid = payload.farmer_id or "farmer-001"
    updated = update_farmer_profile(payload.model_dump(), farmer_id=fid)
    return {"status": "success", "farmer": updated}


@app.get("/api/plots")
def list_plots(farmer_id: str = "farmer-001"):
    """Retrieves all registered plots for the given farmer."""
    plots = get_farmer_plots(farmer_id)
    return {"status": "success", "plots": plots}


@app.post("/api/plots", status_code=201)
def create_plot(payload: NewPlotInput):
    """Registers a new plot in the database."""
    plot_dict = payload.model_dump()
    new_plot = add_farmer_plot(plot_dict)
    return {"status": "success", "plot": new_plot}


@app.delete("/api/plots/{plot_id}")
def remove_plot(plot_id: str, farmer_id: str = "farmer-001"):
    """Removes a registered plot from the database."""
    deleted = delete_farmer_plot(plot_id, farmer_id=farmer_id)
    return {"status": "success", "deleted": deleted, "plot_id": plot_id}


@app.get("/api/yield-history")
def get_history(district: str = "Meerut", crop: str = "Wheat", state: Optional[str] = None):
    """Returns real historical yields from official APY database records."""
    records = get_historical_yields(district, crop, state=state)
    return {
        "status": "success",
        "district": district,
        "state": state or "Uttar Pradesh",
        "crop": crop,
        "records_count": len(records),
        "source": "Official Multi-State APY District Records (2012-2023)",
        "records": records
    }


@app.post("/api/analyze")
def analyze_plot(payload: FarmerPlotInput):
    """Single composite API computing yield prediction, stage-specific agronomic advice,

    and eligible government schemes in one fast call.
    """
    farmer_data = payload.model_dump()

    try:
        # 1. Yield Prediction
        yield_output = predictor.predict(farmer_data)

        # 2. Agronomic Advisory
        advisory_output = AgronomicAdvisor.get_advisory(farmer_data, yield_output if yield_output.get("supported") else None)

        # 3. Scheme Eligibility
        schemes_output = schemes_engine.evaluate_eligibility(farmer_data)
        farmer_category = schemes_engine.classify_farmer_category(payload.plot_acres)

        return {
            "status": "success",
            "plot_input": farmer_data,
            "farmer_category": farmer_category,
            "yield": yield_output,
            "advisory": advisory_output,
            "schemes": schemes_output,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict")
def predict_yield(payload: FarmerPlotInput):
    """Point-estimate yield prediction with metric conversions and confidence interval."""
    try:
        return predictor.predict(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard-data")
def get_dashboard_data(
    district: str = "Meerut",
    crop: str = "Wheat",
    state: Optional[str] = None,
    farmer_id: str = "farmer-001",
    plot_id: Optional[str] = None,
    stage: Optional[str] = None,
    growth_stage: Optional[str] = None,
    symptoms: Optional[str] = None,
    activities: Optional[str] = None,
    sowing_date: Optional[str] = None,
    irrigation: Optional[str] = None
):
    """Unified dashboard data aggregator serving real database records,

    live ML model predictions, and telemetry across all 6 supported states.
    """
    # Resolve state from parameter or district lookup
    resolved_state = state
    if not resolved_state:
        for st_name, dists in CONFIG.state_districts.items():
            if any(d.lower() == district.lower() for d in dists):
                resolved_state = st_name
                break
    if not resolved_state:
        resolved_state = "Uttar Pradesh"

    # 1. Farmer Profile & Plots from DB
    farmer = get_farmer_profile(farmer_id) or {
        "name": "Tanishka",
        "district": district,
        "state": resolved_state,
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

    # Resolve stage, symptoms, activities, and irrigation
    active_stage = stage or growth_stage or (selected_plot.get("stage") if selected_plot else "Tillering")
    active_symptoms = [s.strip() for s in symptoms.split(",") if s.strip()] if symptoms else []
    active_activities = [a.strip() for a in activities.split(",") if a.strip()] if activities else []
    active_irrigation = irrigation or (selected_plot.get("irrigation_source") if selected_plot else "Tube well / Borewell")
    active_sowing_date = sowing_date or (selected_plot.get("sowing_date") if selected_plot else None)

    # 2. Live ML model prediction
    plot_input = {
        "crop": crop,
        "district": district,
        "state": resolved_state,
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
    history_records = get_historical_yields(district, crop, state=resolved_state)
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

    return {
        "status": "success",
        "state": resolved_state,
        "district": district,
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
        "state_yield_benchmarks": CONFIG.state_yield_benchmarks,
        "pilot_scope": {
            "supported_states": CONFIG.supported_states,
            "state_districts": CONFIG.state_districts,
            "supported_crops": CONFIG.crops,
            "supported_districts": CONFIG.districts,
            "pilot_region": CONFIG.region
        }
    }


@app.post("/api/advisory")
def post_advisory(payload: AdvisoryInput):
    """Generates structured personalised advisory cards grounded in ICAR & IMD protocols."""
    farmer_data = payload.model_dump()
    yield_out = predictor.predict(farmer_data) if farmer_data.get("crop") in CONFIG.crops else None
    return PersonalisedAdvisoryEngine.generate_advisory(farmer_data, yield_out)


@app.get("/api/advisory")
def get_advisory_endpoint(
    crop: str = "Wheat",
    district: str = "Meerut",
    state: str = "Uttar Pradesh",
    season: str = "Rabi",
    stage: Optional[str] = None,
    growth_stage: Optional[str] = None,
    symptoms: Optional[str] = None,
    activities: Optional[str] = None,
    sowing_window: Optional[str] = "Timely Sown (Nov 01 - Nov 20)",
    sowing_date: Optional[str] = None,
    irrigation_source: Optional[str] = "Tube well / Borewell",
    soil_type: Optional[str] = "Alluvial (Sandy Loam)",
    march_max_temp_c: Optional[float] = 31.5,
    seasonal_rainfall_mm: Optional[float] = 65.0
):
    """GET endpoint for interactive advisory calculation."""
    active_stage = stage or growth_stage or "Tillering"
    active_symptoms = [s.strip() for s in symptoms.split(",") if s.strip()] if symptoms else []
    active_activities = [a.strip() for a in activities.split(",") if a.strip()] if activities else []
    farmer_data = {
        "crop": crop,
        "district": district,
        "state": state,
        "season": season,
        "growth_stage": active_stage,
        "stage": active_stage,
        "sowing_window": sowing_window,
        "sowing_date": sowing_date,
        "irrigation_source": irrigation_source,
        "soil_type": soil_type,
        "march_max_temp_c": march_max_temp_c,
        "seasonal_rainfall_mm": seasonal_rainfall_mm,
        "reported_symptoms": active_symptoms,
        "recent_activities": active_activities
    }
    yield_out = predictor.predict(farmer_data) if crop in CONFIG.crops else None
    return PersonalisedAdvisoryEngine.generate_advisory(farmer_data, yield_out)


@app.get("/api/weather")
def get_weather(
    district: str = "Meerut",
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """Fetches real-time current weather from Open-Meteo for the requested district or coordinates."""
    return fetch_open_meteo_weather(district, lat, lon)


@app.post("/api/krishisathi/chat")
def krishisathi_chat(payload: ChatQueryInput):
    """Processes farmer query using RAG (PDF search -> Web Search fallback -> Verification)."""
    try:
        rag_res = voice_agent.ask_rag(payload.query, payload.context, lang=payload.lang or "hi")
        resp: Dict[str, Any] = {
            "status": "success",
            "answer": rag_res["answer"],
            "sources": rag_res.get("sources", []),
            "retrieval_mode": rag_res.get("retrieval_mode", "general"),
            "verified": rag_res.get("verified", True),
            "lang": rag_res.get("lang", payload.lang or "hi")
        }
        if payload.include_tts and resp["answer"]:
            tts_res = synthesize_speech_gnani(
                text=resp["answer"],
                language="hi-IN" if resp["lang"] == "hi" else "en-IN",
                voice=payload.voice,
                gender=payload.gender or "female",
                model="timbre-v2.5",
            )
            if tts_res.get("status") == "success":
                resp["audio_base64"] = tts_res.get("audio_base64")
                resp["audio_content_type"] = tts_res.get("content_type", "audio/wav")
                resp["tts_model"] = tts_res.get("model", "timbre-v2.5")
                resp["tts_voice"] = tts_res.get("voice")
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/krishisathi/voice-status")
@app.get("/api/voice/status")
def get_voice_status():
    """Returns Gnani.ai voice readiness without exposing API credentials."""
    return get_gnani_voice_status()


@app.post("/api/krishisathi/stt")
@app.post("/api/voice/stt")
async def gnani_speech_to_text(request: Request):
    """Proxies recorded voice to Gnani Prisma v3.0 STT API (`POST https://api.vachana.ai/stt/v3`)."""
    content_type = request.headers.get("content-type", "")
    body_bytes = await request.body()
    audio_bytes, filename, fields = parse_raw_multipart_or_json(content_type, body_bytes)

    if not audio_bytes:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "error_code": "MISSING_AUDIO_FILE",
            "message": "No audio data received. Please record your voice and try again."
        })

    language_code = fields.get("language_code") or fields.get("lang") or "hi-IN,en-IN"
    model = fields.get("model") or "prisma-v3.0"
    output_format = fields.get("format") or "codemix"
    run_rag = str(fields.get("run_rag", "false")).lower() in ("true", "1", "yes")

    result = transcribe_speech_gnani(
        audio_bytes=audio_bytes,
        filename=filename,
        language_code=language_code,
        model=model,
        output_format=output_format,
    )
    if result.get("status") == "error":
        code = result.get("error_code")
        status_code = 429 if code == "RATE_LIMIT_EXCEEDED" else (504 if code == "API_TIMEOUT" else 400)
        return JSONResponse(status_code=status_code, content=result)

    if run_rag and result.get("transcript"):
        try:
            ctx_raw = fields.get("context") or "{}"
            ctx = json.loads(ctx_raw) if isinstance(ctx_raw, str) else (ctx_raw or {})
        except Exception:
            ctx = {}
        detected = (result.get("detected_language_code") or language_code or "hi").lower()
        chat_lang = "hi" if "hi" in detected else "en"
        rag_res = voice_agent.ask_rag(result["transcript"], ctx, lang=chat_lang)
        result["chat"] = {
            "answer": rag_res.get("answer", ""),
            "sources": rag_res.get("sources", []),
            "retrieval_mode": rag_res.get("retrieval_mode", "general"),
            "verified": rag_res.get("verified", True),
            "lang": rag_res.get("lang", chat_lang),
        }

    return result


class TTSRequestInput(BaseModel):
    text: str
    language: Optional[str] = "hi-IN"
    voice: Optional[str] = None
    gender: Optional[str] = "female"
    model: Optional[str] = "timbre-v2.5"
    speed: Optional[float] = 1.0
    response_format: Optional[str] = "binary"


@app.post("/api/krishisathi/tts")
@app.post("/api/voice/tts")
def gnani_text_to_speech(payload: TTSRequestInput):
    """Proxies synthesis to Gnani Timbre v2.5 TTS API (`POST https://api.vachana.ai/api/v1/tts/inference`)."""
    tts_result = synthesize_speech_gnani(
        text=payload.text,
        language=payload.language,
        voice=payload.voice,
        gender=payload.gender or "female",
        model=payload.model or "timbre-v2.5",
        speed=float(payload.speed or 1.0),
    )
    if tts_result.get("status") == "error":
        code = tts_result.get("error_code")
        status_code = 429 if code == "RATE_LIMIT_EXCEEDED" else (504 if code == "API_TIMEOUT" else 400)
        return JSONResponse(status_code=status_code, content=tts_result)

    if (payload.response_format or "").lower() == "json":
        return {
            "status": "success",
            "audio_base64": tts_result["audio_base64"],
            "content_type": tts_result["content_type"],
            "model": tts_result["model"],
            "voice": tts_result["voice"],
            "language": tts_result["language"],
        }

    return Response(
        content=tts_result["audio_bytes"],
        media_type=tts_result["content_type"],
        headers={
            "X-Gnani-Model": tts_result["model"],
            "X-Gnani-Voice": tts_result["voice"],
            "X-Gnani-Language": tts_result["language"],
        }
    )


@app.get("/api/model-summary")
def get_model_summary():
    """Returns the validated model evaluation and benchmark summary."""
    summary_path = BASE_DIR / "models" / "model_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Model summary not found")


@app.get("/api/schemes")
def get_schemes():
    """Returns government schemes list."""
    schemes_path = BASE_DIR / "data" / "schemes" / "central_schemes.json"
    if schemes_path.exists():
        with open(schemes_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# =========================================================================
# NEW ALL-INDIA PLATFORM ENDPOINTS (Auth, Coverage, Scheme Intel, Suraksha, NASA)
# =========================================================================

@app.get("/api/dataset-coverage")
def get_dataset_coverage():
    """Returns comprehensive All-India dataset coverage report and dynamic dropdown metadata."""
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
    return {
        "status": "success",
        "coverage": cov_data,
        "evaluation": eval_data,
        "supported_states": CONFIG.supported_states,
        "state_districts": CONFIG.state_districts,
        "all_india_crops": CONFIG.all_india_crops,
        "seasons": CONFIG.seasons,
        "district_crops": CONFIG.district_crops,
        "crop_seasons": CONFIG.crop_seasons,
    }


@app.post("/api/auth/register")
async def api_auth_register(request: Request):
    data = await request.json()
    res = register_user(data)
    if res.get("status") == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@app.post("/api/auth/login")
async def api_auth_login(request: Request):
    data = await request.json()
    res = login_user(data.get("email") or data.get("identifier") or "", data.get("password", ""))
    if res.get("status") == "error":
        return JSONResponse(status_code=401, content=res)
    return res


@app.post("/api/auth/logout")
async def api_auth_logout(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        try:
            body = await request.json()
            token = body.get("token", "")
        except Exception:
            pass
    return logout_user(token)


@app.get("/api/auth/me")
def api_auth_me(request: Request, token: Optional[str] = None):
    auth_token = token or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    user = get_session_user(auth_token)
    if not user:
        return JSONResponse(status_code=401, content={"status": "error", "message": "Not authenticated or session expired."})
    return {"status": "success", "user": user}


@app.post("/api/auth/forgot-password")
async def api_auth_forgot_password(request: Request):
    data = await request.json()
    return create_password_reset_token(data.get("email") or data.get("identifier") or "")


@app.post("/api/auth/reset-password")
async def api_auth_reset_password(request: Request):
    data = await request.json()
    res = reset_user_password(data.get("token") or data.get("reset_token") or "", data.get("new_password", ""))
    if res.get("status") == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@app.get("/api/admin/users")
def api_admin_users(request: Request, token: Optional[str] = None):
    auth_token = token or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    user = get_session_user(auth_token)
    if user and user.get("role") != "admin":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Administrator role required."})
    return {"status": "success", "users": list_all_users()}


@app.get("/api/schemes/intelligence")
def api_schemes_intelligence(
    scheme_id: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None
):
    """Returns KrishiScheme Intelligence historical beneficiary & financial impact analytics."""
    return get_krishischeme_intelligence(scheme_id=scheme_id, state=state, district=district)


@app.post("/api/schemes/intelligence/upload")
async def api_schemes_intelligence_upload(request: Request):
    """Allows administrators to upload verified government scheme impact records."""
    data = await request.json()
    res = add_admin_scheme_record(data)
    if res.get("status") == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@app.post("/api/insurance/assess")
async def api_insurance_assess(request: Request):
    """KrishiSuraksha AI Crop Insurance (PMFBY) Eligibility & 72-Hour Claim Assessment."""
    data = await request.json()
    return assess_pmfby_claim_eligibility(data)


@app.get("/api/insurance/history")
def api_insurance_history(user_id: Optional[str] = None, state: Optional[str] = None):
    """Returns recorded KrishiSuraksha crop insurance assessments."""
    return {"status": "success", "records": get_insurance_history(user_id=user_id, state=state)}


@app.get("/api/nasa/intelligence")
def api_nasa_intelligence(
    state: str = "Uttar Pradesh",
    district: str = "Meerut",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """Returns NASA POWER Agroclimatology & NASA GIBS Satellite Earth Intelligence."""
    return fetch_nasa_power_intelligence(
        state=state,
        district=district,
        start_date=start_date,
        end_date=end_date,
        lat=lat,
        lon=lon,
    )


@app.get("/forecast")
def serve_forecast_page():
    return FileResponse(FRONTEND_DIR / "forecast.html")


@app.get("/schemes")
def serve_schemes_page():
    return FileResponse(FRONTEND_DIR / "schemes.html")


@app.get("/krishisathi")
def serve_krishisathi_page():
    return FileResponse(FRONTEND_DIR / "krishisathi.html")


@app.get("/about")
def serve_about_page():
    return FileResponse(FRONTEND_DIR / "about.html")


@app.get("/dashboard")
def serve_dashboard_page():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/")
def serve_root_entry():
    """Shows the Login page first whenever a visitor opens the website root."""
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/login")
def serve_login_page():
    return FileResponse(FRONTEND_DIR / "login.html")


# Mount static files for HTML, CSS, JS, images
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
