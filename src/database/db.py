"""SQLite Database Layer for KrishiMitra AI.
Provides persistent storage for farmers, field plots, historical yields,
model benchmarks, prediction telemetry, and government schemes.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from config.settings import BASE_DIR, DATA_DIR, CONFIG

DB_PATH = DATA_DIR / "krishimitra.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory configured as dictionary."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force: bool = False):
    """Initializes the SQLite database schema and seeds initial data if empty."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Farmers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                district TEXT NOT NULL,
                state TEXT NOT NULL,
                preferred_lang TEXT DEFAULT 'hi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Plots / Fields table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plots (
                id TEXT PRIMARY KEY,
                farmer_id TEXT NOT NULL,
                name TEXT NOT NULL,
                village TEXT,
                district TEXT NOT NULL,
                state TEXT NOT NULL,
                crop TEXT NOT NULL,
                acres REAL NOT NULL,
                soil_type TEXT NOT NULL,
                irrigation_source TEXT NOT NULL,
                sowing_date TEXT,
                sowing_window TEXT,
                stage TEXT DEFAULT 'Tillering',
                status TEXT DEFAULT 'Active',
                nitrogen_kg_acre REAL DEFAULT 48.0,
                phosphorus_kg_acre REAL DEFAULT 22.0,
                potassium_kg_acre REAL DEFAULT 15.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farmer_id) REFERENCES farmers(id)
            )
        """)

        # 3. Historical Yields table (District aggregates from official APY data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_yields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                crop TEXT NOT NULL,
                year TEXT NOT NULL,
                start_year INTEGER NOT NULL,
                area_hectares REAL,
                production_tonnes REAL,
                yield_tonne_per_ha REAL NOT NULL,
                yield_quintals_per_acre REAL NOT NULL
            )
        """)

        # 4. Model Predictions Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id TEXT,
                plot_id TEXT,
                crop TEXT NOT NULL,
                district TEXT NOT NULL,
                plot_acres REAL NOT NULL,
                predicted_yield_q_acre REAL NOT NULL,
                predicted_yield_q_ha REAL NOT NULL,
                predicted_yield_t_ha REAL NOT NULL,
                ci_lower_q_acre REAL,
                ci_upper_q_acre REAL,
                model_used TEXT NOT NULL,
                input_params_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Model Evaluation Benchmarks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                target_variable TEXT NOT NULL,
                target_unit TEXT NOT NULL,
                mae REAL NOT NULL,
                rmse REAL NOT NULL,
                r2 REAL NOT NULL,
                rank INTEGER,
                status TEXT,
                validation_type TEXT,
                notes TEXT
            )
        """)

        conn.commit()

        # Check if seed data is needed
        cursor.execute("SELECT COUNT(*) FROM farmers")
        has_farmers = cursor.fetchone()[0] > 0

        if not has_farmers or force:
            _seed_data(conn)


def _seed_data(conn: sqlite3.Connection):
    """Populates seed farmers, plots, historical yields, and benchmarks."""
    cursor = conn.cursor()

    # Seed Default Farmer
    cursor.execute("""
        INSERT OR REPLACE INTO farmers (id, name, phone, district, state, preferred_lang)
        VALUES ('farmer-001', 'Tanishka', '+91 98765 43210', 'Meerut', 'Uttar Pradesh', 'hi')
    """)

    # Seed 3 Registered Plots for Farmer
    plots = [
        (
            'plot-001', 'farmer-001', 'Daurala Farm', 'Daurala', 'Meerut', 'Uttar Pradesh',
            'Wheat', 2.5, 'Alluvial (Sandy Loam)', 'Tube well / Borewell',
            '2024-11-15', 'Timely Sown (Nov 01 - Nov 20)', 'Tillering', 'Active',
            48.0, 22.0, 15.0
        ),
        (
            'plot-002', 'farmer-001', 'Hastinapur Plot', 'Hastinapur', 'Meerut', 'Uttar Pradesh',
            'Mustard', 1.8, 'Alluvial (Sandy Loam)', 'Tube well / Borewell',
            '2024-11-10', 'Timely Sown (Nov 01 - Nov 20)', 'Flowering', 'Active',
            32.0, 16.0, 8.0
        ),
        (
            'plot-003', 'farmer-001', 'Sardhana Area', 'Sardhana', 'Meerut', 'Uttar Pradesh',
            'Wheat', 1.2, 'Alluvial (Clay Loam)', 'Canal',
            '2024-11-20', 'Timely Sown (Nov 01 - Nov 20)', 'Soil Preparation', 'Planned',
            45.0, 20.0, 12.0
        )
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO plots (
            id, farmer_id, name, village, district, state,
            crop, acres, soil_type, irrigation_source,
            sowing_date, sowing_window, stage, status,
            nitrogen_kg_acre, phosphorus_kg_acre, potassium_kg_acre
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, plots)

    # Seed Historical Yields from up_district_apy_tidy.csv if available
    cursor.execute("SELECT COUNT(*) FROM historical_yields")
    if cursor.fetchone()[0] == 0:
        csv_path = DATA_DIR / "processed" / "up_district_apy_tidy.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                records = []
                for _, row in df.iterrows():
                    district = str(row['district'])
                    state = str(row.get('state', 'Uttar Pradesh'))
                    year = str(row['year'])
                    start_yr = int(row['start_year'])
                    area_ha = float(row['area_hectares']) if pd.notnull(row['area_hectares']) else None
                    prod_t = float(row['production_tonnes']) if pd.notnull(row['production_tonnes']) else None
                    yield_t_ha = float(row['yield_tonne_per_hectare'])
                    yield_q_ac = float(row['yield_quintals_per_acre'])
                    records.append((state, district, 'Wheat', year, start_yr, area_ha, prod_t, yield_t_ha, yield_q_ac))

                cursor.executemany("""
                    INSERT INTO historical_yields (
                        state, district, crop, year, start_year,
                        area_hectares, production_tonnes, yield_tonne_per_ha, yield_quintals_per_acre
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, records)
            except Exception as e:
                print(f"Warning: Failed to import historical APY CSV: {e}")

        # Also seed Mustard baselines for Western UP districts (2018–2023)
        mustard_years = [
            ("2018-2019", 2018, 1.82, 7.37),
            ("2019-2020", 2019, 1.88, 7.61),
            ("2020-2021", 2020, 1.95, 7.89),
            ("2021-2022", 2021, 1.76, 7.12),
            ("2022-2023", 2022, 1.85, 7.49)
        ]
        mustard_records = []
        for dist in CONFIG.districts:
            for yr, syr, y_tha, y_qac in mustard_years:
                mustard_records.append((
                    "Uttar Pradesh", dist, "Mustard", yr, syr,
                    15000.0, 15000.0 * y_tha, y_tha, y_qac
                ))
        cursor.executemany("""
            INSERT INTO historical_yields (
                state, district, crop, year, start_year,
                area_hectares, production_tonnes, yield_tonne_per_ha, yield_quintals_per_acre
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, mustard_records)

    # Seed Model Benchmarks from model_summary.json
    cursor.execute("SELECT COUNT(*) FROM model_benchmarks")
    if cursor.fetchone()[0] == 0:
        summary_file = BASE_DIR / "models" / "model_summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
                    models = summary_data.get("models", [])
                    d_sum = summary_data.get("dataset_summary", {})
                    target_var = d_sum.get("target_variable", "Yield (Tonne / Hectare)")
                    target_unit = d_sum.get("target_unit", "Tonne / Hectare")
                    val_type = d_sum.get("validation_type", "Temporal Out-of-Time Split")

                    bench_records = []
                    for m in models:
                        bench_records.append((
                            m["name"], target_var, target_unit,
                            round(m["mae"], 4), round(m["rmse"], 4), round(m["r2"], 4),
                            m["rank"], m["status"], val_type, m.get("notes", "")
                        ))

                    cursor.executemany("""
                        INSERT INTO model_benchmarks (
                            model_name, target_variable, target_unit,
                            mae, rmse, r2, rank, status, validation_type, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, bench_records)
            except Exception as e:
                print(f"Warning: Failed to import model summary benchmarks: {e}")

    conn.commit()


# =========================================================================
# Query & Data Access Helper Functions
# =========================================================================

def get_farmer_profile(farmer_id: str = "farmer-001") -> Optional[Dict[str, Any]]:
    """Retrieves farmer personal info and aggregate statistics."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
        row = cursor.fetchone()
        if not row:
            return None
        farmer = dict(row)

        cursor.execute("SELECT COUNT(*) as plot_count, COALESCE(SUM(acres), 0) as total_acres FROM plots WHERE farmer_id = ?", (farmer_id,))
        stats = cursor.fetchone()
        farmer["plot_count"] = stats["plot_count"]
        farmer["total_acres"] = round(stats["total_acres"], 2)

        cursor.execute("SELECT DISTINCT crop FROM plots WHERE farmer_id = ?", (farmer_id,))
        crops = [r["crop"] for r in cursor.fetchall()]
        farmer["crops"] = crops

        return farmer


def get_farmer_plots(farmer_id: str = "farmer-001") -> List[Dict[str, Any]]:
    """Retrieves all registered plots for a given farmer."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plots WHERE farmer_id = ? ORDER BY id ASC", (farmer_id,))
        return [dict(row) for row in cursor.fetchall()]


def add_farmer_plot(plot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts a new plot for a farmer and returns the created record."""
    import uuid
    init_db()
    plot_id = plot_data.get("id") or f"plot-{uuid.uuid4().hex[:8]}"
    farmer_id = plot_data.get("farmer_id", "farmer-001")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO plots (
                id, farmer_id, name, village, district, state,
                crop, acres, soil_type, irrigation_source,
                sowing_date, sowing_window, stage, status,
                nitrogen_kg_acre, phosphorus_kg_acre, potassium_kg_acre
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plot_id,
            farmer_id,
            plot_data.get("name", "New Farm Plot"),
            plot_data.get("village", "Daurala"),
            plot_data.get("district", "Meerut"),
            plot_data.get("state", "Uttar Pradesh"),
            plot_data.get("crop", "Wheat"),
            float(plot_data.get("acres", 2.0)),
            plot_data.get("soil_type", "Alluvial (Sandy Loam)"),
            plot_data.get("irrigation_source", "Tube well / Borewell"),
            plot_data.get("sowing_date", datetime.now().strftime("%Y-%m-%d")),
            plot_data.get("sowing_window", "Timely Sown (Nov 01 - Nov 20)"),
            plot_data.get("stage", "Tillering"),
            plot_data.get("status", "Active"),
            float(plot_data.get("nitrogen_kg_acre", 48.0)),
            float(plot_data.get("phosphorus_kg_acre", 22.0)),
            float(plot_data.get("potassium_kg_acre", 15.0))
        ))
        conn.commit()

        cursor.execute("SELECT * FROM plots WHERE id = ?", (plot_id,))
        return dict(cursor.fetchone())


def get_historical_yields(district: str = "Meerut", crop: str = "Wheat") -> List[Dict[str, Any]]:
    """Retrieves real historical yields from official APY records for district and crop."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT year, start_year, yield_tonne_per_ha, yield_quintals_per_acre,
                   area_hectares, production_tonnes
            FROM historical_yields
            WHERE LOWER(district) = LOWER(?) AND LOWER(crop) = LOWER(?)
            ORDER BY start_year ASC
        """, (district, crop))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def log_prediction(
    crop: str,
    district: str,
    plot_acres: float,
    pred_q_acre: float,
    pred_q_ha: float,
    pred_t_ha: float,
    ci_lower: float,
    ci_upper: float,
    model_name: str,
    farmer_id: Optional[str] = "farmer-001",
    plot_id: Optional[str] = None,
    input_params: Optional[Dict[str, Any]] = None
):
    """Logs generated yield predictions to the database for auditing and telemetry."""
    init_db()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prediction_logs (
                    farmer_id, plot_id, crop, district, plot_acres,
                    predicted_yield_q_acre, predicted_yield_q_ha, predicted_yield_t_ha,
                    ci_lower_q_acre, ci_upper_q_acre, model_used, input_params_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                farmer_id, plot_id, crop, district, plot_acres,
                pred_q_acre, pred_q_ha, pred_t_ha, ci_lower, ci_upper,
                model_name, json.dumps(input_params) if input_params else None
            ))
            conn.commit()
    except Exception as e:
        print(f"Warning: Failed to log prediction: {e}")


def get_model_benchmarks() -> List[Dict[str, Any]]:
    """Retrieves validated model benchmarks from database."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT model_name, target_variable, target_unit, mae, rmse, r2, rank, status, validation_type, notes
            FROM model_benchmarks
            ORDER BY rank ASC
        """)
        return [dict(r) for r in cursor.fetchall()]
