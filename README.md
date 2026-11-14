# KrishiMitra-AI — All-India AI-Powered Agricultural Intelligence & Decision Support Platform

KrishiMitra-AI is an all-India agricultural decision-support platform combining machine learning crop yield prediction across **35 States & Union Territories, 736 Districts, 72 Crops, and 5 Seasons**, **KrishiScheme Intelligence** (historical government scheme impact analytics), **KrishiSuraksha** (AI-assisted PMFBY crop insurance guidance), **NASA Earth & Weather Intelligence** (NASA POWER agroclimatology + NASA GIBS satellite layers), **Role-Based Authentication**, and the bilingual **KrishiSathi AI Assistant**.

---

## 1. Exact Datasets Integrated

All paths are resolved dynamically from the repository root (`config/settings.py`):

1. **Crop Dataset**: `crops/all_india_all_seasons_crops_dataset(1).csv`
   - **Raw Rows**: 151,289 | **Cleaned Valid Rows**: 149,737 (1,552 rows with missing target yield removed)
   - **Coverage**: 35 States/UTs, 736 Standardized Districts, 72 Crops, 5 Seasons (`Kharif`, `Rabi`, `Summer`, `Winter`, `Whole Year`), Years `2013–2022`.
2. **Soil Dataset**: `soil/all_states_india_soil_dataset(2).csv`
   - **Rows**: 2,975 district-soil observations (`Soil_Type`, `pH`, `Nitrogen_kg_ha`, `Phosphorus_kg_ha`, `Potassium_kg_ha`, `Organic_Carbon_pct`, `Soil_Moisture_pct`, `Moisture_Retention_Capacity`, `Soil_Fertility_Index`).
3. **Weather & Rainfall Dataset**: `weather/all_states_india_weather_and_rainfall_dataset(1).csv`
   - **Rows**: 33,320 daily/seasonal district observations (`Temp_Max_C`, `Temp_Min_C`, `Temp_Avg_C`, `Humidity_Pct`, `Wind_Speed_kmh`, `Rainfall_mm`, `Cloud_Cover_Pct`, `Solar_Radiation_Wm2`, `Evapotranspiration_mm`, `Weather_Condition`).
   - **Leakage Prevention**: Future columns (`Target_Next_Day_Rainfall_mm`, `Target_Next_Day_Temp_Max_C`, `Target_Next_Day_Temp_Min_C`, `Target_Rain_Tomorrow`), `Area_Hectare`, and `Production_Tonnes` are strictly excluded from model input features.

---

## 2. All-India Machine Learning Pipeline & Chronological Validation

- **Chronological Split**:
  - **Train Set (`2013–2020`)**: 117,739 records
  - **Test Set (`2021–2022`)**: 31,998 records
- **Chronological Evaluation Metrics (`2021–2022` Test Split)**:

| Model | Chronological MAE | Chronological RMSE | Chronological R² | Previously Reported R² |
|---|---:|---:|---:|---:|
| **Random Forest (Selected)** | **0.5580** | **1.8437** | **0.9511** | 0.9223 |
| **Decision Tree** | 0.6094 | 2.0109 | 0.9418 | 0.1111 |
| **Linear Regression** | 0.6849 | 2.0897 | 0.9372 | 0.8251 |
| **Gradient Boosting** | 0.5905 | 2.1041 | 0.9363 | 0.8657 |

---

## 3. Core Platform Modules

1. **All-India Crop Yield Prediction (`frontend/forecast.html`, `/api/predict`)**:
   - Dynamic State → District → Crop → Season → Year selection with optional Soil (`N, P, K, pH, OC, Moisture`) and Weather (`Rainfall, Temp, Humidity, Solar`) overrides.
   - Displays yield in **Tonnes/Ha**, **Quintals/Ha**, and **Quintals/Acre**, historical district trends, previous-year comparison, top influencing factors, model evaluation table, and data source transparency.
2. **Role-Based Authentication (`#tab-profile`, `/api/auth/*`)**:
   - Supports **Farmer**, **Agricultural Officer**, and **Administrator** roles with PBKDF2-HMAC-SHA256 password hashing, bearer session tokens, Forgot/Reset Password flow, and protected Admin endpoints.
3. **KrishiScheme Intelligence (`#tab-scheme-intel`, `/api/schemes/intelligence`)**:
   - Verified multi-year beneficiary, approval, and disbursement analytics for **PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, and PM-KUSUM** sourced from official `.gov.in` portals and PIB releases, plus Administrator CSV/JSON dataset upload.
4. **KrishiSuraksha — AI Crop Insurance Assistance (`#tab-suraksha`, `/api/insurance/assess`)**:
   - Evaluates PMFBY claim eligibility, enforces the **72-hour localized calamity intimation rule**, provides a personalized step-by-step claim guide, document checklist, evidence upload reference, and mandatory official disclaimer.
5. **NASA Earth & Weather Intelligence (`#tab-nasa`, `/api/nasa/intelligence`)**:
   - Live integration with **NASA POWER Agroclimatology API** (`T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`) and **NASA GIBS WMTS Satellite Layers** (`MODIS Terra NDVI 8-Day`, `MODIS Terra True Color`, `MODIS Land Surface Temp`, `GPM IMERG Precipitation`).
6. **KrishiSathi AI Assistant (`frontend/krishisathi.html`, `/api/voice-query`)**:
   - Grounded in the All-India ML Engine, Verified Scheme Intelligence, PMFBY Insurance Rules, and NASA Agro-Climatology in English & Hindi.

---

## 4. Setup & Running Instructions

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Configure environment variables
cp .env.example .env

# 3. Rebuild All-India ML artifacts (already pre-built in models/)
python -m src.pipelines.all_india_engine

# 4. Run the FastAPI + Frontend server on port 8000
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000

# 5. Run the automated test suite
python -m unittest discover -s tests -v
```

Open **`http://127.0.0.1:8000`** in your browser.
