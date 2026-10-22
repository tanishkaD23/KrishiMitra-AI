"""KrishiMitra AI - Interactive Prototype & KrishiSathi Voice Assistant

Focused on Western Uttar Pradesh Rabi Season (Wheat & Mustard).
"""

import sys
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import streamlit.components.v1 as components
from config.settings import CONFIG
from src.yield_model.predict import YieldPredictor
from src.advisory.agronomic_rules import AgronomicAdvisor
from src.schemes.eligibility_engine import SchemeEligibilityEngine
from src.krishisathi.voice_agent import KrishiSathiAgent
from src.krishisathi.tts import get_browser_speech_html

# Page configuration
st.set_page_config(
    page_title="KrishiMitra AI | कृषिमित्र",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for high contrast and rural readability
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        color: #1e3a1e;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .alert-box {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize engines
@st.cache_resource
def load_engines():
    predictor = YieldPredictor()
    schemes_engine = SchemeEligibilityEngine()
    agent = KrishiSathiAgent()
    return predictor, schemes_engine, agent

predictor, schemes_engine, voice_agent = load_engines()

# Header
st.markdown('<div class="main-title">🌾 KrishiMitra AI (कृषिमित्र)</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Plot-Level Yield Forecasting, Precision Advisory & Scheme Delivery for Smallholders | <b>Pilot: Western Uttar Pradesh</b></div>',
    unsafe_allow_html=True,
)

# Sidebar: Farmer & Plot Inputs
with st.sidebar:
    st.header("📍 किसान और खेत का विवरण (Plot Details)")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        crop = st.selectbox("फसल (Crop)", CONFIG.crops, index=0)
    with col_s2:
        district = st.selectbox("जिला (District)", CONFIG.districts, index=0)

    plot_acres = st.number_input(
        "खेत का क्षेत्रफल (Plot Size in Acres)",
        min_value=0.25,
        max_value=25.0,
        value=2.0,
        step=0.5,
        help="1 एकड़ ≈ 0.40 हेक्टेयर। भारत में सीमांत किसान 2.47 एकड़ से कम भूमि रखते हैं।",
    )

    soil_type = st.selectbox("मिट्टी का प्रकार (Soil Type)", CONFIG.soil_types, index=0)
    irrigation_source = st.selectbox(
        "सिंचाई का साधन (Irrigation Source)", CONFIG.irrigation_sources, index=0
    )
    sowing_window = st.selectbox(
        "बुवाई का समय (Sowing Window)",
        [
            "Early Rabi (Oct 15 - Oct 31)",
            "Timely Sown (Nov 01 - Nov 20)",
            "Late Sown (Nov 21 - Dec 15)",
        ],
        index=1,
    )

    with st.expander("🧪 उर्वरक और मौसम विवरण (Nutrients & Weather)"):
        st.caption("क्षेत्रीय मानक औसतन स्वतः भरे गए हैं")
        n_val = st.slider("नाइट्रोजन (N) kg/एकड़", 10.0, 80.0, 48.0 if crop == "Wheat" else 32.0)
        p_val = st.slider("फॉस्फोरस (P) kg/एकड़", 5.0, 40.0, 22.0 if crop == "Wheat" else 16.0)
        k_val = st.slider("पोटाश (K) kg/एकड़", 0.0, 30.0, 15.0 if crop == "Wheat" else 8.0)
        rainfall_val = st.slider("अनुमानित मौसमी वर्षा (mm)", 10.0, 150.0, 65.0)
        march_temp_val = st.slider(
            "मार्च अधिकतम तापमान (°C) [पछुआ गर्मी]", 25.0, 40.0, 31.5,
            help="मार्च में 32°C से अधिक तापमान गेहूं में समय से पूर्व परिपक्वता ला सकता है।"
        )

# Prepare farmer input dict
farmer_input = {
    "crop": crop,
    "district": district,
    "plot_acres": plot_acres,
    "soil_type": soil_type,
    "irrigation_source": irrigation_source,
    "sowing_window": sowing_window,
    "seasonal_rainfall_mm": rainfall_val,
    "march_max_temp_c": march_temp_val,
    "nitrogen_kg_acre": n_val,
    "phosphorus_kg_acre": p_val,
    "potassium_kg_acre": k_val,
    "state": "Uttar Pradesh",
}

# Run Yield Prediction
yield_result = predictor.predict(farmer_input)

# Run Agronomic Advisory
advisory_result = AgronomicAdvisor.get_advisory(farmer_input, yield_result)

# Run Government Scheme Evaluation
eligible_schemes = schemes_engine.evaluate_eligibility(farmer_input)

# Prepare context for KrishiSathi
krishisathi_context = {
    "crop": crop,
    "district": district,
    "plot_acres": plot_acres,
    "predicted_yield": yield_result["predicted_yield_per_acre"],
    "alerts_hi": advisory_result["alerts_hi"],
    "advisories_hi": advisory_result["advisories_hi"],
    "eligible_schemes": eligible_schemes,
}

# --- SECTION 1: KRISHISATHI SIGNATURE VOICE BANNER ---
st.markdown("### 🎙️ KrishiSathi (कृषिसाथी): सुनिए अपनी फसल की ताजा स्थिति")
speech_html = get_browser_speech_html(advisory_result["hindi_voice_script"], auto_play=False)
components.html(speech_html, height=110)

# --- SECTION 2: YIELD FORECAST & PLOT PERFORMANCE ---
st.markdown("---")
col_y1, col_y2, col_y3, col_y4 = st.columns(4)

with col_y1:
    st.metric(
        label="🎯 अनुमानित पैदावार (Yield / Acre)",
        value=f"{yield_result['predicted_yield_per_acre']} Q/Acre",
        delta=f"{yield_result['performance_vs_regional_mean_pct']}% vs जिला औसत",
    )
with col_y2:
    st.metric(
        label="📦 कुल अनुमानित उत्पादन (Total Harvest)",
        value=f"{yield_result['total_harvest_quintals']} क्विंटल",
        help=f"आपके {plot_acres} एकड़ खेत का कुल अनुमानित उत्पादन।",
    )
with col_y3:
    ci = yield_result["confidence_interval_90"]
    st.metric(
        label="📊 90% विश्वसनीयता दायरा",
        value=f"{ci['lower']} - {ci['upper']} Q",
        help="90% संभावना है कि वास्तविक उत्पादन इस सीमा में रहेगा।",
    )
with col_y4:
    farmer_cat = schemes_engine.classify_farmer_category(plot_acres)
    st.metric(
        label="👨‍🌾 किसान श्रेणी (Land Category)",
        value=f"{farmer_cat} ({'सीमांत' if farmer_cat == 'Marginal' else 'लघु'})",
    )

# --- SECTION 3: TABS FOR ADVISORY, SCHEMES, AND KRISHISATHI CHAT ---
tab_advisory, tab_schemes, tab_chat = st.tabs([
    "🌱 व्यक्तिगत कृषि सलाह (Crop Advisory)",
    "🏛️ सरकारी योजनाएं (Govt Schemes)",
    "💬 कृषिसाथी से पूछें (Ask KrishiSathi Voice/Chat)",
])

with tab_advisory:
    # Warnings and critical alerts
    if advisory_result["alerts_hi"]:
        for alert_hi, alert_en in zip(advisory_result["alerts_hi"], advisory_result["alerts_en"]):
            st.warning(f"⚠️ **महत्वपूर्ण चेतावनी**: {alert_hi}\n\n*({alert_en})*")

    st.subheader("📋 चरणबद्ध सिफारिशें (Step-by-Step Recommendations)")
    for i, (adv_hi, adv_en) in enumerate(
        zip(advisory_result["advisories_hi"], advisory_result["advisories_en"]), 1
    ):
        with st.container():
            st.markdown(f"**{i}. {adv_hi}**")
            st.caption(adv_en)

with tab_schemes:
    st.subheader(f"✨ आपके लिए {len(eligible_schemes)} सरकारी योजनाएं उपलब्ध हैं")
    st.info("ये योजनाएं आपके खेत के आकार, फसल और जिले के आधार पर स्वतः जांची गई हैं।")

    for s in eligible_schemes:
        with st.expander(f"🔹 {s['name_hi']} ({s['category']})", expanded=True):
            col_sc1, col_sc2 = st.columns([3, 1])
            with col_sc1:
                st.markdown(f"**लाभ (Benefits)**: {s['benefit_hi']}")
                st.caption(f"English: {s['benefit_en']}")
                st.markdown("**आवश्यक दस्तावेज (Required Documents)**:")
                for doc in s["documents_required"]:
                    st.markdown(f"- 📄 {doc}")
            with col_sc2:
                if s["portal_url"]:
                    st.link_button("🌐 आवेदन पोर्टल", s["portal_url"])

with tab_chat:
    st.subheader("🗣️ कृषिसाथी से सवाल पूछें (Ask Any Question in Hindi)")
    st.caption("आप बोलकर या लिखकर अपनी फसल, सिंचाई, खाद, कीट या योजनाओं के बारे में पूछ सकते हैं।")

    # Sample prompt buttons
    st.markdown("**त्वरित सवाल (Sample Quick Questions):**")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    preset_q = ""
    with q_col1:
        if st.button("💧 सिंचाई कब करें?"):
            preset_q = "मुझे अपनी फसल में सिंचाई कब करनी चाहिए?"
    with q_col2:
        if st.button("🧪 खाद कितनी डालें?"):
            preset_q = "खाद और यूरिया की सही मात्रा क्या है?"
    with q_col3:
        if st.button("🐛 कीट-रोग से बचाव?"):
            preset_q = "मेरी फसल में कीट और फफूंद से बचाव कैसे करें?"
    with q_col4:
        if st.button("🏛️ कौन सी योजना मिलेगी?"):
            preset_q = "मुझे कौन सी सरकारी योजनाओं का लाभ मिल सकता है?"

    user_query = st.text_input(
        "अपना सवाल यहां लिखें (या ऊपर दिए गए बटन दबाएं):",
        value=preset_q,
        placeholder="जैसे: मेरी पैदावार कैसे बढ़ाएं?",
    )

    if user_query:
        with st.spinner("कृषिसाथी विचार कर रहे हैं..."):
            answer = voice_agent.ask(user_query, krishisathi_context)

        st.markdown(f"### 🤖 कृषिसाथी का जवाब:")
        st.success(answer)

        # Audio playback for answer
        answer_audio_html = get_browser_speech_html(answer, auto_play=True)
        components.html(answer_audio_html, height=110)
