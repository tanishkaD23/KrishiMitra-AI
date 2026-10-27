"""KrishiSathi conversational agent providing voice-first, grounded agricultural advisory
in Hindi, Hinglish, and English.
Integrated with Scheme PDF RAG pipeline and Fallback Official Web Search.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from root .env
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

from src.rag.pipeline import SchemeRAGPipeline

logger = logging.getLogger(__name__)


class KrishiSathiAgent:
    """Conversational assistant grounded in farmer plot parameters,
    yield forecast, agronomic advisories, live weather, and government schemes.
    Features:
    1. Scheme PDF RAG (KCC, PM-KISAN, PMFBY, PMKSY, Soil Health Card).
    2. Fallback Official Web-Search for unindexed schemes or current updates.
    3. Multilingual dialogue: Hindi, Hinglish, English.
    4. Guardrails: Refuses to fabricate scheme eligibility or benefits if unverified.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        rag_pipeline: Optional[SchemeRAGPipeline] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._openai_client = None
        self.rag_pipeline = rag_pipeline or SchemeRAGPipeline()
        self.last_rag_result: Optional[Dict[str, Any]] = None

        if self.api_key and self.api_key.strip():
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key.strip(), timeout=8.0)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {type(e).__name__}")
                self._openai_client = None

    def ask(self, query: str, context: Optional[Dict[str, Any]] = None, lang: str = "hi") -> str:
        """Answers farmer query and returns the answer string (for full backward compatibility)."""
        result = self.ask_rag(query, context, lang)
        return result["answer"]

    def ask_rag(self, query: str, context: Optional[Dict[str, Any]] = None, lang: str = "hi") -> Dict[str, Any]:
        """Comprehensive RAG pipeline:
        1. Classifies query and determines language (Hindi, Hinglish, English).
        2. Retrieves from local Scheme PDFs.
        3. If insufficient, falls back to Official Government Web Search.
        4. If unverified, informs the farmer safely without hallucinating.
        5. Generates grounded answer with source citations.
        """
        if context is None:
            context = {}

        query_clean = query.strip()
        lang_mode = self._detect_language(query_clean, lang)

        # Check if query is asking about government schemes, loans, subsidies, insurance, etc.
        is_scheme_query = self._is_scheme_or_policy_query(query_clean)

        # -------------------------------------------------------------
        # Stage 1 & 2: RAG Retrieval (PDF First -> Web Search Fallback)
        # -------------------------------------------------------------
        if is_scheme_query:
            retrieval = self.rag_pipeline.retrieve(query_clean, context)
        else:
            retrieval = {
                "retrieval_mode": "agronomic",
                "verified": True,
                "context_text": "",
                "sources": [],
                "has_official_source": False,
                "access_date": datetime.now().strftime("%Y-%m-%d"),
                "message": "Direct agronomic and plot advisory."
            }
        self.last_rag_result = retrieval

        # -------------------------------------------------------------
        # Stage 3: Guardrail Check (No reliable evidence found)
        # -------------------------------------------------------------
        if is_scheme_query and not retrieval.get("verified"):
            unverified_answer = self._generate_unverified_response(query_clean, lang_mode)
            return {
                "answer": unverified_answer,
                "sources": [],
                "retrieval_mode": "unverified",
                "verified": False,
                "lang": lang_mode
            }

        # -------------------------------------------------------------
        # Stage 4: Answer Generation (OpenAI LLM or Expert Grounded Rules)
        # -------------------------------------------------------------
        # Try OpenAI LLM if configured
        if self._openai_client:
            llm_answer = self._call_openai_llm(query_clean, context, lang_mode, retrieval)
            if llm_answer:
                return {
                    "answer": llm_answer,
                    "sources": retrieval.get("sources", []),
                    "retrieval_mode": retrieval.get("retrieval_mode", "general"),
                    "verified": retrieval.get("verified", True),
                    "lang": lang_mode
                }

        # Fallback to local rule-based response engine
        fallback_answer = self._local_grounded_response(query_clean, context, lang_mode, retrieval)
        return {
            "answer": fallback_answer,
            "sources": retrieval.get("sources", []),
            "retrieval_mode": retrieval.get("retrieval_mode", "fallback_rules"),
            "verified": retrieval.get("verified", True),
            "lang": lang_mode
        }

    def _call_openai_llm(
        self,
        query: str,
        context: Dict[str, Any],
        lang_mode: str,
        retrieval: Dict[str, Any]
    ) -> Optional[str]:
        """Calls OpenAI Chat Completion API with injected RAG context and strict guardrails."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        farmer_name = context.get("farmer_name", "Tanishka")
        district = context.get("district", "Meerut")
        plot_acres = context.get("plot_acres", 2.5)
        growth_stage = context.get("growth_stage", "Tillering")
        pred_yield = context.get("predicted_yield", "19.9")
        range_q_ha = context.get("expected_range_q_ha", "44 - 54")
        irrigation = context.get("irrigation_source", "Tube well / Borewell")
        weather = context.get("weather") or {}

        weather_desc = "Normal seasonal weather"
        if isinstance(weather, dict) and weather.get("available"):
            temp = weather.get("temperature_c", 25)
            hum = weather.get("humidity_pct", 60)
            cond = weather.get("condition", "Clear")
            rain = weather.get("precipitation_mm", 0.0)
            weather_desc = f"{cond}, Temperature {temp}°C, Humidity {hum}%, Rain {rain} mm"

        rag_text = retrieval.get("context_text", "").strip()
        sources = retrieval.get("sources", [])
        sources_str = ", ".join([f"{s['title']} ({s['url']})" for s in sources[:3]]) if sources else "Direct ICAR Agronomic Protocols"

        # Language instructions
        if lang_mode == "en":
            lang_instruction = "Respond in clear, conversational English suited for farmers (2-3 sentences max). Cite official portal/sources clearly."
        elif lang_mode == "hinglish":
            lang_instruction = "Respond in natural Hinglish (conversational Hindi written in Roman script) so a farmer can easily read it on mobile (2-3 sentences max). Cite official portals clearly."
        else:
            lang_instruction = "हमेशा सरल, आदरणीय और बोलचाल की हिंदी (Devanagari) में उत्तर दें (अधिकतम 2-3 वाक्य)। आधिकारिक पोर्टल का नाम जरूर बताएं।"

        system_prompt = f"""You are 'KrishiSathi' (कृषिसाथी), a trusted, expert agricultural & scheme advisory AI for Indian farmers.

Farmer & Plot Context:
- Farmer Name: {farmer_name}
- District: {district}, Western Uttar Pradesh
- Crop: {crop} (Rabi Season)
- Landholding: {plot_acres} Acres
- Stage: {growth_stage}
- Forecasted Yield: {pred_yield} Q/Acre ({range_q_ha} Q/Ha)
- Irrigation Source: {irrigation}
- Current Weather: {weather_desc}

Verified Grounding Context (From Scheme Guidelines / Official Portals):
\"\"\"
{rag_text if rag_text else "No specialized scheme documents matched. Use standard ICAR crop protocols and verified government rules."}
\"\"\"
Sources Consulted: {sources_str}

Strict Rules:
1. {lang_instruction}
2. Ground your answer ONLY in verified facts from the context above or official ICAR agronomic rules.
3. If the user asks about a government scheme and reliable evidence was not provided in the context, do NOT invent eligibility, benefits, or deadlines. State clearly that the information could not be verified.
4. Mention the official source or portal (e.g. pmkisan.gov.in, pmfby.gov.in, mnre.gov.in).
"""

        candidate_models = [self.model]
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
                    temperature=0.3,
                    timeout=8.0
                )
                if response and response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    if content and content.strip():
                        return content.strip()
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"OpenAI call with model '{model_name}' encountered: {type(e).__name__} - {err_msg[:100]}")
                err_lower = err_msg.lower()
                if any(k in err_lower for k in ["insufficient_quota", "credit", "quota", "429", "rate limit", "connection", "apiconnection"]):
                    break

        return None

    def _local_grounded_response(
        self,
        query: str,
        context: Dict[str, Any],
        lang_mode: str,
        retrieval: Dict[str, Any]
    ) -> str:
        """Local rule-based generator when OpenAI is offline or quota-limited."""
        query_lower = query.lower()

        # If RAG returned verified web search or PDF snippets, synthesize directly
        if retrieval.get("verified") and retrieval.get("context_text"):
            sources = retrieval.get("sources", [])
            source_tag = sources[0]["title"] if sources else "आधिकारिक पोर्टल"

            # Check if PM-KUSUM was retrieved
            if "kusum" in query_lower or "solar" in query_lower:
                if lang_mode == "en":
                    return f"According to official MNRE guidelines ({source_tag}), PM-KUSUM provides up to 60% capital subsidy for solar agricultural pumps and tube-well solarization. Apply via upagriculture.com or mnre.gov.in."
                elif lang_mode == "hinglish":
                    return f"Official MNRE guidelines ({source_tag}) ke mutabik, PM-KUSUM scheme me solar pump lagwane par 60% tak subsidy milti hai. Registration upagriculture.com ya mnre.gov.in par hota hai."
                else:
                    return f"नवीन एवं नवीकरणीय ऊर्जा मंत्रालय (MNRE) की आधिकारिक गाइडलाइंस के अनुसार, PM-KUSUM योजना में सोलर पंप लगाने पर 60% तक का अनुदान (सब्सिडी) मिलता है। आवेदन हेतु upagriculture.com या mnre.gov.in पर जाएं।"

            # Check if PM-KISAN eKYC was retrieved
            if "ekyc" in query_lower or "ईकेवाईसी" in query_lower:
                if lang_mode == "en":
                    return f"According to official PM-KISAN guidelines ({source_tag}), eKYC is mandatory for all beneficiaries. You can complete OTP-based eKYC on pmkisan.gov.in or biometric eKYC at your nearest CSC center."
                elif lang_mode == "hinglish":
                    return f"Official PM-KISAN portal ({source_tag}) ke anusar sabhi labharthiyon ke liye eKYC anivarya hai. Aap pmkisan.gov.in par OTP se ya CSC center par biometric se eKYC poori kar sakte hain."
                else:
                    return f"पीएम-किसान आधिकारिक दिशानिर्देशों ({source_tag}) के अनुसार सभी लाभार्थियों के लिए eKYC अनिवार्य है। आप pmkisan.gov.in पर OTP द्वारा अथवा नजदीकी CSC केंद्र पर बायोमेट्रिक से eKYC पूरा कर सकते हैं।"

        # Fallback to standard crop & farming responses
        if lang_mode == "en":
            return self._local_grounded_response_en(query_lower, context)
        return self._local_grounded_response_hi(query_lower, context)

    def _generate_unverified_response(self, query: str, lang_mode: str) -> str:
        """Requirement 6: Tells the farmer that reliable information could not be verified."""
        if lang_mode == "en":
            return (
                "I'm sorry, reliable official information on this query could not be verified from government records or portals. "
                "To prevent misinformation, please consult your local agriculture officer or check directly on the official portal (pmkisan.gov.in / myscheme.gov.in)."
            )
        elif lang_mode == "hinglish":
            return (
                "Kisan bhai, is query ki official jaankari government records ya portals par verify nahi ho saki. "
                "Galat niyam ya fraud se bachne ke liye please official portal (pmkisan.gov.in ya myscheme.gov.in) par check karein ya nazdeeki Krishi Vigyan Kendra se sampark karein."
            )
        else:
            return (
                "क्षमा करें किसान भाई, इस प्रश्न से जुड़ी आधिकारिक व विश्वसनीय जानकारी सरकारी दस्तावेजों या पोर्टल्स पर सत्यापित नहीं हो सकी। "
                "गलत नियमों या भ्रामक दावों से बचने के लिए कृपया आधिकारिक पोर्टल (जैसे pmkisan.gov.in या myscheme.gov.in) पर जांच करें अथवा नजदीकी कृषि विज्ञान केंद्र से संपर्क करें।"
            )

    def _detect_language(self, query: str, default_lang: str = "hi") -> str:
        """Detects whether query is in Hindi (Devanagari), Hinglish (Romanized Hindi), or English."""
        # 1. Check for Devanagari Unicode block
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", query))
        if has_devanagari:
            return "hi"

        query_lower = query.lower()
        # 2. Check common Hinglish markers
        hinglish_words = [
            "kaise", "kya", "kab", "karo", "karein", "hoga", "hogi", "paani", "khad",
            "kisan", "bhai", "fasal", "kitna", "kitni", "milega", "milegi", "kaha",
            "yojana", "sinchai", "paidaawar", "upaj", "khetee", "khet"
        ]
        if any(re.search(rf"\b{hw}\b", query_lower) for hw in hinglish_words):
            return "hinglish"

        # 3. Default based on requested language
        if default_lang == "en":
            return "en"
        return "en" if any(w in query_lower for w in ["when", "how", "what", "which", "where", "yield", "subsidy", "deadline"]) else "hi"

    def _is_scheme_or_policy_query(self, query: str) -> bool:
        """Identifies if the farmer query involves government schemes, loans, subsidies, or rules."""
        query_lower = query.lower()
        terms = [
            "scheme", "subsidy", "yojana", "kisan", "pm-kisan", "pmkisan", "pmfby", "kcc", "kusum", "pmksy",
            "bima", "insurance", "loan", "rin", "ऋण", "योजना", "सब्सिडी", "अनुदान", "किस्त", "installment",
            "ekyc", "ईकेवाईसी", "प्रीमियम", "premium", "deadline", "date", "पात्रता", "eligibility",
            "shc", "soil health card", "solar pump", "सोलर पंप", "claim", "क्लेम", "compensation"
        ]
        return any(t in query_lower for t in terms)

    def _local_grounded_response_hi(self, query: str, context: Dict[str, Any]) -> str:
        """Standard agronomic rules in Hindi."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        crop_hi = "गेहूं" if crop == "Wheat" else "सरसों"
        predicted_yield = context.get("predicted_yield", 19.9)
        plot_acres = context.get("plot_acres", 2.5)
        district = context.get("district", "Meerut")
        growth_stage = context.get("growth_stage", "Tillering")

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
                "और दूसरी फलियां बनते समय (60-65 दिन)।"
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

        if any(w in query for w in ["मौसम", "weather", "तापमान", "बारिश", "rain", "temperature"]):
            weather = context.get("weather") or {}
            if isinstance(weather, dict) and weather.get("available"):
                temp = weather.get("temperature_c", 25)
                cond = weather.get("condition", "साफ")
                return f"{district} में वर्तमान मौसम {cond} है और तापमान {temp}°C है। आवश्यकता अनुसार ही सिंचाई का निर्णय लें।"
            return f"{district} क्षेत्र में मौसम अनुकूल है। पछुआ हवा और तेज धूप के समय मिट्टी में पर्याप्त नमी बनाए रखें।"

        return f"तनिष्का जी, वर्तमान में {growth_stage} अवस्था चल रही है। समय पर संतुलित पोषण और सिंचाई से फसल सुरक्षित रहेगी।"

    def _local_grounded_response_en(self, query: str, context: Dict[str, Any]) -> str:
        """Standard agronomic rules in English."""
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

        if any(w in query for w in ["weather", "temperature", "rain", "forecast"]):
            return f"Weather conditions in {district} are favorable. Maintain optimum soil moisture during peak vegetative stages."

        return (
            f"For your {crop} crop in {district}, Western UP, ensure timely irrigation and balanced nitrogen fertilizer to protect yields against terminal heat."
        )
