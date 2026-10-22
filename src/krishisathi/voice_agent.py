"""KrishiSathi conversational agent providing voice-first, grounded agricultural advisory
in both Hindi and English powered by OpenAI LLM with offline expert rule fallback.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger(__name__)


class KrishiSathiAgent:
    """Conversational assistant grounded in farmer plot parameters,
    yield forecast, agronomic advisories, live weather, and eligible government schemes.
    Powered by OpenAI LLM (with robust fallback to ICAR rule-based agronomic engine).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._openai_client = None

        if self.api_key and self.api_key.strip():
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key.strip())
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {type(e).__name__}")
                self._openai_client = None

    def ask(self, query: str, context: Optional[Dict[str, Any]] = None, lang: str = "hi") -> str:
        """Answers farmer query using OpenAI LLM (if configured and funded) or agricultural knowledge base."""
        if context is None:
            context = {}

        query_clean = query.strip()
        query_lower = query_clean.lower()

        # Check if query itself is primarily English
        is_english = (
            lang == "en"
            or any(word in query_lower for word in ["when", "how", "what", "which", "yield", "water", "fertilizer", "scheme", "weather", "pest", "soil"])
        )

        # 1. Try OpenAI LLM if client is initialized
        if self._openai_client:
            llm_answer = self._call_openai_llm(query_clean, context, is_english)
            if llm_answer:
                return llm_answer

        # 2. Fallback to expert local grounded rules engine
        if is_english:
            return self._local_grounded_response_en(query_lower, context)
        return self._local_grounded_response_hi(query_lower, context)

    def _call_openai_llm(self, query: str, context: Dict[str, Any], is_english: bool) -> Optional[str]:
        """Calls OpenAI Chat Completion API with comprehensive grounding context."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        farmer_name = context.get("farmer_name", "Tanishka")
        district = context.get("district", "Meerut")
        plot_acres = context.get("plot_acres", 2.5)
        growth_stage = context.get("growth_stage", "Tillering")
        pred_yield = context.get("predicted_yield", "19.9")
        range_q_ha = context.get("expected_range_q_ha", "44 - 54")
        irrigation = context.get("irrigation_source", "Tube well / Borewell")
        symptoms = context.get("reported_symptoms", [])
        weather = context.get("weather") or {}

        weather_desc = "Normal seasonal weather"
        if isinstance(weather, dict) and weather.get("available"):
            temp = weather.get("temperature_c", 25)
            hum = weather.get("humidity_pct", 60)
            cond = weather.get("condition", "Clear")
            rain = weather.get("precipitation_mm", 0.0)
            weather_desc = f"{cond}, Temperature {temp}°C, Humidity {hum}%, Rain {rain} mm"

        schemes_list = [s.get("name_hi" if not is_english else "name_en", "") for s in context.get("eligible_schemes", []) if isinstance(s, dict)]
        schemes_str = ", ".join([s for s in schemes_list if s]) or "PM-KISAN, PMFBY Crop Insurance"

        if is_english:
            lang_instruction = "Respond in clear, conversational English suited for farmers (2-3 sentences max). Be respectful, warm, and actionable."
        else:
            lang_instruction = "हमेशा सरल, आदरणीय और बोलचाल की हिंदी (Devanagari) में उत्तर दें (अधिकतम 2-3 वाक्य)। 'किसान भाई' या 'तनिष्का जी' कहकर सम्मानपूर्वक संबोधित करें।"

        system_prompt = f"""You are 'KrishiSathi' (कृषिसाथी), a friendly, trusted AI agricultural advisor for Indian farmers developed by KrishiMitra AI.

Current Farmer & Field Context:
- Farmer Name: {farmer_name}
- District: {district}, Western Uttar Pradesh
- Crop: {crop} (Rabi Season)
- Plot Size: {plot_acres} Acres
- Current Growth Stage: {growth_stage}
- Forecasted Yield: {pred_yield} Q/Acre ({range_q_ha} Q/Ha)
- Irrigation Source: {irrigation}
- Current Live Weather: {weather_desc}
- Reported Field Symptoms: {', '.join(symptoms) if symptoms else 'None (Crop is healthy)'}
- Eligible Schemes: {schemes_str}

Guidelines:
1. {lang_instruction}
2. Ground all advice strictly in ICAR (Indian Council of Agricultural Research) & IMD protocols.
3. Keep the answer direct, practical, and easy to understand when spoken aloud.
4. Do not invent unverified chemical dosages; suggest safe agronomic practices.
"""

        candidate_models = [self.model]
        # If user model fails or is non-standard, fallback to reliable standard models
        for fallback_model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            if fallback_model not in candidate_models:
                candidate_models.append(fallback_model)

        for model_name in candidate_models:
            try:
                response = self._openai_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=220,
                    temperature=0.3
                )
                if response and response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    if content and content.strip():
                        return content.strip()
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"OpenAI call with model '{model_name}' encountered: {type(e).__name__} - {err_msg[:120]}")
                # If it's a quota error or rate limit error, trying other models won't help; break to fallback
                if "insufficient_quota" in err_msg or "credit_balance_exhausted" in err_msg:
                    break

        return None

    def _local_grounded_response_hi(self, query: str, context: Dict[str, Any]) -> str:
        """Rule-based expert response in Hindi grounded in verified agronomic science."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        crop_hi = "गेहूं" if crop == "Wheat" else "सरसों"
        predicted_yield = context.get("predicted_yield", 19.9)
        plot_acres = context.get("plot_acres", 2.5)
        district = context.get("district", "Meerut")
        growth_stage = context.get("growth_stage", "Tillering")
        alerts_hi = context.get("alerts_hi", [])
        advisories_hi = context.get("advisories_hi", [])

        if any(w in query for w in ["पैदावार", "yield", "उपज", "उत्पादन", "paidaawar", "harvest"]):
            total = round(float(predicted_yield) * float(plot_acres), 1)
            return (
                f"किसान भाई, आपके {plot_acres} एकड़ खेत में {crop_hi} की अनुमानित पैदावार लगभग {predicted_yield} क्विंटल प्रति एकड़ "
                f"(कुल लगभग {total} क्विंटल) रहने की संभावना है। संतुलित खाद और समय पर सिंचाई से पैदावार सुरक्षित रहेगी।"
            )

        if any(w in query for w in ["पानी", "सिंचाई", "irrigation", "sinchai", "water"]):
            if crop == "Wheat":
                return (
                    "गेहूं में पहली सिंचाई बुवाई के 20-25 दिन बाद 'ताज जड़' (CRI अवस्था) पर बहुत जरूरी है। "
                    "इसके बाद कल्ले फूटते समय (40-45 दिन) और दाना भरते समय हल्की सिंचाई जरूर करें।"
                )
            return (
                "सरसों में सिर्फ 2 हल्की सिंचाई काफी होती हैं: पहली फूल आने से ठीक पहले (30-35 दिन) "
                "और दूसरी फलियां बनते समय (60-65 दिन)। अधिक पानी से जड़ सड़न का खतरा होता है।"
            )

        if any(w in query for w in ["खाद", "यूरिया", "fertilizer", "dap", "khad", "npk", "urea"]):
            if crop == "Wheat":
                return (
                    f"{district} क्षेत्र में गेहूं के लिए प्रति एकड़ लगभग 48 किलो नाइट्रोजन, 24 किलो फास्फोरस व 16 किलो पोटाश अनुशंसित है। "
                    "यूरिया की आधी मात्रा बुवाई पर और बाकी दो बराबर किस्तों में सिंचाई के समय दें।"
                )
            return (
                "सरसों में तेल की मात्रा और दानों की चमक बढ़ाने के लिए बुवाई के समय 10 किलो बेंटोनाइट सल्फर या 25 किलो जिप्सम प्रति एकड़ जरूर डालें।"
            )

        if any(w in query for w in ["कीट", "कीड़ा", "रोग", "pest", "disease", "माहू", "रतुआ", "rust", "aphid"]):
            if crop == "Wheat":
                return (
                    "पश्चिमी उत्तर प्रदेश में कोहरे के दौरान पत्तियों पर पीले रतुआ (Yellow Rust) की नियमित निगरानी रखें। "
                    "लक्षण दिखते ही प्रोपिकोनाजोल 25% EC (200 मिली प्रति एकड़) का छिड़काव करें।"
                )
            return (
                "सरसों में जनवरी में माहू (चेपा) कीट का प्रकोप बढ़ता है। "
                "शुरुआत में नीम का तेल (5 मिली प्रति लीटर) छिड़कें। अधिक प्रकोप होने पर इमिडाक्लोप्रिड का छिड़काव करें।"
            )

        if any(w in query for w in ["योजना", "स्कीम", "scheme", "सब्सिडी", "बीमा", "pm-kisan", "pmfby", "kcc"]):
            return (
                f"किसान भाई, आपके {plot_acres} एकड़ खेत के लिए आप PM-KISAN (₹6,000/वर्ष) और PMFBY फसल बीमा (मात्र 1.5% रबी प्रीमियम) के पूर्ण पात्र हैं। "
                "नजदीकी सीएससी केंद्र या कृषि विभाग में पंजीकरण कराएं।"
            )

        if any(w in query for w in ["मौसम", "weather", "तापमान", "बारिश", "rain", "temperature"]):
            weather = context.get("weather") or {}
            if isinstance(weather, dict) and weather.get("available"):
                temp = weather.get("temperature_c", 25)
                cond = weather.get("condition", "साफ")
                return f"{district} में वर्तमान मौसम {cond} है और तापमान {temp}°C है। फसल में आवश्यकता अनुसार ही सिंचाई का निर्णय लें।"
            return f"{district} क्षेत्र में मौसम अनुकूल है। पछुआ हवा और तेज धूप के समय मिट्टी में पर्याप्त नमी बनाए रखें।"

        summary = alerts_hi[0] if alerts_hi else advisories_hi[0] if advisories_hi else f"वर्तमान में {growth_stage} अवस्था चल रही है, समय पर खाद व पानी दें।"
        return f"तनिष्का जी, आपकी {crop_hi} फसल के लिए मुख्य सलाह: {summary}"

    def _local_grounded_response_en(self, query: str, context: Dict[str, Any]) -> str:
        """Rule-based expert response in English grounded in verified agronomic science."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        predicted_yield = context.get("predicted_yield", 19.9)
        plot_acres = context.get("plot_acres", 2.5)
        district = context.get("district", "Meerut")

        if any(w in query for w in ["yield", "production", "harvest", "quintal"]):
            total = round(float(predicted_yield) * float(plot_acres), 1)
            return (
                f"Farmer friend, your estimated {crop} yield is approximately {predicted_yield} Quintals/Acre "
                f"(total harvest around {total} Quintals for your {plot_acres} acre plot in {district})."
            )

        if any(w in query for w in ["water", "irrigation", "irrigate"]):
            if crop == "Wheat":
                return (
                    "For wheat, the first irrigation at Crown Root Initiation (CRI stage, 20-25 days after sowing) is critical. "
                    "Follow with light watering at tillering and grain-filling stages."
                )
            return (
                "Mustard requires only 2 light irrigations: first before flowering (30-35 days) and second during siliqua pod filling (60-65 days)."
            )

        if any(w in query for w in ["fertilizer", "urea", "nutrient", "npk"]):
            if crop == "Wheat":
                return (
                    "Apply a balanced N-P-K dosage: 48 kg N, 24 kg P, and 16 kg K per acre. Split nitrogen across basal and the first two irrigations."
                )
            return (
                "For mustard, sulfur is essential for high oil content. Apply 10 kg Bentonite Sulfur or 25 kg Gypsum per acre at sowing."
            )

        if any(w in query for w in ["pest", "disease", "insect", "rust", "aphid"]):
            if crop == "Wheat":
                return (
                    "Scout for Yellow Rust during foggy weather. If symptoms appear, spray Propiconazole 25% EC @ 200 ml per acre."
                )
            return (
                "Watch out for mustard aphids in January. Spray 5% neem oil as prevention or Imidacloprid if infestation exceeds threshold."
            )

        if any(w in query for w in ["scheme", "subsidy", "insurance", "pm-kisan", "pmfby", "kcc"]):
            return (
                f"Based on your {plot_acres} acre landholding, you qualify for PM-KISAN (₹6,000/yr direct income support) and PMFBY crop insurance at only 1.5% Rabi premium."
            )

        if any(w in query for w in ["weather", "temperature", "rain", "forecast"]):
            return f"Weather conditions in {district} are favorable. Maintain optimum soil moisture during peak vegetative stages."

        return (
            f"For your {crop} crop in {district}, Western UP, ensure timely irrigation and balanced nitrogen fertilizer to protect yields against terminal heat."
        )
