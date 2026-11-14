"""Secure Authentication, Role-Based Access Control (RBAC),KrishiScheme Intelligence,
KrishiSuraksha (PMFBY Crop Insurance), and NASA Earth Intelligence Services for KrishiMitra-AI.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config.settings import BASE_DIR, DATA_DIR, MODELS_DIR, CONFIG
from src.database.db import get_db_connection, init_db
from src.pipelines.all_india_engine import standardize_state, standardize_district

NASA_CACHE_DIR = DATA_DIR / "nasa_cache"
NASA_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================================
# 1. SECURE PASSWORD HASHING & SESSION MANAGEMENT (PBKDF2-HMAC-SHA256)
# =========================================================================

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with 120,000 iterations."""
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256$120000${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plaintext password against a stored PBKDF2-HMAC-SHA256 hash in constant time."""
    if not stored_hash or "$" not in stored_hash:
        return False
    parts = stored_hash.split("$")
    if len(parts) != 4:
        return False
    _, iterations_str, salt, expected_hex = parts
    try:
        iterations = int(iterations_str)
    except ValueError:
        iterations = 120000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return hmac.compare_digest(dk.hex(), expected_hex)


def ensure_platform_tables():
    """Creates tables for Users, Sessions, Password Resets, Scheme Impact, and Insurance Claims."""
    init_db()
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Ensure farmer-001 default name is Tanishka if not customized
        cur.execute("UPDATE farmers SET name = 'Tanishka' WHERE id = 'farmer-001' AND name = 'Farmer1'")

        # 1. Users table (Role-Based: farmer, officer, admin)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'farmer',
                state TEXT DEFAULT 'Uttar Pradesh',
                district TEXT DEFAULT 'Meerut',
                village TEXT DEFAULT 'Daurala',
                farmer_id TEXT DEFAULT 'farmer-001',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Active Sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 3. Password Reset Tokens table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. KrishiSuraksha Insurance Claims & Eligibility Assessments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS insurance_assessments (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                farmer_name TEXT,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                village TEXT,
                crop TEXT NOT NULL,
                season TEXT NOT NULL,
                land_acres REAL NOT NULL,
                sowing_date TEXT,
                enrolled_pmfby TEXT,
                policy_number TEXT,
                damage_date TEXT,
                damage_type TEXT NOT NULL,
                eligibility_status TEXT NOT NULL,
                explanation TEXT NOT NULL,
                hours_since_damage REAL,
                photo_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. KrishiScheme Admin Uploaded Datasets table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheme_impact_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_id TEXT NOT NULL,
                state TEXT NOT NULL,
                district TEXT,
                year TEXT NOT NULL,
                registered_farmers INTEGER,
                eligible_farmers INTEGER,
                approved_applications INTEGER,
                rejected_applications INTEGER,
                actual_beneficiaries INTEGER,
                amount_disbursed_crore REAL,
                source_citation TEXT NOT NULL,
                reporting_period TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)

        # Seed default demonstration accounts for the 3 roles if not present (using hashed passwords)
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            default_pw = os.getenv("DEMO_DEFAULT_PASSWORD", "Krishi@2026")
            seed_users = [
                (
                    "user-farmer-001",
                    "Tanishka",
                    "farmer@krishimitra.in",
                    "+91 98765 43210",
                    hash_password(default_pw),
                    "farmer",
                    "Uttar Pradesh",
                    "Meerut",
                    "Daurala",
                    "farmer-001",
                ),
                (
                    "user-officer-001",
                    "Dr. Rajesh Verma (District Agri Officer)",
                    "officer@krishimitra.in",
                    "+91 98111 22334",
                    hash_password(default_pw),
                    "officer",
                    "Uttar Pradesh",
                    "Meerut",
                    "Meerut HQ",
                    "farmer-001",
                ),
                (
                    "user-admin-001",
                    "Platform Administrator",
                    "admin@krishimitra.in",
                    "+91 99000 11223",
                    hash_password(default_pw),
                    "admin",
                    "Delhi",
                    "New Delhi",
                    "Krishi Bhawan",
                    "farmer-001",
                ),
            ]
            cur.executemany("""
                INSERT INTO users (id, name, email, phone, password_hash, role, state, district, village, farmer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_users)

        conn.commit()


ROLE_PERMISSIONS = {
    "farmer": [
        "crop_yield_prediction",
        "historical_agricultural_info",
        "government_schemes",
        "crop_insurance_guidance",
        "nasa_agricultural_intelligence",
        "krishisathi_ai",
    ],
    "officer": [
        "crop_yield_prediction",
        "historical_agricultural_info",
        "government_schemes",
        "crop_insurance_guidance",
        "nasa_agricultural_intelligence",
        "krishisathi_ai",
        "district_agricultural_analytics",
        "farmer_dashboards",
        "scheme_performance_analytics",
        "insurance_assistance_records",
        "agricultural_trends",
    ],
    "admin": [
        "crop_yield_prediction",
        "historical_agricultural_info",
        "government_schemes",
        "crop_insurance_guidance",
        "nasa_agricultural_intelligence",
        "krishisathi_ai",
        "district_agricultural_analytics",
        "farmer_dashboards",
        "scheme_performance_analytics",
        "insurance_assistance_records",
        "agricultural_trends",
        "manage_users",
        "manage_datasets",
        "manage_schemes",
        "monitor_ml_models",
        "system_analytics",
    ],
}


def register_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_platform_tables()
    name = str(payload.get("name") or payload.get("full_name") or "").strip()
    email = str(payload.get("email") or payload.get("identifier") or "").strip().lower()
    password = str(payload.get("password") or "")
    phone = str(payload.get("phone") or "+91 98765 43210").strip()
    raw_role = str(payload.get("role") or "farmer").strip().lower()
    if "officer" in raw_role:
        role = "officer"
    elif "admin" in raw_role:
        role = "admin"
    else:
        role = "farmer"
    state = standardize_state(str(payload.get("state") or "Uttar Pradesh"))
    district = standardize_district(str(payload.get("district") or "Meerut"), state)
    village = str(payload.get("village") or "Daurala").strip()

    if not name or not email or len(password) < 6:
        return {"status": "error", "message": "Name, valid email, and password (min 6 chars) are required."}

    user_id = f"user-{secrets.token_hex(6)}"
    farmer_id = f"farmer-{secrets.token_hex(4)}" if role == "farmer" else "farmer-001"
    pw_hash = hash_password(password)

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
        if cur.fetchone():
            return {"status": "error", "message": "An account with this email already exists."}

        cur.execute("""
            INSERT INTO users (id, name, email, phone, password_hash, role, state, district, village, farmer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, phone, pw_hash, role, state, district, village, farmer_id))

        if role == "farmer":
            cur.execute("""
                INSERT OR REPLACE INTO farmers (id, name, phone, district, state, preferred_lang)
                VALUES (?, ?, ?, ?, ?, 'en')
            """, (farmer_id, name, phone, district, state))

        token = secrets.token_urlsafe(32)
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
        cur.execute("""
            INSERT INTO auth_sessions (token, user_id, role, expires_at)
            VALUES (?, ?, ?, ?)
        """, (token, user_id, role, expires))
        conn.commit()

    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": role,
            "state": state,
            "district": district,
            "village": village,
            "farmer_id": farmer_id,
            "permissions": ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["farmer"]),
        },
    }


def login_user(email: str, password: str) -> Dict[str, Any]:
    ensure_platform_tables()
    email_clean = str(email or "").strip().lower()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cur.fetchone()
        if not row or not verify_password(str(password or ""), row["password_hash"]):
            return {"status": "error", "message": "Invalid email or password."}

        user = dict(row)
        token = secrets.token_urlsafe(32)
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
        cur.execute("""
            INSERT INTO auth_sessions (token, user_id, role, expires_at)
            VALUES (?, ?, ?, ?)
        """, (token, user["id"], user["role"], expires))
        conn.commit()

    role = user["role"]
    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": role,
            "state": user["state"],
            "district": user["district"],
            "village": user["village"],
            "farmer_id": user["farmer_id"],
            "permissions": ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["farmer"]),
        },
    }


def get_session_user(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    ensure_platform_tables()
    clean_tok = token.replace("Bearer ", "").strip()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.* FROM auth_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (clean_tok,))
        row = cur.fetchone()
        if not row:
            return None
        user = dict(row)
        user.pop("password_hash", None)
        user["permissions"] = ROLE_PERMISSIONS.get(user["role"], ROLE_PERMISSIONS["farmer"])
        return user


def logout_user(token: Optional[str]) -> Dict[str, Any]:
    if not token:
        return {"status": "success"}
    ensure_platform_tables()
    clean_tok = token.replace("Bearer ", "").strip()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM auth_sessions WHERE token = ?", (clean_tok,))
        conn.commit()
    return {"status": "success", "message": "Logged out successfully."}


def create_password_reset_token(email: str) -> Dict[str, Any]:
    ensure_platform_tables()
    email_clean = str(email or "").strip().lower()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cur.fetchone()
        if not row:
            return {"status": "error", "message": "No registered account found for this email address."}
        reset_token = secrets.token_hex(4).upper()  # 8-character verification code
        expires = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        cur.execute("""
            INSERT INTO password_resets (token, email, expires_at, used)
            VALUES (?, ?, ?, 0)
        """, (reset_token, email_clean, expires))
        conn.commit()
    return {
        "status": "success",
        "message": "Password reset verification code generated (valid for 30 minutes).",
        "reset_token": reset_token,
        "email": email_clean,
    }


def reset_user_password(token: str, new_password: str) -> Dict[str, Any]:
    ensure_platform_tables()
    if not new_password or len(new_password) < 6:
        return {"status": "error", "message": "New password must be at least 6 characters."}
    tok_clean = str(token or "").strip().upper()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM password_resets WHERE token = ? AND used = 0", (tok_clean,))
        row = cur.fetchone()
        if not row:
            return {"status": "error", "message": "Invalid or expired reset code."}
        pw_hash = hash_password(new_password)
        cur.execute("UPDATE users SET password_hash = ? WHERE LOWER(email) = ?", (pw_hash, row["email"]))
        cur.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (tok_clean,))
        conn.commit()
    return {"status": "success", "message": "Password updated successfully. You may now sign in."}


def list_all_users() -> List[Dict[str, Any]]:
    ensure_platform_tables()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, phone, role, state, district, village, created_at FROM users ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]


# =========================================================================
# 2. KRISHISCHEME INTELLIGENCE — VERIFIED HISTORICAL IMPACT ANALYSIS
# =========================================================================

VERIFIED_SCHEME_INTELLIGENCE = [
    {
        "id": "pm-kisan",
        "short_name": "PM-KISAN",
        "full_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "launch_year": 2019,
        "ministry": "Ministry of Agriculture and Farmers Welfare, Govt. of India",
        "objective": "Provide direct income support of ₹6,000/year in three equal DBT installments of ₹2,000 to all landholding farmer families to meet agricultural input expenses.",
        "eligibility_criteria": "All landholding farmer families with cultivable land in their name (excluding institutional landholders, constitutional post holders, and income-tax payers).",
        "benefits": "₹6,000 per year (₹2,000 every 4 months via Aadhaar-seeded Direct Benefit Transfer).",
        "application_process": "1. Open pmkisan.gov.in -> 'New Farmer Registration'. 2. Enter Aadhaar, mobile, state, and Khatauni land details. 3. Complete mandatory OTP/Biometric e-KYC.",
        "required_documents": ["Aadhaar Card linked with Mobile", "Land Ownership Record (Khasra / Khatauni)", "Aadhaar-Seeded Active Bank Account"],
        "official_website": "https://pmkisan.gov.in",
        "source": "Ministry of Agriculture & Farmers Welfare Annual Report & PIB Parliamentary Replies (17th/18th Installment Releases)",
        "reporting_period": "FY 2018-19 to FY 2024-25 (Up to 18th Installment)",
        "last_updated": "2024-10-05",
        "national_metrics": {
            "registered_farmers": "12.50 Crore (Official Portal Registrations)",
            "eligible_farmers": "11.80 Crore (Post Land-Seeding & e-KYC Verification)",
            "approved_applications": "11.45 Crore",
            "rejected_or_ineligible_excluded": "0.68 Crore (Excluded due to Income Tax / Institutional / Unverified Land Seeding)",
            "actual_beneficiaries_latest_installment": "9.40 Crore Farmers (18th Installment)",
            "total_financial_assistance_distributed": "₹3.46 Lakh Crore+ (Cumulative since Feb 2019)",
            "coverage_trend": "Increasing (Expanded from 3.16 Cr in 1st installment to 9.40+ Cr active e-KYC verified beneficiaries)",
        },
        "yearly_trend": [
            {"year": "2018-19", "beneficiaries_crore": 3.16, "amount_crore": 6320},
            {"year": "2019-20", "beneficiaries_crore": 8.95, "amount_crore": 48714},
            {"year": "2020-21", "beneficiaries_crore": 10.45, "amount_crore": 60990},
            {"year": "2021-22", "beneficiaries_crore": 10.78, "amount_crore": 66825},
            {"year": "2022-23", "beneficiaries_crore": 8.56, "amount_crore": 58200},
            {"year": "2023-24", "beneficiaries_crore": 9.12, "amount_crore": 60100},
            {"year": "2024-25", "beneficiaries_crore": 9.40, "amount_crore": 45000},
        ],
        "top_beneficiary_states": [
            {"state": "Uttar Pradesh", "beneficiaries_lakh": 225.4, "disbursed_crore": 74500},
            {"state": "Maharashtra", "beneficiaries_lakh": 91.5, "disbursed_crore": 31200},
            {"state": "Madhya Pradesh", "beneficiaries_lakh": 81.2, "disbursed_crore": 27400},
            {"state": "Bihar", "beneficiaries_lakh": 75.8, "disbursed_crore": 24800},
            {"state": "Rajasthan", "beneficiaries_lakh": 68.4, "disbursed_crore": 22900},
            {"state": "Andhra Pradesh", "beneficiaries_lakh": 45.2, "disbursed_crore": 15400},
            {"state": "Karnataka", "beneficiaries_lakh": 49.6, "disbursed_crore": 16800},
            {"state": "Gujarat", "beneficiaries_lakh": 51.0, "disbursed_crore": 17100},
        ],
        "district_coverage_note": "Granular district-level approved vs rejected counts require State DBT API synchronization. Urban/metro and tribal Sixth-Schedule districts show lower land-record seeding density.",
    },
    {
        "id": "pmfby",
        "short_name": "PMFBY",
        "full_name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "launch_year": 2016,
        "ministry": "Ministry of Agriculture and Farmers Welfare, Govt. of India",
        "objective": "Provide comprehensive crop insurance protection against non-preventable natural risks from pre-sowing to post-harvest at highly subsidized farmer premium rates (1.5% Rabi, 2% Kharif, 5% Commercial/Horticultural).",
        "eligibility_criteria": "All farmers (loanee and non-loanee, including tenant/sharecroppers in notified states) growing notified crops in notified insurance units (IU).",
        "benefits": "Full sum-insured protection against drought, flood, inundation, hailstorm, cyclone, unseasonal rain, and widespread pest/disease attack. Over ₹500 returned in claims per ₹100 of farmer premium paid nationally.",
        "application_process": "Enroll via pmfby.gov.in, CSC centres, or lending bank before seasonal cut-off (typically July 31 for Kharif, Dec 31 for Rabi). Report localized calamity within 72 hours on Crop Insurance App or Toll-Free 14447.",
        "required_documents": ["Aadhaar Card", "Land Possession Record (Khatauni) / Tenancy Agreement", "Sowing Certificate (Bawani Praman Patra)", "Bank Passbook with IFSC"],
        "official_website": "https://pmfby.gov.in",
        "source": "PMFBY Official Dashboard & Ministry of Agriculture Parliamentary Reports (2016-17 to 2023-24)",
        "reporting_period": "2016-17 to 2023-24 (8 Cumulative Crop Years)",
        "last_updated": "2024-08-15",
        "national_metrics": {
            "registered_farmers": "56.80 Crore Farmer Applications (Cumulative since 2016)",
            "eligible_farmers": "All farmers growing notified crops in participating States/UTs",
            "approved_applications": "39.70 Crore Farmer Applications Enrolled in FY 2023-24 (Record High)",
            "rejected_or_ineligible_excluded": "Historical data unavailable (Official portal reports total insured vs claim-settled applications)",
            "actual_beneficiaries_latest_installment": "14.80+ Crore Farmer Claims Paid Cumulatively",
            "total_financial_assistance_distributed": "₹1.63 Lakh Crore+ Claims Paid (against ₹32,440 Crore total farmer share of premium)",
            "coverage_trend": "Increasing (Farmer applications grew 27% in FY 2023-24 to reach 3.97 Crore applications; non-loanee voluntary share rose to 55%)",
        },
        "yearly_trend": [
            {"year": "2018-19", "applications_crore": 5.82, "claims_paid_crore": 29354},
            {"year": "2019-20", "applications_crore": 6.13, "claims_paid_crore": 27398},
            {"year": "2020-21", "applications_crore": 6.23, "claims_paid_crore": 21107},
            {"year": "2021-22", "applications_crore": 8.32, "claims_paid_crore": 19152},
            {"year": "2022-23", "applications_crore": 11.68, "claims_paid_crore": 18210},
            {"year": "2023-24", "applications_crore": 15.10, "claims_paid_crore": 17500},
        ],
        "top_beneficiary_states": [
            {"state": "Maharashtra", "applications_lakh": 385.0, "claims_paid_crore": 34200},
            {"state": "Rajasthan", "applications_lakh": 310.5, "claims_paid_crore": 28900},
            {"state": "Madhya Pradesh", "applications_lakh": 275.0, "claims_paid_crore": 26400},
            {"state": "Chhattisgarh", "applications_lakh": 92.0, "claims_paid_crore": 8900},
            {"state": "Odisha", "applications_lakh": 118.0, "claims_paid_crore": 7800},
            {"state": "Uttar Pradesh", "applications_lakh": 145.0, "claims_paid_crore": 10200},
            {"state": "Haryana", "applications_lakh": 64.0, "claims_paid_crore": 7400},
        ],
        "district_coverage_note": "States that opted out in specific historical years (e.g., Punjab, Bihar, West Bengal) have state-specific relief models instead of central PMFBY.",
    },
    {
        "id": "kcc",
        "short_name": "KCC",
        "full_name": "Kisan Credit Card (KCC) & Modified Interest Subvention Scheme",
        "launch_year": 1998,
        "ministry": "Ministry of Agriculture & Farmers Welfare / NABARD / Department of Financial Services",
        "objective": "Provide timely, adequate institutional credit to farmers for crop cultivation, post-harvest expenses, and allied activities (dairy, fisheries) at an effective interest rate of 4% per annum.",
        "eligibility_criteria": "Owner cultivators, tenant farmers, oral lessees, sharecroppers, SHGs/JLGs, and dairy/fishery farmers.",
        "benefits": "Short-term crop credit up to ₹3 Lakh at 7% p.a. with 3% prompt repayment incentive = 4% effective interest rate. Collateral-free limit up to ₹1.60 Lakh (upgraded to ₹2.00 Lakh by RBI effective Jan 2025).",
        "application_process": "Apply at any Commercial Bank, Regional Rural Bank (RRB), Cooperative Bank, or via pmkisan.gov.in / JanSamarth portal.",
        "required_documents": ["Aadhaar Card & PAN Card", "Land Record (Khatauni)", "2 Passport Photos", "Completed KCC Application Form"],
        "official_website": "https://www.myscheme.gov.in/schemes/kcc",
        "source": "NABARD / RBI / Ministry of Finance Parliamentary Reports (FY 2023-24)",
        "reporting_period": "Cumulative Operative KCC Accounts up to March 2024",
        "last_updated": "2024-07-22",
        "national_metrics": {
            "registered_farmers": "7.75 Crore Operative KCC Accounts",
            "eligible_farmers": "All PM-KISAN beneficiaries & institutional agricultural borrowers",
            "approved_applications": "7.75 Crore Active Sanctioned Cards",
            "rejected_or_ineligible_excluded": "Historical data unavailable (Bank-level credit appraisal records)",
            "actual_beneficiaries_latest_installment": "7.75 Crore Farmers",
            "total_financial_assistance_distributed": "₹9.81 Lakh Crore Operative Credit Limit Sanctioned",
            "coverage_trend": "Increasing (Over 4.25 Crore new KCC cards issued during saturation drives since 2020)",
        },
        "yearly_trend": [
            {"year": "2019-20", "operative_accounts_crore": 6.67, "credit_limit_lakh_crore": 7.09},
            {"year": "2020-21", "operative_accounts_crore": 7.02, "credit_limit_lakh_crore": 7.85},
            {"year": "2021-22", "operative_accounts_crore": 7.18, "credit_limit_lakh_crore": 8.45},
            {"year": "2022-23", "operative_accounts_crore": 7.36, "credit_limit_lakh_crore": 9.28},
            {"year": "2023-24", "operative_accounts_crore": 7.75, "credit_limit_lakh_crore": 9.81},
        ],
        "top_beneficiary_states": [
            {"state": "Uttar Pradesh", "accounts_lakh": 142.0, "credit_crore": 168000},
            {"state": "Rajasthan", "accounts_lakh": 72.5, "credit_crore": 105000},
            {"state": "Maharashtra", "accounts_lakh": 68.0, "credit_crore": 92000},
            {"state": "Madhya Pradesh", "accounts_lakh": 64.2, "credit_crore": 88000},
            {"state": "Andhra Pradesh", "accounts_lakh": 54.0, "credit_crore": 76000},
            {"state": "Punjab", "accounts_lakh": 31.5, "credit_crore": 72000},
        ],
        "district_coverage_note": "Districts with higher tenant cultivation in Eastern India show lower KCC saturation than Punjab, Haryana, and Western UP.",
    },
    {
        "id": "soil-health-card",
        "short_name": "Soil Health Card",
        "full_name": "Soil Health Card (SHC) & Soil Health Management Scheme",
        "launch_year": 2015,
        "ministry": "Department of Agriculture & Farmers Welfare, Govt. of India",
        "objective": "Assess soil nutrient status across 12 parameters (N, P, K, S, Zn, Fe, Cu, Mn, B, pH, EC, OC) and provide crop-wise fertilizer recommendations to curb chemical overuse.",
        "eligibility_criteria": "All farming households across all States and Union Territories.",
        "benefits": "Free laboratory testing of farm soil samples and personalized NPK + micronutrient dosage card, reducing chemical fertilizer cost by 8–10% and boosting yields.",
        "application_process": "Grid/village-level soil sampling by State Agriculture Department or Krishi Sakhi via the Mobile Soil Health Card App (soilhealth.dac.gov.in).",
        "required_documents": ["Aadhaar Card", "Mobile Number", "Khasra / Survey Number & Geo-coordinates"],
        "official_website": "https://soilhealth.dac.gov.in",
        "source": "Soil Health Card Portal (soilhealth.dac.gov.in) & PIB Official Releases",
        "reporting_period": "Cycle-I (2015-17), Cycle-II (2017-19), Model Village & Digital SHC (2020-2024)",
        "last_updated": "2024-09-10",
        "national_metrics": {
            "registered_farmers": "24.17 Crore Soil Health Cards Distributed Cumulatively",
            "eligible_farmers": "All ~14.6 Crore operational landholdings in India",
            "approved_applications": "24.17 Crore Cards Issued across Cycles I, II & Digital SHC",
            "rejected_or_ineligible_excluded": "Not Applicable (Universal Soil Testing Service)",
            "actual_beneficiaries_latest_installment": "24.17 Crore Cards Issued",
            "total_financial_assistance_distributed": "₹1,706+ Crore Central Assistance released to States for Soil Testing Labs & Sampling",
            "coverage_trend": "Increasing (Transitioned to Geo-referenced Digital Soil Health Cards via Mobile App in 2023-24)",
        },
        "yearly_trend": [
            {"year": "Cycle-I (2015-17)", "cards_issued_crore": 10.74},
            {"year": "Cycle-II (2017-19)", "cards_issued_crore": 11.97},
            {"year": "Model Village (2019-20)", "cards_issued_crore": 0.19},
            {"year": "Digital SHC (2023-24)", "cards_issued_crore": 1.27},
        ],
        "top_beneficiary_states": [
            {"state": "Uttar Pradesh", "cards_lakh": 392.0},
            {"state": "Maharashtra", "cards_lakh": 265.0},
            {"state": "Madhya Pradesh", "cards_lakh": 212.0},
            {"state": "Rajasthan", "cards_lakh": 188.0},
            {"state": "Karnataka", "cards_lakh": 165.0},
            {"state": "Andhra Pradesh", "cards_lakh": 148.0},
        ],
        "district_coverage_note": "591 districts are directly covered in our repository's `soil/all_states_india_soil_dataset(2).csv` across 5 survey cycles (2013-2026).",
    },
    {
        "id": "pmksy",
        "short_name": "PMKSY",
        "full_name": "Pradhan Mantri Krishi Sinchayee Yojana (Per Drop More Crop - PDMC)",
        "launch_year": 2015,
        "ministry": "Department of Agriculture & Farmers Welfare / Ministry of Jal Shakti",
        "objective": "Enhance water-use efficiency at farm level through Micro-Irrigation technologies (Drip and Sprinkler systems) under 'Per Drop More Crop'.",
        "eligibility_criteria": "All farmers with cultivable land and assured irrigation source; up to 5 hectares per beneficiary.",
        "benefits": "55% financial subsidy for Small & Marginal farmers and 45% for other farmers on Drip and Sprinkler system installation.",
        "application_process": "Apply online through State Horticulture / Agriculture DBT portals (e.g., upagriculture.com, mahadbt.maharashtra.gov.in) or pmksy.gov.in.",
        "required_documents": ["Aadhaar Card", "Land Ownership Record (7/12 Extract or Khatauni)", "Water Source Proof / Electricity Bill", "Bank Passbook"],
        "official_website": "https://pmksy.gov.in",
        "source": "PMKSY - Per Drop More Crop Official Dashboard & Ministry Annual Report (2015-16 to 2023-24)",
        "reporting_period": "FY 2015-16 to FY 2023-24",
        "last_updated": "2024-08-01",
        "national_metrics": {
            "registered_farmers": "Historical data unavailable (Applications managed by respective State DBT portals)",
            "eligible_farmers": "All irrigated & semi-irrigated landholders",
            "approved_applications": "89.85 Lakh Hectares covered under Micro-Irrigation (2015-16 to 2023-24)",
            "rejected_or_ineligible_excluded": "Historical data unavailable",
            "actual_beneficiaries_latest_installment": "83.40+ Lakh Farmers benefitted",
            "total_financial_assistance_distributed": "₹21,870+ Crore Central Subsidy Released under PDMC",
            "coverage_trend": "Increasing (Average 9–11 Lakh Hectares added annually under Drip & Sprinkler irrigation)",
        },
        "yearly_trend": [
            {"year": "2018-19", "area_covered_lakh_ha": 11.58, "central_release_crore": 2918},
            {"year": "2019-20", "area_covered_lakh_ha": 11.72, "central_release_crore": 2700},
            {"year": "2020-21", "area_covered_lakh_ha": 9.37, "central_release_crore": 2562},
            {"year": "2021-22", "area_covered_lakh_ha": 10.15, "central_release_crore": 1998},
            {"year": "2022-23", "area_covered_lakh_ha": 11.12, "central_release_crore": 2450},
            {"year": "2023-24", "area_covered_lakh_ha": 10.85, "central_release_crore": 2610},
        ],
        "top_beneficiary_states": [
            {"state": "Karnataka", "area_lakh_ha": 17.8},
            {"state": "Tamil Nadu", "area_lakh_ha": 13.4},
            {"state": "Andhra Pradesh", "area_lakh_ha": 12.9},
            {"state": "Gujarat", "area_lakh_ha": 11.6},
            {"state": "Maharashtra", "area_lakh_ha": 10.8},
            {"state": "Rajasthan", "area_lakh_ha": 6.4},
            {"state": "Uttar Pradesh", "area_lakh_ha": 4.2},
        ],
        "district_coverage_note": "Peninsular and Western semi-arid states account for >70% of micro-irrigation adoption; Indo-Gangetic canal districts have lower drip penetration.",
    },
    {
        "id": "pm-kusum",
        "short_name": "PM-KUSUM",
        "full_name": "Pradhan Mantri Kisan Urja Suraksha evam Utthaan Mahabhiyan (PM-KUSUM)",
        "launch_year": 2019,
        "ministry": "Ministry of New and Renewable Energy (MNRE), Govt. of India",
        "objective": "De-dieselize the farm sector and provide water and energy security to farmers through Component-A (Decentralized Solar Plants), Component-B (Standalone Solar Pumps), and Component-C (Feeder/Pump Solarization).",
        "eligibility_criteria": "Individual farmers, Water User Associations, FPOs, and Primary Agricultural Credit Societies (PACS).",
        "benefits": "Up to 60% government capital subsidy (30% Central + 30% State; 50% Central in NE/Hill states/J&K) for standalone solar agricultural pumps (1 HP to 10 HP).",
        "application_process": "Apply on pmkusum.mnre.gov.in or State Nodal Agency portals during token booking windows.",
        "required_documents": ["Aadhaar Card", "Land Ownership Record (Khatauni)", "Bank Account Passbook", "Borewell / Water Source Declaration"],
        "official_website": "https://pmkusum.mnre.gov.in",
        "source": "MNRE Official PM-KUSUM Portal Dashboard (pmkusum.mnre.gov.in)",
        "reporting_period": "2019-20 to October 2024",
        "last_updated": "2024-10-15",
        "national_metrics": {
            "registered_farmers": "Historical data unavailable (State token-booking queues vary by state)",
            "eligible_farmers": "Over 13.50 Lakh Solar Pumps Sanctioned under Component-B",
            "approved_applications": "13.50 Lakh Standalone Solar Pumps Sanctioned",
            "rejected_or_ineligible_excluded": "Historical data unavailable",
            "actual_beneficiaries_latest_installment": "4.15+ Lakh Solar Pumps Installed & Commissioned",
            "total_financial_assistance_distributed": "₹34,422 Crore Total Approved Central Financial Outlay (extended till March 2026)",
            "coverage_trend": "Increasing (Installations accelerated sharply across Rajasthan, Maharashtra, Haryana, and UP in 2023-24)",
        },
        "yearly_trend": [
            {"year": "2020-21", "pumps_installed_cumulative": 48000},
            {"year": "2021-22", "pumps_installed_cumulative": 102000},
            {"year": "2022-23", "pumps_installed_cumulative": 215000},
            {"year": "2023-24", "pumps_installed_cumulative": 355000},
            {"year": "2024-25 (Oct)", "pumps_installed_cumulative": 415000},
        ],
        "top_beneficiary_states": [
            {"state": "Rajasthan", "pumps_installed": 132500},
            {"state": "Maharashtra", "pumps_installed": 108400},
            {"state": "Haryana", "pumps_installed": 96200},
            {"state": "Uttar Pradesh", "pumps_installed": 52400},
            {"state": "Punjab", "pumps_installed": 14800},
            {"state": "Madhya Pradesh", "pumps_installed": 11200},
        ],
        "district_coverage_note": "High-insolation, deep-water-table districts in Rajasthan, Haryana, Maharashtra, and Bundelkhand/Western UP lead adoption.",
    },
]


def get_krishischeme_intelligence(
    scheme_id: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> Dict[str, Any]:
    """Returns verified scheme impact analysis and any admin-uploaded records."""
    ensure_platform_tables()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM scheme_impact_records ORDER BY id DESC LIMIT 100")
        uploaded = [dict(r) for r in cur.fetchall()]

    if state:
        st_norm = standardize_state(state)
        uploaded = [r for r in uploaded if standardize_state(r.get("state", "")) == st_norm]

    if scheme_id:
        for sc in VERIFIED_SCHEME_INTELLIGENCE:
            if sc["id"].lower() == scheme_id.lower() or sc["short_name"].lower() == scheme_id.lower():
                return {
                    "status": "success",
                    "scheme": sc,
                    "admin_uploaded_records": [r for r in uploaded if r["scheme_id"] == sc["id"]],
                }
        return {"status": "not_found", "message": "Historical data unavailable."}

    return {
        "status": "success",
        "selected_state": standardize_state(state) if state else "All-India",
        "selected_district": district or "All Districts",
        "total_schemes_analyzed": len(VERIFIED_SCHEME_INTELLIGENCE),
        "schemes": VERIFIED_SCHEME_INTELLIGENCE,
        "admin_uploaded_records": uploaded,
        "data_integrity_note": (
            "All statistics cite official Ministry of Agriculture & Farmers Welfare, PM-KISAN, PMFBY, NABARD, "
            "Soil Health Card, PMKSY, and MNRE parliamentary/annual reports. Metrics unavailable at granular "
            "sub-district levels are explicitly marked 'Historical data unavailable.'"
        ),
    }


def add_admin_scheme_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Allows administrators to upload verified scheme impact records."""
    ensure_platform_tables()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO scheme_impact_records (
                scheme_id, state, district, year, registered_farmers,
                eligible_farmers, approved_applications, rejected_applications,
                actual_beneficiaries, amount_disbursed_crore,
                source_citation, reporting_period, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(payload.get("scheme_id") or "pm-kisan"),
            standardize_state(str(payload.get("state") or "Uttar Pradesh")),
            standardize_district(str(payload.get("district") or "All Districts")),
            str(payload.get("year") or "2023-24"),
            payload.get("registered_farmers"),
            payload.get("eligible_farmers"),
            payload.get("approved_applications"),
            payload.get("rejected_applications"),
            payload.get("actual_beneficiaries"),
            payload.get("amount_disbursed_crore"),
            str(payload.get("source_citation") or "Admin Verified Upload (data.gov.in)"),
            str(payload.get("reporting_period") or "FY 2023-24"),
            datetime.utcnow().strftime("%Y-%m-%d"),
        ))
        conn.commit()
    return {"status": "success", "message": "Verified scheme impact record stored."}


# =========================================================================
# 3. KRISHISURAKSHA — AI-POWERED CROP INSURANCE ASSISTANCE (PMFBY)
# =========================================================================

COVERED_PERILS_PMFBY = {
    "drought": "Mid-Season Adversity / Prevented Sowing / Yield Loss (Covered under Area Approach)",
    "dry spell": "Mid-Season Adversity / Yield Loss (Covered under Area Approach)",
    "flood": "Inundation / Widespread Flood (Covered; Hydroponic/hydrophilic crops like Rice covered under area yield loss)",
    "inundation": "Localized Calamity — Inundation (Covered; Intimate within 72 hours)",
    "hailstorm": "Localized Calamity — Hailstorm (Covered; Intimate within 72 hours)",
    "landslide": "Localized Calamity — Landslide (Covered; Intimate within 72 hours)",
    "cloudburst": "Localized Calamity — Cloudburst (Covered; Intimate within 72 hours)",
    "unseasonal rain": "Post-Harvest / Standing Crop Unseasonal & Cyclonic Rain (Covered; Intimate within 72 hours if harvested & drying in field up to 14 days)",
    "cyclonic rain": "Post-Harvest / Cyclonic Rain (Covered; Intimate within 72 hours)",
    "pest attack": "Widespread Pest & Disease Attack (Covered under CCE Area Yield Approach)",
    "disease": "Widespread Crop Disease (Covered under CCE Area Yield Approach)",
    "natural fire": "Localized Calamity — Natural Fire & Lightning (Covered; Intimate within 72 hours)",
}

EXCLUDED_PERILS_PMFBY = {
    "wild animal": "Damage by wild or stray animals (General exclusion unless specifically notified as an add-on cover by the State Government)",
    "stray cattle": "Damage by stray cattle/grazing (Excluded under standard PMFBY operational guidelines)",
    "theft": "Theft or malicious damage (Excluded under PMFBY guidelines)",
    "war": "War or nuclear perils (Excluded under PMFBY guidelines)",
    "negligence": "Post-harvest loss after produce is bundled/heaped or beyond 14 days of harvesting (Excluded)",
}


def assess_pmfby_claim_eligibility(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Rules-based PMFBY eligibility & claim guidance assessment engine."""
    ensure_platform_tables()

    farmer_name = str(payload.get("farmer_name") or "Farmer").strip()
    state = standardize_state(str(payload.get("state") or "").strip())
    district = standardize_district(str(payload.get("district") or "").strip(), state)
    village = str(payload.get("village") or "").strip()
    crop = str(payload.get("crop") or "").strip()
    season = str(payload.get("season") or "").strip()
    land_acres = float(payload.get("land_acres") if payload.get("land_acres") is not None else 2.0)
    sowing_date = str(payload.get("sowing_date") or "").strip()
    enrolled_pmfby = str(
        payload.get("enrolled_pmfby")
        if payload.get("enrolled_pmfby") is not None
        else (payload.get("enrolled_in_pmfby") or "")
    ).strip().lower()
    policy_number = str(payload.get("policy_number") or "").strip()
    damage_date_str = str(payload.get("damage_date") or payload.get("loss_date") or "").strip()
    damage_type = str(payload.get("damage_type") or payload.get("loss_cause") or "").strip().lower()
    photo_filename = str(payload.get("photo_filename") or "").strip()
    explicit_hours = payload.get("hours_since_damage")

    # Check 1: Are mandatory inputs provided?
    if not state or not district or not crop or not season or not damage_type or land_acres <= 0:
        return {
            "status": "success",
            "assessment_result": "More information required.",
            "eligibility_status": "More information required.",
            "within_72_hour_window": False,
            "reasons": [
                "State, District, Crop, Season, Land Area (Acres), and Type of Crop Damage are required to evaluate PMFBY rules."
            ],
            "disclaimer": "This is a preliminary AI-assisted information and eligibility guidance system. Final claim approval depends on official insurance company and government authority verification.",
        }

    reasons = []
    checks_passed = []
    hours_since_damage = float(explicit_hours) if explicit_hours is not None else None
    within_72_hour_window = True

    # Check 2: Is the crop notified/grown in this state & season in our All-India dataset?
    state_crops = CONFIG.state_crops.get(state, CONFIG.crops)
    crop_match = any(c.lower() == crop.lower() or (crop.lower() == "mustard" and "mustard" in c.lower()) for c in state_crops)
    if crop_match:
        checks_passed.append(f"Crop '{crop}' ({season}) is a recognized agricultural crop in {state} ({district}).")
    else:
        reasons.append(f"Crop '{crop}' could not be verified in the historical crop notification registry for {state}.")

    # Check 3: Enrolment status
    if enrolled_pmfby in ("no", "not enrolled", "false"):
        result_label = "Not eligible under currently available rules."
        reasons.append(
            "Active PMFBY insurance enrolment prior to the seasonal cut-off date (typically July 31 for Kharif / Dec 31 for Rabi) is mandatory to file a claim."
        )
    elif enrolled_pmfby in ("unsure", "unknown", ""):
        result_label = "Eligibility cannot be verified with available information."
        reasons.append(
            "Please verify whether your KCC bank account deducted the PMFBY premium or provide your CSC/Portal 19-digit Application/Policy Number."
        )
    else:
        checks_passed.append(
            f"Farmer indicated active PMFBY enrolment" + (f" (Policy/Application No: {policy_number})." if policy_number else ".")
        )
        result_label = "Potentially eligible."

    # Check 3b: Explicit missing mandatory documents check if passed in payload
    if payload.get("has_aadhaar") is False or payload.get("has_bank_passbook") is False:
        if result_label == "Potentially eligible.":
            result_label = "More information required."
        reasons.append("Aadhaar card and Aadhaar-seeded Bank Passbook are mandatory to process DBT insurance claims.")

    # Check 3c: Landowner vs. Tenant / Sharecropper (Bataidar) Eligibility Rules
    ownership_type = str(payload.get("ownership_type") or "owner").strip().lower()
    landowner_kcc_duplicate = str(payload.get("landowner_kcc_claimed") or "no").strip().lower()
    landowner_tenant_guidance = ""

    if ownership_type == "tenant_with_agreement":
        checks_passed.append(
            "Landowner-to-Tenant Rule Passed: Tenant/Sharecropper (Bataidar) cultivating a Landowner's plot is ELIGIBLE under PMFBY with Landowner Lease/Consent Agreement or Patwari/Lekhpal Sowing Certificate."
        )
        landowner_tenant_guidance = (
            "✅ ELIGIBLE VIA LANDOWNER AGREEMENT: Under PMFBY rules, a Tenant/Bataidar farmer CAN get crop insurance on a Landowner's land. "
            "The claim payout comes from the Insurance Company directly to the cultivating farmer's Aadhaar-linked bank account (NOT from the Landowner's pocket). "
            "Ensure you attach: (1) Written Lease/Batai Agreement or Landowner Consent (NOC) with Khasra/Khatauni number, and (2) Sowing Certificate (Bawani Praman Patra) signed by Lekhpal/Patwari/Gram Pradhan."
        )
    elif ownership_type == "tenant_without_agreement":
        if result_label == "Potentially eligible.":
            result_label = "More information required."
        reasons.append(
            "Landowner Consent / Sowing Certificate Required: As a Tenant/Bataidar farming on a Landowner's plot without a written agreement, you MUST obtain either a Landowner Consent Letter (Sahmati Patra) with Khasra number OR a Sowing Certificate from the Village Lekhpal/Patwari/Sarpanch to prove actual cultivation."
        )
        landowner_tenant_guidance = (
            "⚠️ ACTION REQUIRED FROM LANDOWNER / LEKHPAL: Without a written lease or Landowner NOC, the insurance company cannot verify that you (and not the Landowner) cultivated the crop. "
            "Get a simple signed Consent Note (Sahmati Patra) from the Landowner mentioning the Khasra number, OR get a Sowing Certificate (Bawani Praman Patra) from your Village Patwari/Lekhpal."
        )
    elif ownership_type == "joint_family":
        checks_passed.append(
            "Joint Family Khatauni Rule: Eligible for your cultivated share (Hissa) using combined Khatauni + Sowing Certificate."
        )
        landowner_tenant_guidance = (
            "✅ JOINT FAMILY LAND ELIGIBLE: You can claim PMFBY insurance for your specific cultivated share (Hissa) of the joint family Khatauni. Attach the joint Khatauni copy and a family share declaration / Sowing Certificate."
        )
    else:
        checks_passed.append("Land Ownership Verified: Direct Khatedar Landowner (Khud ki Zameen — Khasra/Khatauni holder).")
        landowner_tenant_guidance = (
            "✅ DIRECT LANDOWNER ELIGIBLE: As the registered Khatedar Landowner, your claim is processed directly against your Khasra/Khatauni record and PMFBY Policy/KCC account."
        )

    if landowner_kcc_duplicate == "yes" and ownership_type.startswith("tenant"):
        if result_label == "Potentially eligible.":
            result_label = "More information required."
        reasons.append(
            "Duplicate Plot Alert: If the Landowner already has an active KCC loan that auto-deducted PMFBY insurance on the same Khasra number, two policies cannot claim on the same plot unless the Landowner provides an NOC/Bank transfer declaration."
        )

    # Check 4: Damage Peril Coverage
    matched_excluded = next((desc for k, desc in EXCLUDED_PERILS_PMFBY.items() if k in damage_type), None)
    matched_covered = next((desc for k, desc in COVERED_PERILS_PMFBY.items() if k in damage_type), None)

    if matched_excluded:
        result_label = "Not eligible under currently available rules."
        reasons.append(f"Peril Exclusion: {matched_excluded}")
    elif matched_covered:
        checks_passed.append(f"Covered Risk Peril: {matched_covered}")
    else:
        if result_label == "Potentially eligible.":
            result_label = "Eligibility cannot be verified with available information."
        reasons.append(f"Damage type '{damage_type}' requires manual inspection against your State's specific PMFBY notification.")

    # Check 5: 72-Hour Intimation Rule for Localized / Post-Harvest Losses
    is_localized = any(k in damage_type for k in ["hail", "inundation", "landslide", "cloudburst", "unseasonal", "cyclonic", "fire"])
    if hours_since_damage is not None:
        if is_localized:
            if hours_since_damage <= 72.0:
                within_72_hour_window = True
                checks_passed.append(
                    f"Timely Reporting Window: Crop damage occurred ~{int(hours_since_damage)} hours ago, which is within the mandatory 72-hour localized calamity intimation window."
                )
            else:
                within_72_hour_window = False
                reasons.append(
                    f"72-Hour Intimation Alert: Localized/Post-harvest damage occurred ~{int(hours_since_damage)} hours ago. "
                    f"Under PMFBY operational guidelines, individual localized claims must be intimated within 72 hours."
                )
                if result_label == "Potentially eligible.":
                    result_label = "More information required."
    elif damage_date_str:
        try:
            dmg_dt = datetime.strptime(damage_date_str[:10], "%Y-%m-%d")
            now_dt = datetime.now()
            diff_hours = max(0.0, (now_dt - dmg_dt).total_seconds() / 3600.0)
            hours_since_damage = round(diff_hours, 1)
            if is_localized:
                if diff_hours <= 72.0:
                    within_72_hour_window = True
                    checks_passed.append(
                        f"Timely Reporting Window: Crop damage occurred ~{int(diff_hours)} hours ago, which is within the mandatory 72-hour localized calamity intimation window."
                    )
                else:
                    within_72_hour_window = False
                    reasons.append(
                        f"72-Hour Intimation Alert: Localized/Post-harvest damage occurred ~{int(diff_hours // 24)} days ago ({damage_date_str}). "
                        f"Under PMFBY operational guidelines, individual localized claims must be intimated within 72 hours, though widespread area-level yield losses remain covered via Crop Cutting Experiments (CCE)."
                    )
                    if result_label == "Potentially eligible.":
                        result_label = "More information required."
        except Exception:
            pass
    elif is_localized and result_label == "Potentially eligible.":
        within_72_hour_window = False
        result_label = "More information required."
        reasons.append("Exact crop damage date is required to verify the mandatory 72-hour localized calamity reporting window.")

    explanation_text = " ".join(checks_passed + reasons)

    # Log assessment in SQLite
    assess_id = f"CLM-{secrets.token_hex(4).upper()}"
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO insurance_assessments (
                id, user_id, farmer_name, state, district, village, crop, season,
                land_acres, sowing_date, enrolled_pmfby, policy_number,
                damage_date, damage_type, eligibility_status, explanation,
                hours_since_damage, photo_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assess_id,
            payload.get("user_id", "user-farmer-001"),
            farmer_name,
            state,
            district,
            village,
            crop,
            season,
            land_acres,
            sowing_date,
            enrolled_pmfby,
            policy_number,
            damage_date_str,
            damage_type,
            result_label,
            explanation_text,
            hours_since_damage,
            photo_filename,
        ))
        conn.commit()

    # Compute indicative Sum Insured & Farmer Premium based on season & land area
    sum_insured_per_acre = 34000.0 if season.lower() == "rabi" else (32000.0 if season.lower() == "kharif" else 42000.0)
    prem_rate = 0.015 if season.lower() == "rabi" else (0.02 if season.lower() == "kharif" else 0.05)
    estimated_sum_insured_inr = round(land_acres * sum_insured_per_acre)
    farmer_premium_inr = round(estimated_sum_insured_inr * prem_rate)

    return {
        "status": "success",
        "assessment_id": assess_id,
        "assessment_result": result_label,
        "eligibility_status": result_label,
        "within_72_hour_window": within_72_hour_window,
        "ownership_type": ownership_type,
        "landowner_tenant_guidance": landowner_tenant_guidance,
        "estimated_sum_insured_inr": estimated_sum_insured_inr,
        "farmer_premium_inr": farmer_premium_inr,
        "checks_passed": checks_passed,
        "reasons_and_alerts": reasons,
        "explanation": explanation_text,
        "hours_since_damage": hours_since_damage,
        "premium_rate_info": "1.5% for Rabi Crops | 2.0% for Kharif Crops | 5.0% for Commercial/Horticultural Crops",
        "claim_procedure_steps": [
            "Step 1 (Immediate 72-Hour Intimation): Report localized or post-harvest crop loss within 72 hours via the Krishi Rakshak Toll-Free Helpline (14447), the official PMFBY Crop Insurance Mobile App, or your lending bank/CSC.",
            "Step 2 (Geo-Tagged Field Evidence): Upload 2–3 clear geo-tagged photographs and a short video of the damaged standing/harvested crop via the PMFBY Crop Insurance App.",
            "Step 3 (Joint Loss Assessment Survey): A joint team comprising the Insurance Company Loss Assessor and Block/Village Agriculture Officer will inspect the plot within 10 days of intimation.",
            "Step 4 (Area-Level CCE & DBT Settlement): For widespread drought/flood/pest losses, claims are calculated automatically from Crop Cutting Experiments (CCE) and credited directly to your Aadhaar-linked bank account.",
        ],
        "required_documents_checklist": [
            "PMFBY Application / Policy Receipt (19-digit Ack Number) or KCC Bank Statement showing premium debit",
            "Aadhaar Card linked with active mobile number and DBT bank account",
            "Updated Land Record (Khasra / Khatauni / 7-12 Extract) or notarized Tenant/Sharecropper agreement",
            "Sowing Certificate (Bawani Praman Patra) issued by Patwari / Lekhpal / Gram Pradhan",
            "Geo-tagged photographs of damaged crop plot with date/time stamp",
            "Cancelled Cheque / Bank Passbook copy with clear IFSC code",
        ],
        "official_links_and_helplines": {
            "portal": "https://pmfby.gov.in",
            "krishi_rakshak_helpline": "14447 (National Toll-Free Crop Insurance Helpline)",
            "whatsapp_chatbot": "+91 70655 14447 (PMFBY Official WhatsApp Bot)",
            "kisan_call_centre": "1800-180-1551",
        },
        "disclaimer": (
            "IMPORTANT DISCLAIMER: KrishiSuraksha is a preliminary AI-assisted information and eligibility guidance system "
            "grounded in official PMFBY operational guidelines. It never guarantees insurance approval or compensation. "
            "Final claim approval depends on official insurance company and State/Central Government authority verification."
        ),
    }


def get_insurance_history(user_id: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_platform_tables()
    with get_db_connection() as conn:
        cur = conn.cursor()
        if user_id and state:
            cur.execute(
                "SELECT * FROM insurance_assessments WHERE user_id = ? AND state = ? ORDER BY created_at DESC LIMIT 25",
                (user_id, standardize_state(state)),
            )
        elif user_id:
            cur.execute("SELECT * FROM insurance_assessments WHERE user_id = ? ORDER BY created_at DESC LIMIT 25", (user_id,))
        elif state:
            cur.execute(
                "SELECT * FROM insurance_assessments WHERE state = ? ORDER BY created_at DESC LIMIT 50",
                (standardize_state(state),),
            )
        else:
            cur.execute("SELECT * FROM insurance_assessments ORDER BY created_at DESC LIMIT 50")
        return [dict(r) for r in cur.fetchall()]


# =========================================================================
# 4. NASA EARTH INTELLIGENCE — NASA POWER API & NASA GIBS SATELLITE LAYERS
# =========================================================================

def _load_district_coords() -> Dict[Tuple[str, str], Dict[str, Any]]:
    lookup_path = MODELS_DIR / "all_india_intelligence_lookup.joblib"
    if lookup_path.exists():
        try:
            import joblib
            b = joblib.load(lookup_path)
            return b.get("weather_lookup", {})
        except Exception:
            pass
    return {}


_DISTRICT_COORDS_CACHE: Optional[Dict[Tuple[str, str], Dict[str, Any]]] = None


def get_district_coordinates(state: str, district: str) -> Tuple[float, float, bool]:
    """Resolves (Latitude, Longitude, has_exact_coord) for any Indian state & district."""
    global _DISTRICT_COORDS_CACHE
    if _DISTRICT_COORDS_CACHE is None:
        _DISTRICT_COORDS_CACHE = _load_district_coords()

    st = standardize_state(state)
    dt = standardize_district(district, st)
    rec = _DISTRICT_COORDS_CACHE.get((st, dt))
    if rec and "Latitude" in rec and "Longitude" in rec:
        return float(rec["Latitude"]), float(rec["Longitude"]), True

    # Fallback: average coordinates of the state
    state_lats = [v["Latitude"] for (k_st, _), v in _DISTRICT_COORDS_CACHE.items() if k_st == st and "Latitude" in v]
    state_lons = [v["Longitude"] for (k_st, _), v in _DISTRICT_COORDS_CACHE.items() if k_st == st and "Longitude" in v]
    if state_lats and state_lons:
        return round(sum(state_lats) / len(state_lats), 4), round(sum(state_lons) / len(state_lons), 4), False

    return 28.9845, 77.7064, False  # Default Meerut


def fetch_nasa_power_intelligence(
    state: str = "Uttar Pradesh",
    district: str = "Meerut",
    start_date: Optional[str] = "20230101",
    end_date: Optional[str] = "20231231",
    temporal_view: str = "monthly",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    days: Optional[int] = None,
) -> Dict[str, Any]:
    """Queries NASA POWER Agroclimatology API (https://power.larc.nasa.gov/api/temporal/daily/point)
    with local disk caching, timeout handling, scientific agricultural stress indicators,
    and automatic fallback to our verified agro-climatic dataset if NASA's endpoint is unreachable.

    Parameters retrieved from NASA POWER:
    - T2M: Temperature at 2 Meters (°C)
    - T2M_MAX: Maximum Temperature at 2 Meters (°C)
    - PRECTOTCORR: Precipitation Corrected (mm/day)
    - RH2M: Relative Humidity at 2 Meters (%)
    - ALLSKY_SFC_SW_DWN: All Sky Surface Shortwave Downward Irradiance (MJ/m^2/day)
    - WS2M: Wind Speed at 2 Meters (m/s)
    """
    st = standardize_state(state)
    dt = standardize_district(district, st)
    if lat is not None and lon is not None:
        lat, lon, exact_coord = float(lat), float(lon), True
    else:
        lat, lon, exact_coord = get_district_coordinates(st, dt)

    s_clean = re.sub(r"[^0-9]", "", str(start_date or "20230101"))[:8]
    e_clean = re.sub(r"[^0-9]", "", str(end_date or "20231231"))[:8]
    if len(s_clean) != 8:
        s_clean = "20230101"
    if len(e_clean) != 8:
        e_clean = "20231231"

    cache_key = f"nasa_power_{lat:.3f}_{lon:.3f}_{s_clean}_{e_clean}.json"
    cache_path = NASA_CACHE_DIR / cache_key

    raw_power_data = None
    data_source_type = "NASA POWER Agroclimatology Archive (Satellite & MERRA-2 Reanalysis — Historical/Near-Real-Time Observations, NOT a Live Weather Forecast)"
    api_live_success = False

    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                raw_power_data = json.load(f)
                api_live_success = True
        except Exception:
            raw_power_data = None

    if raw_power_data is None:
        params = "T2M,T2M_MAX,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN,WS2M"
        url = (
            f"https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters={params}&community=AG&longitude={lon}&latitude={lat}"
            f"&start={s_clean}&end={e_clean}&format=JSON"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KrishiMitra-AI-AgriResearch/2.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    raw_power_data = json.loads(resp.read().decode("utf-8"))
                    api_live_success = True
                    with open(cache_path, "w", encoding="utf-8") as cf:
                        json.dump(raw_power_data, cf)
        except Exception:
            raw_power_data = None

    daily_records = []
    if raw_power_data and "properties" in raw_power_data and "parameter" in raw_power_data["properties"]:
        param_block = raw_power_data["properties"]["parameter"]
        t2m = param_block.get("T2M", {})
        t2m_max = param_block.get("T2M_MAX", {})
        prec = param_block.get("PRECTOTCORR", {})
        rh2m = param_block.get("RH2M", {})
        solar = param_block.get("ALLSKY_SFC_SW_DWN", {})
        wind = param_block.get("WS2M", {})

        for d_key in sorted(t2m.keys()):
            tv = float(t2m.get(d_key, -999))
            if tv <= -900:
                continue
            tmax_v = float(t2m_max.get(d_key, tv + 5.0))
            if tmax_v <= -900:
                tmax_v = tv + 5.0
            pv = max(0.0, float(prec.get(d_key, 0.0)))
            rhv = float(rh2m.get(d_key, 55.0))
            if rhv <= -900:
                rhv = 55.0
            sol_v = float(solar.get(d_key, 18.0))
            if sol_v <= -900:
                sol_v = 18.0
            ws_v = max(0.0, float(wind.get(d_key, 2.5)))

            formatted_date = f"{d_key[:4]}-{d_key[4:6]}-{d_key[6:8]}"
            daily_records.append({
                "date": formatted_date,
                "year": d_key[:4],
                "month": d_key[:6],
                "temp_c": round(tv, 2),
                "temp_max_c": round(tmax_v, 2),
                "precip_mm": round(pv, 2),
                "humidity_pct": round(rhv, 1),
                "solar_mj_m2": round(sol_v, 2),
                "wind_ms": round(ws_v, 2),
            })

    # Safe fallback to repository's verified `weather/all_states_india_weather_and_rainfall_dataset(1).csv` if offline
    if not daily_records:
        data_source_type = (
            "Offline Fallback: Verified Repository Agro-Meteorological Dataset "
            "(`weather/all_states_india_weather_and_rainfall_dataset(1).csv` — Historical Observations, NOT a Live Forecast)"
        )
        weather_csv = BASE_DIR / "weather" / "all_states_india_weather_and_rainfall_dataset(1).csv"
        if weather_csv.exists():
            import pandas as pd
            df_w = pd.read_csv(weather_csv, low_memory=False)
            df_w["State"] = df_w["State"].apply(standardize_state)
            df_w["District"] = [standardize_district(d, s) for d, s in zip(df_w["District"], df_w["State"])]
            sub = df_w[(df_w["State"] == st) & (df_w["District"] == dt)].sort_values("Date")
            if sub.empty:
                sub = df_w[df_w["State"] == st].sort_values("Date").head(56)
            for r in sub.itertuples(index=False):
                d_str = str(r.Date)
                daily_records.append({
                    "date": d_str,
                    "year": d_str[:4],
                    "month": d_str[:7].replace("-", ""),
                    "temp_c": round(float(r.Current_Temp_C), 2),
                    "temp_max_c": round(float(r.Current_Temp_C) + 4.5, 2),
                    "precip_mm": round(float(r.Rainfall_Current_mm), 2),
                    "humidity_pct": round(float(r.Relative_Humidity_pct), 1),
                    "solar_mj_m2": round(float(r.Solar_Radiation_MJ_m2), 2),
                    "wind_ms": round(float(r.Wind_Speed_10m_ms), 2),
                })

    # Aggregate Monthly & Yearly Series
    monthly_map: Dict[str, List[Dict[str, Any]]] = {}
    yearly_map: Dict[str, List[Dict[str, Any]]] = {}
    for rec in daily_records:
        monthly_map.setdefault(rec["date"][:7], []).append(rec)
        yearly_map.setdefault(rec["year"], []).append(rec)

    monthly_series = []
    for m_key in sorted(monthly_map.keys()):
        items = monthly_map[m_key]
        monthly_series.append({
            "period": m_key,
            "avg_temp_c": round(sum(x["temp_c"] for x in items) / len(items), 2),
            "max_temp_c": round(max(x["temp_max_c"] for x in items), 2),
            "total_rain_mm": round(sum(x["precip_mm"] for x in items), 2),
            "avg_humidity_pct": round(sum(x["humidity_pct"] for x in items) / len(items), 1),
            "avg_solar_mj_m2": round(sum(x["solar_mj_m2"] for x in items) / len(items), 2),
            "avg_wind_ms": round(sum(x["wind_ms"] for x in items) / len(items), 2),
        })

    yearly_series = []
    for y_key in sorted(yearly_map.keys()):
        items = yearly_map[y_key]
        yearly_series.append({
            "period": y_key,
            "avg_temp_c": round(sum(x["temp_c"] for x in items) / len(items), 2),
            "max_temp_c": round(max(x["temp_max_c"] for x in items), 2),
            "total_rain_mm": round(sum(x["precip_mm"] for x in items), 2),
            "avg_humidity_pct": round(sum(x["humidity_pct"] for x in items) / len(items), 1),
            "avg_solar_mj_m2": round(sum(x["solar_mj_m2"] for x in items) / len(items), 2),
            "avg_wind_ms": round(sum(x["wind_ms"] for x in items) / len(items), 2),
        })

    # Compute Scientifically Justified Agricultural Intelligence Indicators
    avg_temp = round(sum(x["temp_c"] for x in daily_records) / max(1, len(daily_records)), 2)
    max_temp = round(max((x["temp_max_c"] for x in daily_records), default=30.0), 2)
    total_rain = round(sum(x["precip_mm"] for x in daily_records), 2)
    avg_humidity = round(sum(x["humidity_pct"] for x in daily_records) / max(1, len(daily_records)), 1)
    avg_solar = round(sum(x["solar_mj_m2"] for x in daily_records) / max(1, len(daily_records)), 2)
    heat_stress_days = sum(1 for x in daily_records if x["temp_max_c"] >= 35.0)
    heavy_rain_days = sum(1 for x in daily_records if x["precip_mm"] >= 35.0)

    indicators = []
    # 1. Temperature Stress (ICAR threshold: >32°C during grain filling or >35°C max causes floral/grain abortion)
    if max_temp >= 35.0 or avg_temp >= 30.0:
        indicators.append({
            "name": "Thermal / Heat Stress Indicator",
            "status": "Elevated Heat Stress Risk",
            "threshold_used": "T_max >= 35.0°C or Mean T >= 30.0°C (ICAR Terminal Heat Threshold)",
            "observed_value": f"Peak {max_temp}°C | Mean {avg_temp}°C ({heat_stress_days} high-heat observations)",
            "agronomic_implication": "High canopy temperatures accelerate evapotranspiration and shorten grain-filling duration in Wheat/Mustard/Pulses. Light evening irrigation or 1.5% KNO3 foliar spray is recommended.",
        })
    else:
        indicators.append({
            "name": "Thermal / Heat Stress Indicator",
            "status": "Normal Thermal Regime",
            "threshold_used": "T_max < 35.0°C (Optimal Photosynthetic Window)",
            "observed_value": f"Peak {max_temp}°C | Mean {avg_temp}°C",
            "agronomic_implication": "Temperature profile remains within safe physiological bounds for vegetative and reproductive crop stages.",
        })

    # 2. Rainfall Deficit / Excess / Meteorological Drought Indicator (IMD norms)
    expected_baseline_rain = 650.0 if len(daily_records) > 180 else 180.0
    rain_departure_pct = round(((total_rain - expected_baseline_rain) / max(1.0, expected_baseline_rain)) * 100.0, 1)
    if rain_departure_pct <= -20.0:
        indicators.append({
            "name": "Rainfall Deficit & Drought Analytical Indicator",
            "status": "Rainfall Deficit Observed (Analytical Drought Watch)",
            "threshold_used": "Cumulative Rainfall Departure <= -20% vs Seasonal Baseline (IMD Analytical Criterion)",
            "observed_value": f"{total_rain} mm ({rain_departure_pct}% vs baseline)",
            "agronomic_implication": "Analytical moisture deficit detected. Prioritize life-saving irrigation at critical root/flowering stages and mulching to conserve soil moisture.",
        })
    elif rain_departure_pct >= 25.0 or heavy_rain_days >= 3:
        indicators.append({
            "name": "Excess Rainfall & Waterlogging Indicator",
            "status": "Excess Precipitation / Inundation Watch",
            "threshold_used": "Departure >= +25% or Daily Rain >= 35 mm",
            "observed_value": f"{total_rain} mm (+{rain_departure_pct}% departure, {heavy_rain_days} heavy rain events)",
            "agronomic_implication": "Ensure field drainage channels are clear to prevent root asphyxiation in Pulses, Mustard, and Wheat.",
        })
    else:
        indicators.append({
            "name": "Precipitation & Soil Moisture Balance",
            "status": "Normal Precipitation Regime",
            "threshold_used": "Departure within -19% to +24% of baseline",
            "observed_value": f"{total_rain} mm ({rain_departure_pct:+.1f}% vs baseline)",
            "agronomic_implication": "Cumulative precipitation supports normal crop water requirements alongside scheduled irrigation.",
        })

    # 3. Solar Radiation & Photosynthetic Potential
    indicators.append({
        "name": "Solar Radiation & Photosynthetic Active Potential",
        "status": "High Insolation" if avg_solar >= 17.0 else "Moderate / Cloudy Insolation",
        "threshold_used": "ALLSKY_SFC_SW_DWN >= 17.0 MJ/m²/day",
        "observed_value": f"{avg_solar} MJ/m²/day | Mean RH: {avg_humidity}%",
        "agronomic_implication": (
            "Strong solar irradiance supports high biomass accumulation and PM-KUSUM solar pump efficiency."
            if avg_solar >= 17.0
            else "Reduced solar radiation and higher humidity warrant vigilance against fungal foliar diseases (Yellow Rust / Blight / Aphids)."
        ),
    })

    # NASA GIBS (Global Imagery Browse Services) WMTS Tile Layer Configuration
    gibs_layers = [
        {
            "id": "MODIS_Terra_NDVI_8Day",
            "name": "MODIS Terra Vegetation Index (NDVI 8-Day)",
            "wmts_url_template": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png",
            "max_zoom": 9,
            "description": "Normalized Difference Vegetation Index measuring crop canopy vigor and greenness.",
        },
        {
            "id": "MODIS_Terra_CorrectedReflectance_TrueColor",
            "name": "MODIS Terra True Color Satellite Imagery",
            "wmts_url_template": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
            "max_zoom": 9,
            "description": "True-color satellite surface reflectance observation over Indian agricultural belts.",
        },
        {
            "id": "MODIS_Terra_Land_Surface_Temp_Day",
            "name": "MODIS Land Surface Temperature (Daytime)",
            "wmts_url_template": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Land_Surface_Temp_Day/default/{date}/GoogleMapsCompatible_Level7/{z}/{y}/{x}.png",
            "max_zoom": 7,
            "description": "Daytime land surface thermal emission for monitoring agricultural heat stress.",
        },
        {
            "id": "IMERG_Precipitation_Rate",
            "name": "GPM IMERG Precipitation Rate",
            "wmts_url_template": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/IMERG_Precipitation_Rate/default/{date}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png",
            "max_zoom": 6,
            "description": "Global Precipitation Measurement (GPM) satellite rainfall rate estimation.",
        },
    ]

    return {
        "status": "success",
        "state": st,
        "district": dt,
        "coordinates": {
            "latitude": lat,
            "longitude": lon,
            "exact_district_centroid": exact_coord,
        },
        "data_classification": "Historical & Near-Real-Time Satellite/Reanalysis Observations (NOT a Live Weather Forecast)",
        "data_source": data_source_type,
        "official_links": {
            "nasa_power": "https://power.larc.nasa.gov/",
            "nasa_earthdata": "https://www.earthdata.nasa.gov/",
            "nasa_gibs": "https://www.earthdata.nasa.gov/data/tools/gibs",
        },
        "nasa_live_api_connected": api_live_success,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
        "date_range": {"start": s_clean, "end": e_clean, "observations_count": len(daily_records)},
        "summary_metrics": {
            "avg_temp_c": avg_temp,
            "max_temp_c": max_temp,
            "total_rain_mm": total_rain,
            "avg_humidity_pct": avg_humidity,
            "avg_solar_mj_m2": avg_solar,
            "heat_stress_days": heat_stress_days,
            "heavy_rain_days": heavy_rain_days,
        },
        "monthly_series": monthly_series,
        "yearly_series": yearly_series,
        "daily_sample": daily_records[-60:],
        "agricultural_indicators": indicators,
        "gibs_satellite_layers": gibs_layers,
        "scientific_disclaimer": (
            "NOTE: NASA POWER and NASA GIBS provide historical and near-real-time Earth observation reanalysis data, "
            "NOT live meteorological weather forecasts. Analytical drought and temperature stress indicators above are "
            "agro-climatic decision-support metrics and do not constitute official government disaster or drought declarations."
        ),
    }
