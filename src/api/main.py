"""FastAPI application for KrishiMitra AI backend serving REST APIs and the custom HTML/CSS/JS frontend."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
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

app = FastAPI(
    title="KrishiMitra AI API",
    description="Plot-level yield forecasting, precision advisory, and scheme delivery with KrishiSathi voice assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines and database
init_db()
predictor = YieldPredictor()
schemes_engine = SchemeEligibilityEngine()
voice_agent = KrishiSathiAgent()

FRONTEND_DIR = BASE_DIR / "frontend"


class FarmerPlotInput(BaseModel):
    crop: str = Field(default="Wheat", example="Wheat")
    district: str = Field(default="Meerut", example="Meerut")
    plot_acres: float = Field(default=2.0, ge=0.1, le=50.0, example=2.0)
    soil_type: str = Field(default="Alluvial (Sandy Loam)", example="Alluvial (Sandy Loam)")
    irrigation_source: str = Field(default="Tube well / Borewell", example="Tube well / Borewell")
    sowing_window: str = Field(default="Timely Sown (Nov 01 - Nov 20)", example="Timely Sown (Nov 01 - Nov 20)")
    seasonal_rainfall_mm: float = Field(default=65.0, ge=0.0, le=500.0)
    march_max_temp_c: float = Field(default=31.5, ge=15.0, le=48.0)
    nitrogen_kg_acre: float = Field(default=48.0, ge=0.0, le=150.0)
    phosphorus_kg_acre: float = Field(default=22.0, ge=0.0, le=100.0)
    potassium_kg_acre: float = Field(default=15.0, ge=0.0, le=80.0)
    state: str = Field(default="Uttar Pradesh")
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
    context: Dict[str, Any]
    lang: Optional[str] = "hi"


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
def get_config():
    """Returns available pilot choices and baseline defaults for the frontend."""
    return {
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
    }


@app.get("/api/farmer")
def get_farmer(farmer_id: str = "farmer-001"):
    """Returns profile and plot overview for the registered farmer."""
    profile = get_farmer_profile(farmer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {"status": "success", "farmer": profile}


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


@app.get("/api/yield-history")
def get_history(district: str = "Meerut", crop: str = "Wheat"):
    """Returns real historical yields from official APY database records."""
    records = get_historical_yields(district, crop)
    return {
        "status": "success",
        "district": district,
        "crop": crop,
        "records_count": len(records),
        "source": "Official Uttar Pradesh APY District Records (2012-2023)",
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

    live ML model predictions, and telemetry.
    """
    # 1. Farmer Profile & Plots from DB
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

    return {
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
    """Processes farmer query in Hindi or English, returning a grounded voice answer."""
    try:
        answer = voice_agent.ask(payload.query, payload.context, lang=payload.lang or "hi")
        return {"status": "success", "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/model-summary")
def serve_model_summary_page():
    return FileResponse(FRONTEND_DIR / "model-summary.html")


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


# Mount static files for HTML, CSS, JS, images
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
