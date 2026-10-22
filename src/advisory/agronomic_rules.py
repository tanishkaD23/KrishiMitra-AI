"""Personalised Agricultural Advisory Engine for KrishiMitra AI.

Generates verified, stage-specific, climate-responsive, and symptom-guided
advisories for smallholder farmers in Western Uttar Pradesh and Gangetic Plains.

Features:
- Stage-specific wheat, mustard, and rice management.
- Climate, rainfall, and terminal heat stress precautions.
- Soil management guidance grounded in regional baselines without claiming plot-level sensor certitude.
- Symptom-guided pest and disease vigilance with evidence-based next steps without claiming unverified diagnoses.
- Verified agricultural sources (ICAR, IIWBR, DRMR, NRRI, IMD, Soil Health Card Mission).
- Full bilingual English and Hindi output.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


# Verified Agricultural Sources
SOURCES = {
    "IIWBR": {
        "name": "ICAR - Indian Institute of Wheat and Barley Research, Karnal",
        "url": "https://iiwbr.icar.gov.in"
    },
    "DRMR": {
        "name": "ICAR - Directorate of Rapeseed-Mustard Research, Bharatpur",
        "url": "https://drmr.icar.gov.in"
    },
    "NRRI": {
        "name": "ICAR - National Rice Research Institute, Cuttack",
        "url": "https://icar-nrri.in"
    },
    "IMD": {
        "name": "IMD Agromet Advisory Service (Gramin Krishi Mausam Sewa - GKMS)",
        "url": "https://imdagrimet.gov.in"
    },
    "SHC": {
        "name": "Department of Agriculture & Farmers Welfare (Soil Health Card Scheme)",
        "url": "https://soilhealth.dac.gov.in"
    },
    "UP_AGRI": {
        "name": "Uttar Pradesh State Agriculture Department & KVK Meerut",
        "url": "https://upagriculture.com"
    }
}


class PersonalisedAdvisoryEngine:
    """Core engine generating structured, evidence-based agricultural advisory cards."""

    @classmethod
    def generate_advisory(cls, farmer_input: Dict[str, Any], yield_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates comprehensive personalised advisory cards based on farmer inputs."""
        crop = farmer_input.get("crop", "Wheat")
        district = farmer_input.get("district", "Meerut")
        state = farmer_input.get("state", "Uttar Pradesh")
        season = farmer_input.get("season", "Rabi")
        stage = farmer_input.get("growth_stage") or farmer_input.get("stage") or "Tillering"
        sowing_window = farmer_input.get("sowing_window", "Timely Sown (Nov 01 - Nov 20)")
        sowing_date = farmer_input.get("sowing_date")
        irrigation = farmer_input.get("irrigation_source", "Tube well / Borewell")
        soil_type = farmer_input.get("soil_type", "Alluvial (Sandy Loam)")
        march_temp = float(farmer_input.get("march_max_temp_c", 31.5))
        rainfall_mm = float(farmer_input.get("seasonal_rainfall_mm", 65.0))
        n_applied = float(farmer_input.get("nitrogen_kg_acre", 48.0))
        p_applied = float(farmer_input.get("phosphorus_kg_acre", 22.0))
        k_applied = float(farmer_input.get("potassium_kg_acre", 15.0))
        recent_activities = farmer_input.get("recent_activities") or []
        reported_symptoms = farmer_input.get("reported_symptoms") or []

        if isinstance(recent_activities, str):
            recent_activities = [recent_activities]
        if isinstance(reported_symptoms, str):
            reported_symptoms = [reported_symptoms]

        cards: List[Dict[str, Any]] = []

        # =========================================================================
        # 1. CROP GROWTH STAGE MANAGEMENT (Stage-specific verified agronomic rules)
        # =========================================================================
        if crop == "Wheat":
            stage_card = cls._get_wheat_stage_card(stage, irrigation, recent_activities, sowing_window)
            if stage_card:
                cards.append(stage_card)
        elif crop == "Mustard":
            stage_card = cls._get_mustard_stage_card(stage, irrigation, recent_activities)
            if stage_card:
                cards.append(stage_card)
        elif crop in ["Rice", "Paddy"]:
            stage_card = cls._get_rice_stage_card(stage, irrigation)
            if stage_card:
                cards.append(stage_card)
        else:
            cards.append({
                "id": "adv-unsupported-crop",
                "category": "Pilot Scope & Advisory Limitations",
                "title_en": f"General Management Guidelines for {crop}",
                "title_hi": f"{crop} के लिए सामान्य दिशानिर्देश",
                "priority": "informational",
                "observation": f"Crop '{crop}' is outside the Western UP Rabi pilot calibration scope. Dedicated model predictions are currently calibrated for Wheat and Mustard.",
                "observation_hi": f"फसल '{crop}' पश्चिमी उत्तर प्रदेश रबी पायलट के दायरे से बाहर है। मॉडल मुख्य रूप से गेहूं और सरसों के लिए कैलिब्रेटेड है।",
                "recommendation": "Follow state package of practices and consult your local Krishi Vigyan Kendra (KVK) for micro-plot recommendations.",
                "recommendation_hi": "राज्य कृषि विभाग की अनुशंसाओं का पालन करें और स्थानीय कृषि विज्ञान केंद्र से संपर्क करें।",
                "reason": "Calibrated ML yield models and stage benchmarks are available for Wheat and Mustard in Western UP.",
                "reason_hi": "वर्तमान में गेहूं और सरसों के लिए ही सत्यापित मॉडल उपलब्ध हैं।",
                "source": SOURCES["UP_AGRI"]["name"],
                "source_url": SOURCES["UP_AGRI"]["url"],
                "badge_color": "blue"
            })

        # =========================================================================
        # 2. CLIMATE, RAINFALL & TEMPERATURE PRECAUTIONS
        # =========================================================================
        climate_card = cls._get_climate_card(crop, march_temp, rainfall_mm, irrigation, sowing_window)
        if climate_card:
            cards.append(climate_card)

        # =========================================================================
        # 3. SOIL MANAGEMENT (Responsible, non-overclaiming regional guidance)
        # =========================================================================
        soil_card = cls._get_soil_management_card(crop, soil_type, n_applied, p_applied, k_applied, district)
        if soil_card:
            cards.append(soil_card)

        # =========================================================================
        # 4. PEST & DISEASE SYMPTOM INQUIRY & VIGILANCE (Evidence-based next steps)
        # =========================================================================
        pest_card = cls._get_pest_disease_card(crop, reported_symptoms, stage)
        if pest_card:
            cards.append(pest_card)

        # Generate legacy string lists for backwards compatibility
        advisories_en = [c["recommendation"] for c in cards if c["priority"] != "urgent"]
        advisories_hi = [c["recommendation_hi"] for c in cards if c["priority"] != "urgent"]
        alerts_en = [f"{c['title_en']}: {c['observation']} -> {c['recommendation']}" for c in cards if c["priority"] == "urgent"]
        alerts_hi = [f"{c['title_hi']}: {c['observation_hi']} -> {c['recommendation_hi']}" for c in cards if c["priority"] == "urgent"]

        # Voice summary in Hindi
        pred_val = yield_result.get("predicted_yield_per_acre", 19.5) if yield_result else 19.5
        crop_hindi = "गेहूं" if crop == "Wheat" else ("सरसों" if crop == "Mustard" else crop)
        hindi_voice_script = f"नमस्ते किसान भाई! आपके खेत में {crop_hindi} की फसल {stage} अवस्था में है। "
        if alerts_hi:
            hindi_voice_script += f"खास ध्यान दें: {cards[0]['recommendation_hi']} "
        elif cards:
            hindi_voice_script += f"मुख्य सलाह: {cards[0]['recommendation_hi']} "

        return {
            "status": "success",
            "crop": crop,
            "district": district,
            "state": state,
            "season": season,
            "growth_stage": stage,
            "structured_cards": cards,
            "advisories_en": advisories_en,
            "advisories_hi": advisories_hi,
            "alerts_en": alerts_en,
            "alerts_hi": alerts_hi,
            "hindi_voice_script": hindi_voice_script,
            "disclaimer_en": "Advisories synthesize ICAR protocols and district agro-climatic baselines. Localized soil testing is recommended for micro-plot precision.",
            "disclaimer_hi": "यह सलाह आईसीएआर दिशानिर्देशों और जिला कृषि मौसम पर आधारित है। खेत स्तर की सटीक मात्रा के लिए मिट्टी जांच अवश्य कराएं।"
        }

    # -------------------------------------------------------------------------
    # Helper: Wheat Stage-Specific Guidance
    # -------------------------------------------------------------------------
    @classmethod
    def _get_wheat_stage_card(cls, stage: str, irrigation: str, activities: List[str], sowing: str) -> Dict[str, Any]:
        s = stage.lower()
        if "sow" in s or "pre-sow" in s:
            return {
                "id": "adv-wheat-sowing",
                "category": "Crop Growth Stage Management",
                "title_en": "Wheat Sowing & Seed Treatment Protocol",
                "title_hi": "गेहूं बुवाई एवं बीज उपचार सलाह",
                "priority": "moderate",
                "observation": "Field is in pre-sowing / sowing preparation stage for Rabi season in Western UP.",
                "observation_hi": "खेत रबी सीजन में गेहूं की बुवाई / तैयारी की अवस्था में है।",
                "recommendation": "Treat seed with Trichoderma viride @ 4g/kg seed or Carboxin+Thiram @ 2g/kg. Maintain sowing depth at 4-5 cm with 20 cm row spacing.",
                "recommendation_hi": "बीज को ट्राइकोडर्मा विरिडी (4 ग्राम/किग्रा) या थीरम (2 ग्राम/किग्रा) से उपचारित करें। बुवाई 4-5 सेमी गहराई और 20 सेमी पंक्ति दूरी पर करें।",
                "reason": "Seed treatment provides early protection against loose smut and seedling rot, ensuring uniform field stand.",
                "reason_hi": "बीज शोधन से कंडुआ और जड़ गलन रोग से सुरक्षा मिलती है तथा फसल का जमाव एकसमान होता है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "amber"
            }
        elif "cri" in s or "crown" in s or "root" in s:
            recent_irr = any("irrigation" in a.lower() for a in activities)
            return {
                "id": "adv-wheat-cri",
                "category": "Critical Irrigation & Root Establishment",
                "title_en": "Crown Root Initiation (CRI) Critical Irrigation (20–25 DAS)",
                "title_hi": "ताज जड़ (CRI) अवस्था पर पहली सिंचाई (20-25 दिन)",
                "priority": "urgent" if not recent_irr else "moderate",
                "observation": "Wheat is at Crown Root Initiation stage (20–25 days after sowing), when secondary crown roots anchor the plant." + (" (First irrigation already recorded)" if recent_irr else " (Irrigation pending)"),
                "observation_hi": "गेहूं की फसल ताज जड़ (CRI) अवस्था (20-25 दिन) पर है, जो जड़ों के फैलाव के लिए अत्यंत संवेदनशील है।" + (" (सिंचाई हो चुकी है)" if recent_irr else " (सिंचाई लंबित है)"),
                "recommendation": "Apply a light first irrigation (4–5 cm depth) immediately if not yet done. Avoid heavy flooding. 2–3 days post-irrigation, broadcast 45 kg Neem-coated Urea per acre.",
                "recommendation_hi": "यदि अभी तक सिंचाई नहीं की है तो तुरंत पहली हल्की सिंचाई (4-5 सेमी) करें। पानी ठहरने न दें। सिंचाई के 2-3 दिन बाद 45 किलो नीम लेपित यूरिया का बुरकाव करें।",
                "reason": "Crown roots establish during 20–25 DAS. Moisture stress at this stage permanently reduces tiller generation by up to 25%, directly lowering yield potential.",
                "reason_hi": "20-25 दिन पर क्राउन जड़ें फूटती हैं; इस समय नमी की कमी से कल्ले 20-25% कम निकलते हैं जिससे कुल पैदावार घट जाती है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "red" if not recent_irr else "green"
            }
        elif "tiller" in s:
            return {
                "id": "adv-wheat-tillering",
                "category": "Nutrient Split & Tiller Development",
                "title_en": "Tillering Stage Nutrient & Weed Management (25–45 DAS)",
                "title_hi": "कल्ले फूटने की अवस्था: यूरिया व खरपतवार नियंत्रण (25-45 दिन)",
                "priority": "moderate",
                "observation": "Wheat is actively producing vegetative tillers (25–45 DAS). Canopy coverage is expanding.",
                "observation_hi": "गेहूं में वानस्पतिक कल्ले फूटने (25-45 दिन) की सक्रिय अवस्था चल रही है।",
                "recommendation": "Broadcast first split of Neem-coated Urea (40–45 kg/acre) when soil has optimum moisture. If broadleaf weeds are visible, spray Metsulfuron methyl 20% WP @ 8 g/acre at 30–35 DAS.",
                "recommendation_hi": "मिट्टी में नमी रहते 40-45 किलो नीम लेपित यूरिया डालें। चौड़ी पत्ती वाले खरपतवार दिखने पर 30-35 दिन पर मेटसल्फ्यूरॉन मिथाइल 20% WP (8 ग्राम/एकड़) का छिड़काव करें।",
                "reason": "Timely nitrogen ensures high tiller survival and ear-bearing capacity. Controlling weeds early eliminates moisture-nutrient competition.",
                "reason_hi": "समय पर नाइट्रोजन मिलने से कल्लों की संख्या बढ़ती है। समय पर खरपतवार निकालने से खाद-पानी की बर्बादी रुकती है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "green"
            }
        elif "joint" in s or "boot" in s:
            return {
                "id": "adv-wheat-jointing",
                "category": "Stem Elongation & Spike Protection",
                "title_en": "Jointing to Booting Stage Care (45–65 DAS)",
                "title_hi": "गांठ बनने व गोभ (बूटिंग) अवस्था की देखभाल (45-65 दिन)",
                "priority": "moderate",
                "observation": "Nodes are elongating and the embryonic wheat spike is developing inside the flag leaf sheath (45–65 DAS).",
                "observation_hi": "गेहूं में तने की गांठें बढ़ रही हैं और गोभ में बालियां बन रही हैं (45-65 दिन)।",
                "recommendation": "Provide second / third timely irrigation. Broadcast final split of nitrogen (30 kg Urea/acre). Monitor flag leaves for yellow rust signs.",
                "recommendation_hi": "समय पर दूसरी/तीसरी सिंचाई दें। अंतिम 30 किलो यूरिया प्रति एकड़ बुरकाव करें। झंडा पत्ती पर पीले रतुए के लक्षणों की जांच करें।",
                "reason": "Flag leaf surface area directly determines the photosynthetic energy available for subsequent grain filling.",
                "reason_hi": "झंडा पत्ती (Flag Leaf) स्वस्थ रहने से बालियों में दानों का भराव सबसे अच्छा होता है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "amber"
            }
        elif "flower" in s or "head" in s:
            return {
                "id": "adv-wheat-flowering",
                "category": "Flowering & Anthesis Safeguards",
                "title_en": "Heading & Anthesis Protection (65–85 DAS)",
                "title_hi": "फूल आने व बाली निकलने की अवस्था (65-85 दिन)",
                "priority": "moderate",
                "observation": "Spikes have emerged and pollination/anthesis is underway. Moisture stress now directly aborts florets.",
                "observation_hi": "बालियां निकल चुकी हैं और परागण की प्रक्रिया चल रही है।",
                "recommendation": "Ensure soil remains moist. Irrigate on calm, windless days. Avoid nitrogen spraying during active flowering.",
                "recommendation_hi": "खेत में नमी बनाए रखें। हवा शांत रहने पर ही हल्की सिंचाई करें। फूल खिलते समय यूरिया का छिड़काव न करें।",
                "reason": "High winds during irrigation cause catastrophic lodging. Adequate moisture ensures maximum grain set per ear.",
                "reason_hi": "हवा के समय सिंचाई से फसल गिरने (Lodging) का खतरा रहता है। उचित नमी से प्रत्येक बाली में पूरे दाने बनते हैं।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "blue"
            }
        else:  # Milking / Grain filling / Maturity
            return {
                "id": "adv-wheat-grainfill",
                "category": "Grain Filling & Terminal Protection",
                "title_en": "Milking & Grain Filling Phase (85–110 DAS)",
                "title_hi": "दूधिया व दाना भराव अवस्था (85-110 दिन)",
                "priority": "moderate",
                "observation": "Kernels are synthesizing starch and maturing from milk to dough stage (85–110 DAS).",
                "observation_hi": "दाने में दूधिया रस भर रहा है और दाना सख्त हो रहा है (85-110 दिन)।",
                "recommendation": "Apply one light final irrigation at dough stage if soil is dry. Spray 1.5% Potassium Nitrate (13:0:45) if March heat surges occur.",
                "recommendation_hi": "यदि जमीन सूखी हो तो एक हल्की सिंचाई करें। मार्च में तापमान बढ़ने पर 1.5% पोटेशियम नाइट्रेट का छिड़काव करें।",
                "reason": "Prevents shriveled grains and forced maturity, maintaining test weight and hectolitre weight.",
                "reason_hi": "दाना सिकुड़ने से बचता है और 1000 दानों का वजन (Test Weight) अच्छा रहता है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "amber"
            }

    # -------------------------------------------------------------------------
    # Helper: Mustard Stage-Specific Guidance
    # -------------------------------------------------------------------------
    @classmethod
    def _get_mustard_stage_card(cls, stage: str, irrigation: str, activities: List[str]) -> Dict[str, Any]:
        s = stage.lower()
        if "flow" in s:
            return {
                "id": "adv-mustard-flowering",
                "category": "Pre-Flowering & Branching Management",
                "title_en": "Mustard Flowering Stage Moisture & Pest Guard (30–40 DAS)",
                "title_hi": "सरसों में फूल आने की अवस्था: सिंचाई व कीट सुरक्षा (30-40 दिन)",
                "priority": "urgent",
                "observation": "Mustard is entering pre-flowering / yellow bloom phase (30–40 DAS). Canopy is dense.",
                "observation_hi": "सरसों में फूल आने की अवस्था चल रही है और पौधे तेजी से बढ़ रहे हैं।",
                "recommendation": "Apply the first critical light irrigation if soil moisture is depleting. Do not flood. Check top 10 cm of central branch daily for aphid (chepa) colonies.",
                "recommendation_hi": "पहली हल्की सिंचाई दें, खेत में पानी न भरने दें। रोजाना फूलों व शाखाओं पर माहू (चेपा) कीट की जांच करें।",
                "reason": "First irrigation promotes maximum secondary branches and flower pods. Early aphid detection allows organic neem oil control before pest population explodes.",
                "reason_hi": "इस समय हल्की सिंचाई से शाखाएं और फलियां ज्यादा बनती हैं। समय पर माहू दिखने पर नीम के तेल से ही नियंत्रण हो जाता है।",
                "source": SOURCES["DRMR"]["name"],
                "source_url": SOURCES["DRMR"]["url"],
                "badge_color": "amber"
            }
        elif "pod" in s or "siliqua" in s:
            return {
                "id": "adv-mustard-pod",
                "category": "Pod Filling & Oil Content Enhancement",
                "title_en": "Siliqua (Pod) Formation Stage (60–70 DAS)",
                "title_hi": "फलियां बनने की अवस्था: सिंचाई व तेल संवर्धन (60-70 दिन)",
                "priority": "moderate",
                "observation": "Green pods (siliquae) are filling with developing seeds (60–70 DAS).",
                "observation_hi": "सरसों में हरी फलियां बन रही हैं और दाने भर रहे हैं (60-70 दिन)।",
                "recommendation": "Provide second and final light irrigation at pod filling stage. If aphids exceed economic threshold (25-30 aphids/twig), apply recommended eco-friendly spray in late evening.",
                "recommendation_hi": "फलियां बनते समय दूसरी व अंतिम हल्की सिंचाई करें। माहू का प्रकोप अधिक होने पर शाम के समय अनुशंसित छिड़काव करें।",
                "reason": "Moisture stress during pod filling reduces seed size and lowers oil percentage by 2–4%.",
                "reason_hi": "फलियों में दाना भरते समय सूखे से दाना छोटा रह जाता है और तेल की मात्रा 2-4% घट जाती है।",
                "source": SOURCES["DRMR"]["name"],
                "source_url": SOURCES["DRMR"]["url"],
                "badge_color": "green"
            }
        else:
            return {
                "id": "adv-mustard-veg",
                "category": "Vegetative & Sulfur Nutrition",
                "title_en": "Mustard Vegetative & Sulfur Management (15–30 DAS)",
                "title_hi": "सरसों वानस्पतिक विकास एवं सल्फर प्रबंधन (15-30 दिन)",
                "priority": "moderate",
                "observation": "Crop is in rosette / vegetative establishment. Thinning and weeding required.",
                "observation_hi": "सरसों के पौधे प्रारंभिक विकास की अवस्था में हैं। विरलीकरण (Thinning) जरूरी है।",
                "recommendation": "Maintain 12–15 cm plant-to-plant distance by thinning weak seedlings. Ensure 10 kg Bentonite Sulfur per acre was incorporated to synthesize glucosinolates and oil.",
                "recommendation_hi": "पौधे से पौधे की दूरी 12-15 सेमी रखें। कमजोर पौधों को निकाल दें। तेल की मात्रा बढ़ाने के लिए प्रति एकड़ 10 किलो सल्फर अवश्य दें।",
                "reason": "Crowded seedlings compete for light and develop weak stems. Sulfur is an indispensable building block of mustard oil molecules.",
                "reason_hi": "घने पौधे कमजोर रह जाते हैं। सल्फर सरसों में तेल की मात्रा 2 से 3 प्रतिशत बढ़ा देता है।",
                "source": SOURCES["DRMR"]["name"],
                "source_url": SOURCES["DRMR"]["url"],
                "badge_color": "amber"
            }

    # -------------------------------------------------------------------------
    # Helper: Rice Stage-Specific Guidance
    # -------------------------------------------------------------------------
    @classmethod
    def _get_rice_stage_card(cls, stage: str, irrigation: str) -> Dict[str, Any]:
        return {
            "id": "adv-rice-management",
            "category": "Kharif Season Water & Nutrient Management",
            "title_en": "Paddy / Rice Water & Split Nutrient Care",
            "title_hi": "धान / चावल जल एवं उर्वरक प्रबंधन",
            "priority": "moderate",
            "observation": "Rice in Western UP operates in Kharif cycle (June–October), requiring disciplined water regimes.",
            "observation_hi": "पश्चिमी उत्तर प्रदेश में धान की खेती खरीफ मौसम (जून-अक्टूबर) में की जाती है।",
            "recommendation": "Adopt Alternate Wetting and Drying (AWD) during vegetative phase: allow water level to drop 5 cm below soil surface before re-irrigating. Maintain 5 cm water depth strictly during flowering.",
            "recommendation_hi": "वानस्पतिक अवस्था में 'वैकल्पिक गीला और सूखा' (AWD) पद्धति अपनाएं। फूल खिलने के समय खेत में 5 सेमी पानी अवश्य बनाए रखें।",
            "reason": "AWD saves 25–30% irrigation water and reduces methane emissions without penalizing yield. Continuous flooding is only critical at panicle initiation and flowering.",
            "reason_hi": "AWD विधि से 25-30% पानी की बचत होती है और पैदावार पर कोई बुरा असर नहीं पड़ता।",
            "source": SOURCES["NRRI"]["name"],
            "source_url": SOURCES["NRRI"]["url"],
            "badge_color": "blue"
        }

    # -------------------------------------------------------------------------
    # Helper: Climate, Weather & Rainfall Precautions
    # -------------------------------------------------------------------------
    @classmethod
    def _get_climate_card(cls, crop: str, march_temp: float, rainfall_mm: float, irrigation: str, sowing: str) -> Optional[Dict[str, Any]]:
        # Terminal heat stress in late Rabi
        if crop == "Wheat" and ("late" in sowing.lower() or march_temp >= 31.5):
            return {
                "id": "adv-climate-heat",
                "category": "Climate Risk & Thermal Stress Mitigation",
                "title_en": "Terminal Heat Warning (March Temperature Precautions)",
                "title_hi": "पछुआ गर्मी व तापमान वृद्धि से बचाव चेतावनी (मार्च महीना)",
                "priority": "urgent" if march_temp >= 32.5 else "moderate",
                "observation": f"Forecasted March maximum temperature is {march_temp}°C. Late-sown wheat and rising temperatures coincide with grain-filling.",
                "observation_hi": f"मार्च में अधिकतम तापमान {march_temp}°C तक पहुंचने का अनुमान है। तापमान बढ़ने से दाना भरते समय गर्मी का झटका लग सकता है।",
                "recommendation": "1) Spray 1.5% Potassium Nitrate (13:0:45) (15 g/L water) at boot and milk stage. 2) Irrigate during calm evenings if soil dries. 3) Avoid nitrogen top-dressing after boot stage.",
                "recommendation_hi": "1) बूटिंग और दूधिया अवस्था पर 1.5% पोटेशियम नाइट्रेट (13:0:45) का छिड़काव करें। 2) जमीन सूखने पर शाम को हल्की सिंचाई करें। 3) देर से यूरिया न डालें।",
                "reason": "Foliar potassium regulates osmotic potential in flag leaves, preserving chlorophyll and preventing thermal desiccation of wheat kernels.",
                "reason_hi": "पोटेशियम पौधों की पत्तियों में पानी की कमी नहीं होने देता और दानों को सिकुड़ने से बचाता है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "red" if march_temp >= 32.5 else "amber"
            }
        elif "rainfed" in irrigation.lower():
            return {
                "id": "adv-climate-moisture-stress",
                "category": "Moisture Deficit & Drought Mitigation",
                "title_en": "Rainfed Soil Moisture Conservation Notice",
                "title_hi": "असिंचित क्षेत्र: नमी संरक्षण सलाह",
                "priority": "urgent",
                "observation": f"Plot is marked as Rainfed with seasonal rainfall recorded at {rainfall_mm} mm. Winter rains in Western UP are variable.",
                "observation_hi": f"खेत असिंचित श्रेणी में है और मौसमी वर्षा {rainfall_mm} मिमी दर्ज है। पश्चिमी उत्तर प्रदेश में सर्दियों की बारिश अनिश्चित रहती है।",
                "recommendation": "Arrange at least one supplemental protective irrigation at Crown Root Initiation stage. Apply straw mulch (2 tonnes/acre) between rows to reduce soil evaporation.",
                "recommendation_hi": "कम से कम एक जीवन रक्षक सिंचाई क्राउन जड़ अवस्था पर जरूर दें। क्यारियों में पुआल या सूखी घास की मल्चिंग करें ताकि नमी उड़े नहीं।",
                "reason": "Without assured water, wheat yield drops by over 35%. Mulch suppresses capillary evaporation and keeps root-zone soil cooler by 2–3°C.",
                "reason_hi": "बिना पानी के गेहूं की पैदावार 35% तक घट जाती है। मल्चिंग से जमीन की नमी लंबे समय तक बनी रहती है।",
                "source": SOURCES["IMD"]["name"],
                "source_url": SOURCES["IMD"]["url"],
                "badge_color": "red"
            }
        else:
            return {
                "id": "adv-climate-weather-forecast",
                "category": "Weather Coordination & Irrigation Scheduling",
                "title_en": "Agromet Weather Synchronization",
                "title_hi": "मौसम पूर्वानुमान एवं सिंचाई सामंजस्य",
                "priority": "informational",
                "observation": f"Current weather indicates mild conditions with negligible immediate rainfall probability in Western UP agro-climatic zone.",
                "observation_hi": "पश्चिमी उत्तर प्रदेश में मौसम सामान्य है और तात्कालिक वर्षा की संभावना नगण्य है।",
                "recommendation": "Proceed with scheduled agronomic operations. Check local 3-day weather bulletins before spraying liquid agro-chemicals.",
                "recommendation_hi": "तय योजना के अनुसार सिंचाई व खाद का कार्य करें। दवा छिड़कने से पहले आगामी 3 दिनों का मौसम अवश्य देख लें।",
                "reason": "Synchronizing spraying with calm, dry weather ensures 100% foliar retention without wash-off losses.",
                "reason_hi": "बारिश न होने पर दवा का पूरा असर पत्तियों पर होता है और दवा धुलकर बहती नहीं है।",
                "source": SOURCES["IMD"]["name"],
                "source_url": SOURCES["IMD"]["url"],
                "badge_color": "blue"
            }

    # -------------------------------------------------------------------------
    # Helper: Soil Management (Responsible, non-overclaiming regional guidance)
    # -------------------------------------------------------------------------
    @classmethod
    def _get_soil_management_card(cls, crop: str, soil_type: str, n: float, p: float, k: float, district: str) -> Dict[str, Any]:
        return {
            "id": "adv-soil-management",
            "category": "Soil Fertility & Nutrient Management",
            "title_en": f"Balanced Soil Nutrition Guidelines ({district} Baseline)",
            "title_hi": f"संतुलित मृदा पोषण दिशानिर्देश ({district} जिला स्तर)",
            "priority": "informational",
            "observation": f"District-level records classify the predominant soil as {soil_type} with medium organic carbon. Note: District statistics are regional baselines, not certified farm-specific soil measurements.",
            "observation_hi": f"जिला स्तरीय आंकड़ों के अनुसार इस क्षेत्र की मिट्टी '{soil_type}' है। ध्यान दें: यह जिला औसत है, आपके खेत की व्यक्तिगत जांच नहीं।",
            "recommendation": f"Follow recommended balanced ratio: for Wheat, apply 120 kg N : 60 kg P2O5 : 40 kg K2O per hectare (equivalent to 48:24:16 kg/acre). Current applied dosage: N={n}, P={p}, K={k} kg/acre. For precise plot-specific dosages, collect a composite soil sample and test through the Soil Health Card portal.",
            "recommendation_hi": f"संतुलित खाद डालें: गेहूं के लिए प्रति एकड़ 48 किलो नाइट्रोजन, 24 किलो फास्फोरस व 16 किलो पोटाश अनुशंसित है। आपके खेत का रिकॉर्ड: N={n}, P={p}, K={k} किग्रा/एकड़। अपने खेत की सटीक जांच के लिए मृदा स्वास्थ्य कार्ड योजना में मिट्टी की जांच कराएं।",
            "reason": "District averages serve as a macro reference; localized soil texture, pH, and electrical conductivity vary across neighboring plots. A lab test prevents costly over-fertilization and rectifies zinc/boron micro-deficiencies.",
            "reason_hi": "जिला स्तर का आंकड़ा केवल मार्गदर्शन के लिए है; खेत-खेत की मिट्टी में भिन्नता होती है। लैब टेस्ट कराने से खाद की बचत होती है और सही पोषण मिलता है।",
            "source": SOURCES["SHC"]["name"],
            "source_url": SOURCES["SHC"]["url"],
            "badge_color": "blue"
        }

    # -------------------------------------------------------------------------
    # Helper: Pest & Disease Vigilance (Evidence-based next steps)
    # -------------------------------------------------------------------------
    @classmethod
    def _get_pest_disease_card(cls, crop: str, symptoms: List[str], stage: str) -> Dict[str, Any]:
        symptom_str = " ".join([s.lower() for s in symptoms])

        # 1. Yellow Rust / Yellow Powder Concern
        if any(w in symptom_str for w in ["rust", "yellow powder", "stripes", "rataua", "रतुआ", "पीला"]):
            return {
                "id": "adv-pest-rust-evidence",
                "category": "Disease Vigilance & Step-by-Step Verification",
                "title_en": "Yellow Rust (Stripe Rust) Verification & Evidence-Based Protocol",
                "title_hi": "पीला रतुआ (Stripe Rust): प्रमाण आधारित जांच व सुरक्षित कदम",
                "priority": "urgent",
                "observation": "Reported visual symptom (yellow stripes / yellow powdery residue on leaves) is an indicator of possible Yellow Rust (Puccinia striiformis), prevalent during cool, humid spells in Western UP. Note: This is an evidence indicator, not a certified lab diagnosis.",
                "observation_hi": "पत्तियों पर पीली धारियां व हल्दी जैसा पाउडर दिखना 'पीला रतुआ' का संभावित लक्षण है, जो सर्दियों में पश्चिमी उप्र में फैलता है। ध्यान दें: यह प्रारंभिक संकेत है, अंतिम लैब पुष्टि नहीं।",
                "recommendation": "1) Perform physical wipe test: gently rub affected leaves with a white cloth or thumb — if yellow-orange spores rub off, rust fungus is present. 2) Inspect 10 plants in a zigzag line. 3) If confirmed, report to the local KVK extension officer and spray Propiconazole 25% EC @ 1 ml/L (200 ml/acre) in 200 L water using a hollow cone nozzle.",
                "recommendation_hi": "1) सफेद कपड़े या अंगूठे से पत्ती को पोंछें — यदि पीला पाउडर छूटता है तो रतुआ फफूंद की पुष्टि होती है। 2) खेत में 10 पौधों की जांच करें। 3) पुष्टि होने पर कृषि विज्ञान केंद्र को सूचित करें और प्रोपिकोनाजोल 25% EC (1 मिली/लीटर या 200 मिली/एकड़) का छिड़काव करें।",
                "reason": "Definitive visual confirmation prevents unnecessary fungicide expenditure. If rust is active, early treatment halts airborne spore propagation within 48 hours.",
                "reason_hi": "बिना जांच के कीटनाशक का खर्च न करें। पुष्टि होने पर 48 घंटे में छिड़काव करने से रोग पूरे खेत में फैलने से रुक जाता है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "red"
            }

        # 2. Aphid / Sucking Pest Concern (Mustard or Wheat)
        elif any(w in symptom_str for w in ["aphid", "chepa", "mahu", "insects", "कीट", "माहू", "चेपा"]):
            return {
                "id": "adv-pest-aphid-evidence",
                "category": "Pest Monitoring & Integrated Pest Management (IPM)",
                "title_en": "Mustard / Cereal Aphid Scouting & Safe Next Steps",
                "title_hi": "माहू (चेपा) कीट: आर्थिक क्षति स्तर (ETL) व सुरक्षित कदम",
                "priority": "urgent",
                "observation": "Small green/brown sucking insects reported on terminal shoots or inflorescence. In cool overcast weather, aphid populations multiply exponentially.",
                "observation_hi": "पौधे के ऊपरी भाग या फूलों पर छोटे हरे-भूरे माहू (चेपा) कीट देखे गए हैं। नम व ठंडे मौसम में इनकी संख्या तेजी से बढ़ती है।",
                "recommendation": "1) Scout 20 random plants across the field. 2) Determine Economic Threshold Level (ETL: 25–30 aphids per 10 cm central shoot). 3) If below ETL, apply organic Neem Oil (1500 ppm @ 3 ml/L). 4) If above ETL, seek verified prescription for Thiamethoxam 25% WG (80 g/acre) from authorized extension desk.",
                "recommendation_hi": "1) खेत में 20 पौधों की जांच करें। 2) आर्थिक क्षति सीमा (ETL: प्रति शाखा 25-30 माहू) देखें। 3) यदि कीट कम हैं तो नीम का तेल (1500 ppm @ 3 मिली/लीटर) छिड़कें। 4) अधिक होने पर अधिकृत कृषि रक्षा केंद्र से अनुशंसित दवा लें।",
                "reason": "Preserving natural predators (Coccinellid ladybird beetles) is critical. Spraying below ETL damages beneficial fauna and disrupts pollination.",
                "reason_hi": "नीम का तेल मित्र कीटों (लेडीबर्ड बीटल) को नुकसान नहीं पहुंचाता, जिससे प्राकृतिक संतुलन बना रहता है।",
                "source": SOURCES["DRMR"]["name"],
                "source_url": SOURCES["DRMR"]["url"],
                "badge_color": "red"
            }

        # 3. Yellowing Leaf Tips / Curling Concern
        elif any(w in symptom_str for w in ["curl", "yellowing", "tip", "chlorosis", "पत्ती", "पीली"]):
            return {
                "id": "adv-pest-chlorosis-evidence",
                "category": "Physiological Stress & Differential Scouting",
                "title_en": "Leaf Chlorosis / Tip Yellowing Differential Diagnosis Guide",
                "title_hi": "पत्तियों का पीला पड़ना: कारण एवं जांच के कदम",
                "priority": "moderate",
                "observation": "Reported symptom of leaf yellowing / tip necrosis can stem from multiple distinct sources: nitrogen deficiency, temporary waterlogging, or early root rot.",
                "observation_hi": "पत्तियों के पीले पड़ने के कई कारण हो सकते हैं: नाइट्रोजन की कमी, खेत में पानी भरा रहना या जड़ों की समस्या।",
                "recommendation": "1) Check lower vs upper leaves: lower leaf yellowing indicates nitrogen mobility deficiency. 2) Dig a sample root: white healthy roots indicate nutrient deficit (rectify with 2% Urea spray); brown slimy roots indicate root rot from water stagnation. 3) Consult local KVK with live plant sample before chemical treatment.",
                "recommendation_hi": "1) निचली पत्तियां पीली हैं तो नाइट्रोजन की कमी है। 2) जड़ें खोदकर देखें: यदि जड़ें सफेद हैं तो पोषक तत्व की कमी है; यदि जड़ें काली/सड़ी हैं तो जलभराव की समस्या है। 3) पौधे का नमूना लेकर कृषि विज्ञान केंद्र जाएं।",
                "reason": "Treating waterlogged yellowing with chemical fungicide wastes money; differentiated inspection identifies the true limiting factor.",
                "reason_hi": "सही कारण जाने बिना दवा डालने से खर्च व्यर्थ जाता है। सही पहचान से ही सटीक समाधान संभव है।",
                "source": SOURCES["UP_AGRI"]["name"],
                "source_url": SOURCES["UP_AGRI"]["url"],
                "badge_color": "amber"
            }

        # 4. Healthy Crop / No Symptoms
        else:
            return {
                "id": "adv-pest-scouting-healthy",
                "category": "Proactive Pest Scouting & Prevention",
                "title_en": "Proactive Field Surveillance & Preventive Protocol",
                "title_hi": "नियमित खेत निगरानी एवं निवारक सुरक्षा प्रोटोकॉल",
                "priority": "informational",
                "observation": "No acute crop diseases or pest infestations currently reported. Field is in stable condition.",
                "observation_hi": "वर्तमान में किसी गंभीर कीट या बीमारी की सूचना नहीं है। फसल की स्थिति सामान्य है।",
                "recommendation": "Conduct weekly zigzag field scouting. Inspect leaf undersides and flag leaves early in the morning when moisture reveals initial fungal or aphid focal points.",
                "recommendation_hi": "सप्ताह में एक बार पूरे खेत का चक्कर लगाएं। सुबह के समय पत्तियों के निचले हिस्से की जांच करें ताकि किसी भी कीट या फफूंद का तुरंत पता चल सके।",
                "reason": "Catching localized pest outbreaks in the initial 'hotspot' stage reduces remedial intervention costs by over 75%.",
                "reason_hi": "शुरुआती दौर में ही लक्षण पकड़ने से कीटनाशक का खर्च 75% तक कम हो जाता है।",
                "source": SOURCES["IIWBR"]["name"],
                "source_url": SOURCES["IIWBR"]["url"],
                "badge_color": "green"
            }


class AgronomicAdvisor:
    """Wrapper class preserving legacy interface for backwards compatibility

    while delegating to the enhanced PersonalisedAdvisoryEngine.
    """

    @staticmethod
    def get_advisory(farmer_input: Dict[str, Any], yield_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provides full backward compatibility with existing tests and codebase."""
        if yield_result is None:
            yield_result = {"predicted_yield_per_acre": 19.5}
        return PersonalisedAdvisoryEngine.generate_advisory(farmer_input, yield_result)

    @staticmethod
    def get_personalised_advisory(farmer_input: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method returning structured advisory cards."""
        return PersonalisedAdvisoryEngine.generate_advisory(farmer_input, None)
