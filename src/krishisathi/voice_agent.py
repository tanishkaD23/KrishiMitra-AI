"""KrishiSathi conversational agent providing voice-first, grounded agricultural advisory

in both Hindi and English.
"""

import os
from typing import Dict, Any, Optional


class KrishiSathiAgent:
    """Conversational assistant grounded in farmer plot parameters,

    yield forecast, agronomic advisories, and eligible government schemes.
    Supports both Hindi and English dialogue.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._gemini_model = None

        if self.api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self._gemini_model = None

    def ask(self, query: str, context: Dict[str, Any], lang: str = "hi") -> str:
        """Answers farmer query using Gemini (if available) or agricultural knowledge base."""
        query_clean = query.strip().lower()

        # Check if query itself is primarily English
        is_english = (
            lang == "en"
            or any(word in query_clean for word in ["when", "how", "what", "which", "yield", "water", "fertilizer", "scheme"])
        )

        if self._gemini_model:
            try:
                lang_instruction = (
                    "Respond in clear, conversational English suited for farmers (2-3 sentences max)."
                    if is_english
                    else "हमेशा सरल, आदरणीय और बोलचाल की हिंदी में उत्तर दें (अधिकतम 2-3 वाक्य)।"
                )

                system_prompt = f"""
You are 'KrishiSathi' (कृषिसाथी), a friendly, expert agricultural advisor for Indian smallholder farmers.
Farmer Profile:
- Crop: {context.get('crop', 'Wheat')}
- Plot Size: {context.get('plot_acres', 1)} Acres
- District: {context.get('district', 'Meerut')}, Western Uttar Pradesh
- Forecasted Yield: {context.get('predicted_yield', '18.5')} Quintals/Acre
- Alerts: {', '.join(context.get('alerts_hi', ['No critical alerts']))}
- Eligible Schemes: {', '.join([s.get('name_hi', s.get('name_en', '')) for s in context.get('eligible_schemes', [])])}

Rules:
1. {lang_instruction}
2. Ground all answers strictly on the farmer's plot and regional data.
"""
                response = self._gemini_model.generate_content(
                    f"{system_prompt}\n\nFarmer Query: {query}\nKrishiSathi Response:"
                )
                if response and response.text:
                    return response.text.strip()
            except Exception:
                pass

        # Fallback local matcher
        if is_english:
            return self._local_grounded_response_en(query_clean, context)
        return self._local_grounded_response_hi(query_clean, context)

    def _local_grounded_response_hi(self, query: str, context: Dict[str, Any]) -> str:
        crop = context.get("crop", "Wheat")
        crop_hi = "गेहूं" if crop == "Wheat" else "सरसों"
        predicted_yield = context.get("predicted_yield", 18.5)
        plot_acres = context.get("plot_acres", 1.0)
        alerts_hi = context.get("alerts_hi", [])
        advisories_hi = context.get("advisories_hi", [])
        schemes = context.get("eligible_schemes", [])

        if any(w in query for w in ["पैदावार", "yield", "उपज", "उत्पादन", "paidaawar"]):
            return (
                f"किसान भाई, आपके {plot_acres} एकड़ खेत में {crop_hi} की अनुमानित पैदावार लगभग {predicted_yield} क्विंटल प्रति एकड़ "
                f"(कुल लगभग {round(float(predicted_yield) * float(plot_acres), 1)} क्विंटल) रहने की संभावना है।"
            )

        if any(w in query for w in ["पानी", "सिंचाई", "irrigation", "sinchai"]):
            if crop == "Wheat":
                return (
                    "गेहूं में पहली सिंचाई बुवाई के 20-25 दिन बाद 'ताज जड़' (CRI अवस्था) पर बहुत जरूरी है। "
                    "इसके बाद कल्ले फूटते समय और दाना भरते समय हल्की सिंचाई जरूर करें।"
                )
            return (
                "सरसों में सिर्फ 2 हल्की सिंचाई काफी होती हैं: पहली फूल आने से ठीक पहले (30-35 दिन) "
                "और दूसरी फलियां बनते समय (60-65 दिन)।"
            )

        if any(w in query for w in ["खाद", "यूरिया", "fertilizer", "dap", "khad", "npk"]):
            if crop == "Wheat":
                return (
                    "गेहूं के लिए संतुलित मात्रा में 50 किलो नाइट्रोजन, 25 किलो फॉस्फोरस और 15 किलो पोटाश प्रति एकड़ दें। "
                    "यूरिया को किस्तों में पहली और दूसरी सिंचाई के साथ दें।"
                )
            return (
                "सरसों में तेल और दाने की चमक बढ़ाने के लिए बुवाई के समय 10 किलो बेंटोनाइट सल्फर या 25 किलो जिप्सम प्रति एकड़ जरूर डालें।"
            )

        if any(w in query for w in ["कीट", "कीड़ा", "रोग", "pest", "disease", "माहू", "रतुआ"]):
            if crop == "Wheat":
                return (
                    "पश्चिमी उत्तर प्रदेश में पत्तियों पर पीले रतुआ की निगरानी रखें। "
                    "लक्षण दिखते ही प्रोपिकोनाजोल 25% EC (200 मिली प्रति एकड़) का छिड़काव करें।"
                )
            return (
                "सरसों में जनवरी में माहू (चेपा) कीट का प्रकोप बढ़ता है। "
                "शुरुआत में नीम का तेल (5 मिली/लीटर) छिड़कें। अधिक प्रकोप पर इमिडाक्लोप्रिड का छिड़काव करें।"
            )

        if any(w in query for w in ["योजना", "स्कीम", "scheme", "सब्सिडी", "बीमा", "pm-kisan", "pmfby"]):
            return (
                f"किसान भाई, आपके {plot_acres} एकड़ खेत के लिए आप PM-KISAN (₹6,000/वर्ष) और PMFBY फसल बीमा (मात्र 1.5% प्रीमियम) के पूर्ण पात्र हैं।"
            )

        summary = alerts_hi[0] if alerts_hi else advisories_hi[0] if advisories_hi else "समय पर खाद और पानी दें।"
        return f"किसान भाई, आपकी फसल के लिए मुख्य सलाह: {summary}"

    def _local_grounded_response_en(self, query: str, context: Dict[str, Any]) -> str:
        crop = context.get("crop", "Wheat")
        predicted_yield = context.get("predicted_yield", 18.5)
        plot_acres = context.get("plot_acres", 1.0)

        if any(w in query for w in ["yield", "production", "harvest", "quintal"]):
            total = round(float(predicted_yield) * float(plot_acres), 1)
            return (
                f"Farmer friend, your estimated {crop} yield is approximately {predicted_yield} Quintals/Acre "
                f"(total harvest around {total} Quintals for your {plot_acres} acre plot)."
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
                    "Apply a balanced N-P-K dose of 50 kg N, 25 kg P, and 15 kg K per acre. Split urea doses across basal and the first two irrigations."
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

        if any(w in query for w in ["scheme", "subsidy", "insurance", "pm-kisan", "pmfby"]):
            return (
                f"Based on your {plot_acres} acre landholding, you qualify for PM-KISAN (₹6,000/yr direct income support) and PMFBY crop insurance at only 1.5% Rabi premium."
            )

        return (
            f"For your {crop} crop in Western UP, ensure timely irrigation and balanced nitrogen fertilizer to protect yields against terminal heat."
        )
