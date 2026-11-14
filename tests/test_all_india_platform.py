"""Comprehensive Unit & Integration Tests for the All-India KrishiMitra-AI Platform."""
from __future__ import annotations

import unittest
import uuid

from fastapi.testclient import TestClient

from config.settings import (
    CROP_DATASET_PATH as ALL_INDIA_CROP_DATASET_FILE,
    SOIL_DATASET_PATH as ALL_INDIA_SOIL_DATASET_FILE,
    WEATHER_DATASET_PATH as ALL_INDIA_WEATHER_DATASET_FILE,
)
from src.api.main import app


class TestAllIndiaPlatform(unittest.TestCase):
    """End-to-end verification of All-India ML, Auth, Schemes, Insurance, and NASA modules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_01_exact_dataset_filenames_exist(self) -> None:
        """Verify exact dataset filenames required by Section 2 of the specification."""
        self.assertEqual(
            ALL_INDIA_CROP_DATASET_FILE.name,
            "all_india_all_seasons_crops_dataset(1).csv",
        )
        self.assertEqual(
            ALL_INDIA_SOIL_DATASET_FILE.name,
            "all_states_india_soil_dataset(2).csv",
        )
        self.assertEqual(
            ALL_INDIA_WEATHER_DATASET_FILE.name,
            "all_states_india_weather_and_rainfall_dataset(1).csv",
        )
        self.assertTrue(ALL_INDIA_CROP_DATASET_FILE.exists(), "Crop dataset missing")
        self.assertTrue(ALL_INDIA_SOIL_DATASET_FILE.exists(), "Soil dataset missing")
        self.assertTrue(ALL_INDIA_WEATHER_DATASET_FILE.exists(), "Weather dataset missing")

    def test_02_dataset_coverage_and_options_api(self) -> None:
        """Verify /api/dataset-coverage and /api/options expose all 35 States/UTs and 72 crops."""
        cov_resp = self.client.get("/api/dataset-coverage")
        self.assertEqual(cov_resp.status_code, 200)
        cov = cov_resp.json()
        self.assertEqual(cov["status"], "success")
        self.assertGreaterEqual(len(cov["supported_states"]), 35)
        self.assertGreaterEqual(len(cov["all_india_crops"]), 70)
        self.assertIn("coverage", cov)
        self.assertIn("evaluation", cov)

        opt_resp = self.client.get("/api/options")
        self.assertEqual(opt_resp.status_code, 200)
        opt = opt_resp.json()
        self.assertGreaterEqual(len(opt["supported_states"]), 35)
        self.assertGreaterEqual(len(opt["crops"]), 70)
        self.assertIn("Kharif", opt["seasons"])
        self.assertIn("Rabi", opt["seasons"])

    def test_03_all_india_crop_yield_prediction(self) -> None:
        """Verify All-India crop yield prediction across diverse states, crops, and seasons."""
        payload = {
            "state": "Maharashtra",
            "district": "Pune",
            "crop": "Rice",
            "season": "Kharif",
            "plot_acres": 2.5,
            "all_india_mode": True,
        }
        resp = self.client.post("/api/predict", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(data.get("supported"))
        self.assertGreater(data["predicted_yield_tonne_per_ha"], 0)
        self.assertGreater(data["predicted_yield_q_ha"], 0)
        self.assertGreater(data["predicted_yield_per_acre"], 0)
        self.assertIn("soil_conditions", data)
        self.assertIn("weather_conditions", data)
        self.assertIn("historical_trends", data)
        self.assertIn("previous_year_comparison", data)
        self.assertIn("important_factors", data)
        self.assertIn("model_evaluation", data)
        self.assertIn("data_availability", data)

    def test_04_authentication_and_rbac_workflow(self) -> None:
        """Verify Registration, Login, Profile, Forgot/Reset Password, and RBAC."""
        unique_email = f"officer_{uuid.uuid4().hex[:8]}@krishimitra.in"
        reg_resp = self.client.post(
            "/api/auth/register",
            json={
                "name": "Dr. Rajesh Sharma",
                "email": unique_email,
                "phone": "9876543210",
                "password": "SecurePassword123!",
                "role": "officer",
                "state": "Madhya Pradesh",
                "district": "Indore",
            },
        )
        self.assertEqual(reg_resp.status_code, 200)
        reg_data = reg_resp.json()
        self.assertEqual(reg_data["status"], "success")
        token = reg_data["token"]
        self.assertEqual(reg_data["user"]["role"], "officer")

        # Verify /api/auth/me
        me_resp = self.client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["user"]["email"], unique_email)

        # Verify Forgot + Reset password flow
        forgot_resp = self.client.post(
            "/api/auth/forgot-password", json={"email": unique_email}
        )
        self.assertEqual(forgot_resp.status_code, 200)
        reset_token = forgot_resp.json().get("reset_token")
        self.assertTrue(reset_token)

        reset_resp = self.client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "NewSecurePassword456!"},
        )
        self.assertEqual(reset_resp.status_code, 200)

        # Login with new password
        login_resp = self.client.post(
            "/api/auth/login",
            json={"email": unique_email, "password": "NewSecurePassword456!"},
        )
        self.assertEqual(login_resp.status_code, 200)
        new_token = login_resp.json()["token"]

        # Verify Agricultural Officer cannot access Administrator user list
        admin_check = self.client.get(
            "/api/admin/users", headers={"Authorization": f"Bearer {new_token}"}
        )
        self.assertEqual(admin_check.status_code, 403)

    def test_05_krishischeme_intelligence(self) -> None:
        """Verify KrishiScheme Intelligence module returns verified multi-year impact data."""
        resp = self.client.get("/api/schemes/intelligence?state=Uttar%20Pradesh")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["schemes"]), 6)
        short_names = {s["short_name"] for s in data["schemes"]}
        for expected in ["PM-KISAN", "PMFBY", "KCC", "Soil Health Card", "PMKSY", "PM-KUSUM"]:
            self.assertIn(expected, short_names)
        self.assertIn("Historical data unavailable.", data["data_integrity_note"])

    def test_06_krishisuraksha_crop_insurance_4_statuses(self) -> None:
        """Verify KrishiSuraksha PMFBY assessment returns exact 4 statuses and 72-hour rule."""
        valid_statuses = {
            "Potentially eligible.",
            "More information required.",
            "Not eligible under currently available rules.",
            "Eligibility cannot be verified with available information.",
        }

        # Case 1: Potentially eligible (within 72h, enrolled, valid loss cause)
        r1 = self.client.post(
            "/api/insurance/assess",
            json={
                "farmer_name": "Ramesh Kumar",
                "state": "Uttar Pradesh",
                "district": "Meerut",
                "crop": "Wheat",
                "season": "Rabi",
                "land_acres": 2.0,
                "damage_type": "Hailstorm",
                "hours_since_damage": 24,
                "enrolled_pmfby": "yes",
            },
        )
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        self.assertEqual(d1["eligibility_status"], "Potentially eligible.")
        self.assertIn(d1["eligibility_status"], valid_statuses)
        self.assertTrue(d1["within_72_hour_window"])
        self.assertIn("final claim approval depends on official", d1["disclaimer"].lower())

        # Case 2: Not eligible (not enrolled in PMFBY)
        r2 = self.client.post(
            "/api/insurance/assess",
            json={
                "state": "Uttar Pradesh",
                "district": "Meerut",
                "crop": "Wheat",
                "season": "Rabi",
                "land_acres": 2.0,
                "damage_type": "Flood",
                "hours_since_damage": 24,
                "enrolled_pmfby": "no",
            },
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(
            r2.json()["eligibility_status"],
            "Not eligible under currently available rules.",
        )

        # Case 3: More information required (missing Aadhaar / Bank docs)
        r3 = self.client.post(
            "/api/insurance/assess",
            json={
                "state": "Uttar Pradesh",
                "district": "Meerut",
                "crop": "Wheat",
                "season": "Rabi",
                "land_acres": 2.0,
                "damage_type": "Drought",
                "hours_since_damage": 36,
                "enrolled_pmfby": "yes",
                "has_aadhaar": False,
                "has_bank_passbook": False,
            },
        )
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["eligibility_status"], "More information required.")

        # Case 4: Eligibility cannot be verified (enrollment unknown)
        r4 = self.client.post(
            "/api/insurance/assess",
            json={
                "state": "Uttar Pradesh",
                "district": "Meerut",
                "crop": "Wheat",
                "season": "Rabi",
                "land_acres": 2.0,
                "damage_type": "Hailstorm",
                "hours_since_damage": 20,
                "enrolled_pmfby": "unknown",
            },
        )
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(
            r4.json()["eligibility_status"],
            "Eligibility cannot be verified with available information.",
        )

    def test_07_nasa_earth_intelligence(self) -> None:
        """Verify NASA Earth & Weather Intelligence endpoint returns GIBS layers & agro-indicators."""
        resp = self.client.get(
            "/api/nasa/intelligence?state=Uttar%20Pradesh&district=Meerut"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("gibs_satellite_layers", data)
        self.assertGreaterEqual(len(data["gibs_satellite_layers"]), 4)
        self.assertIn("agricultural_indicators", data)
        self.assertGreaterEqual(len(data["agricultural_indicators"]), 3)
        self.assertIn("scientific_disclaimer", data)

    def test_08_supabase_auth_route_protection_and_netlify_config(self) -> None:
        """Verify Login page shown first at root, Supabase auth guard on all pages, and Netlify routing."""
        from config.settings import BASE_DIR

        # 1. Root URL "/" shows the Login page first
        root_resp = self.client.get("/")
        self.assertEqual(root_resp.status_code, 200)
        self.assertIn("Select your identity", root_resp.text)
        self.assertIn("supabase_auth.js", root_resp.text)

        # 2. Supabase config endpoint
        sb_resp = self.client.get("/api/auth/supabase-config")
        self.assertEqual(sb_resp.status_code, 200)
        sb_data = sb_resp.json()
        self.assertEqual(sb_data["status"], "success")
        self.assertIn("supabase_url", sb_data)
        self.assertIn("supabase_anon_key", sb_data)

        # 3. Verify all internal pages include supabase_auth.js route protection & Logout button
        frontend_dir = BASE_DIR / "frontend"
        for page_name in ["dashboard.html", "index.html", "forecast.html", "schemes.html", "krishisathi.html", "about.html"]:
            page_path = frontend_dir / page_name
            self.assertTrue(page_path.exists(), f"Missing {page_name}")
            html = page_path.read_text(encoding="utf-8")
            self.assertIn("supabase_auth.js", html, f"{page_name} missing supabase_auth.js guard")
            self.assertIn("data-km-logout", html, f"{page_name} missing functional Logout button")

        # 4. Verify Netlify configuration files exist
        self.assertTrue((BASE_DIR / "netlify.toml").exists(), "netlify.toml missing")
        self.assertTrue((frontend_dir / "_redirects").exists(), "frontend/_redirects missing")


if __name__ == "__main__":
    unittest.main()
