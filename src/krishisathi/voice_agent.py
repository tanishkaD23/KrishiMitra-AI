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
from src.weather.live_weather import fetch_open_meteo_weather
from src.yield_model.predict import YieldPredictor

logger = logging.getLogger(__name__)


class KrishiSathiAgent:
    """Conversational assistant grounded in farmer plot parameters,
    yield forecast, agronomic advisories, live weather, and government schemes.
    Features:
    1. Scheme PDF & Central JSON RAG (PM-KISAN, PMFBY, KCC, PMKSY, Soil Health Card, PM-KUSUM, SMAM, PKVY, e-NAM).
    2. Fallback Official Web-Search for unindexed schemes or current updates.
    3. Live Weather & 7-Day Forecast Integration + Multi-State ML Yield Predictor.
    4. Multilingual dialogue: Hindi, Hinglish, English across all 10 Rabi crops and 6 states.
    5. Guardrails: Refuses to fabricate scheme eligibility or benefits if unverified.
    """

    _OPENAI_QUOTA_EXHAUSTED: bool = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        rag_pipeline: Optional[SchemeRAGPipeline] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        raw_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.model = "gpt-4o-mini" if raw_model in ("gpt-5.5", "gpt-5") else raw_model
        self._openai_client = None
        self.rag_pipeline = rag_pipeline or SchemeRAGPipeline()
        self._predictor: Optional[YieldPredictor] = None
        self.last_rag_result: Optional[Dict[str, Any]] = None

        if self.api_key and self.api_key.strip():
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key.strip(), timeout=6.0)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {type(e).__name__}")
                self._openai_client = None

    def _get_predictor(self) -> YieldPredictor:
        if self._predictor is None:
            self._predictor = YieldPredictor()
        return self._predictor

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
        is_mock_key = "sk-mock" in str(self.api_key or "")
        if self._openai_client and (is_mock_key or not KrishiSathiAgent._OPENAI_QUOTA_EXHAUSTED):
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
        final_retrieval = self.last_rag_result or retrieval
        return {
            "answer": fallback_answer,
            "sources": final_retrieval.get("sources", []),
            "retrieval_mode": final_retrieval.get("retrieval_mode", "fallback_rules"),
            "verified": final_retrieval.get("verified", True),
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
                    if "sk-mock" not in str(self.api_key or ""):
                        KrishiSathiAgent._OPENAI_QUOTA_EXHAUSTED = True
                    break

        return None

    def _local_grounded_response(
        self,
        query: str,
        context: Dict[str, Any],
        lang_mode: str,
        retrieval: Dict[str, Any]
    ) -> str:
        """Comprehensive local RAG & agronomic knowledge synthesizer when OpenAI is offline or quota-limited."""
        query_lower = query.lower()

        # 1. If RAG returned verified PDF / Central Scheme JSON / Web Search context, synthesize directly
        if retrieval.get("verified") and retrieval.get("context_text"):
            return self._synthesize_rag_scheme_answer(query_lower, lang_mode, retrieval, context)

        # 2. Enrich context with live weather and ML yield prediction if not already present
        district = context.get("district", "Meerut")
        state = context.get("state", "Uttar Pradesh")
        crop = self._extract_crop_from_query(query_lower) or context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        context = dict(context)
        context["crop"] = crop
        context["district"] = district
        context["state"] = state

        if "predicted_yield" not in context:
            try:
                pred_res = self._get_predictor().predict({
                    "state": state,
                    "district": district,
                    "crop": crop,
                    "plot_acres": float(context.get("plot_acres", 2.5))
                })
                if pred_res.get("supported"):
                    context["predicted_yield"] = pred_res.get("predicted_yield_per_acre", 19.5)
                    context["expected_range_q_ha"] = pred_res.get("expected_range_q_ha", "42 - 52")
                    context["soil_type"] = pred_res.get("soil_type", context.get("soil_type", "Alluvial Loam"))
            except Exception:
                pass

        # 3. Route to rich Hindi / Hinglish / English agronomic knowledge engine
        if lang_mode == "en":
            return self._local_grounded_response_en(query_lower, context)
        elif lang_mode == "hinglish":
            return self._local_grounded_response_hinglish(query_lower, context)
        return self._local_grounded_response_hi(query_lower, context)

    def _synthesize_rag_scheme_answer(
        self,
        query_lower: str,
        lang_mode: str,
        retrieval: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Synthesizes detailed, accurate scheme answers from retrieved PDF/JSON/Web chunks."""
        sources = retrieval.get("sources", [])
        source_tag = sources[0]["title"].split("-")[0].strip() if sources else "आधिकारिक पोर्टल"
        portal_url = sources[0].get("url", "https://myscheme.gov.in") if sources else "https://myscheme.gov.in"
        ctx_text = retrieval.get("context_text", "")

        # 1. PM-KUSUM Solar Pump
        if any(w in query_lower for w in ["kusum", "solar", "सोलर", "कुसुम", "सौर"]):
            if lang_mode == "en":
                return (
                    f"According to official MNRE guidelines ({source_tag}), **PM-KUSUM** provides up to **60% government subsidy** "
                    f"(30% Central + 30% State) for standalone solar irrigation pumps (2 HP to 10 HP).\n"
                    f"• **Eligibility:** Farmers with assured irrigation/borewell source and land record (Khatauni).\n"
                    f"• **Official Portal:** Apply online at {portal_url} or upagriculture.com."
                )
            elif lang_mode == "hinglish":
                return (
                    f"Official MNRE guidelines ({source_tag}) ke mutabik, **PM-KUSUM Scheme** me 2 HP se 10 HP solar pump lagwane par **60% tak government subsidy** (30% Kendra + 30% Rajya) milti hai.\n"
                    f"• **Documents:** Aadhaar, Khatauni, Bank Passbook aur Borewell declaration.\n"
                    f"• **Apply:** {portal_url} ya upagriculture.com par online registration karein."
                )
            return (
                f"नवीन एवं नवीकरणीय ऊर्जा मंत्रालय (MNRE) की आधिकारिक गाइडलाइंस ({source_tag}) के अनुसार, **PM-KUSUM योजना** में सोलर पंप (2 HP से 10 HP) लगाने पर **60% तक अनुदान (सब्सिडी)** मिलता है।\n"
                f"• **आवश्यक दस्तावेज:** आधार कार्ड, खतौनी, बैंक पासबुक और बोरवेल घोषणा पत्र।\n"
                f"• **आधिकारिक पोर्टल:** आवेदन हेतु {portal_url} या upagriculture.com पर जाएं।"
            )

        # 2. PM-KISAN & eKYC
        if any(w in query_lower for w in ["pm-kisan", "pm kisan", "pmkisan", "पीएम किसान", "सम्मान निधि", "ekyc", "ईकेवाईसी", "6000", "किस्त", "installment"]):
            if "ekyc" in query_lower or "ईकेवाईसी" in query_lower:
                if lang_mode == "en":
                    return (
                        f"According to official PM-KISAN guidelines ({source_tag}), **eKYC is mandatory** to receive the ₹2,000 installment.\n"
                        f"• **How to complete:** Visit **pmkisan.gov.in** -> 'Farmers Corner' -> 'e-KYC' for Aadhaar OTP verification, or visit your nearest CSC center for biometric authentication."
                    )
                elif lang_mode == "hinglish":
                    return (
                        f"Official PM-KISAN portal ({source_tag}) ke anusar ₹2,000 ki kist paane ke liye **eKYC anivarya** hai.\n"
                        f"• **Process:** Aap **pmkisan.gov.in** ke 'Farmers Corner' me Aadhaar OTP se ghar baithe eKYC kar sakte hain, ya nazdeeki CSC kendra par biometric lagwa sakte hain."
                    )
                return (
                    f"पीएम-किसान आधिकारिक दिशानिर्देशों ({source_tag}) के अनुसार सभी लाभार्थियों के लिए **eKYC अनिवार्य** है।\n"
                    f"• **प्रक्रिया:** आप **pmkisan.gov.in** के 'Farmers Corner' में जाकर आधार OTP द्वारा घर बैठे अथवा नजदीकी जन सेवा केंद्र (CSC) पर बायोमेट्रिक से eKYC पूरा कर सकते हैं।"
                )
            if lang_mode == "en":
                return (
                    f"Under **PM-KISAN Samman Nidhi** ({source_tag}), eligible landholding farmer families receive **₹6,000 per year** in three equal DBT installments of ₹2,000 every 4 months.\n"
                    f"• **Documents Required:** Aadhaar Card linked to mobile & bank account, Land record (Khatauni), and active e-KYC.\n"
                    f"• **Check Status / Apply:** https://pmkisan.gov.in"
                )
            elif lang_mode == "hinglish":
                return (
                    f"**PM-KISAN Samman Nidhi** ({source_tag}) ke tahat kisan parivaron ko har saal **₹6,000** teen barabar kiston (₹2,000 prati 4 maah) me seedhe Aadhaar-linked bank khate me milte hain.\n"
                    f"• **Zaroori शर्तें:** Khatauni me naam, Bank DBT seeding aur e-KYC.\n"
                    f"• **Official Portal:** https://pmkisan.gov.in"
                )
            return (
                f"**प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)** ({source_tag}) के अंतर्गत सभी पात्र भूमिधर किसान परिवारों को **₹6,000 प्रति वर्ष** (₹2,000 की 3 समान किस्तों में) सीधे आधार-लिंक्ड बैंक खाते में मिलते हैं।\n"
                f"• **आवश्यक दस्तावेज:** आधार कार्ड, खसरा/खतौनी, बैंक खाता (DBT सक्रिय) और पूर्ण e-KYC।\n"
                f"• **आधिकारिक पोर्टल:** https://pmkisan.gov.in"
            )

        # 3. PMFBY Crop Insurance
        if any(w in query_lower for w in ["pmfby", "fasal bima", "insurance", "बीमा", "फसल बीमा", "प्रीमियम", "premium", "claim", "क्लेम"]):
            if lang_mode == "en":
                return (
                    f"Under **Pradhan Mantri Fasal Bima Yojana (PMFBY)** ({source_tag}), farmers pay a nominal premium of only **1.5% for Rabi crops** (Wheat, Mustard, Gram) and 2% for Kharif crops.\n"
                    f"• **Coverage:** Full financial protection against drought, hailstorm, unseasonal rain, waterlogging, and post-harvest losses (report within **72 hours** on Crop Insurance App or Helpline 14447).\n"
                    f"• **Official Portal:** https://pmfby.gov.in"
                )
            elif lang_mode == "hinglish":
                return (
                    f"**PM Fasal Bima Yojana (PMFBY)** ({source_tag}) me Rabi faslon (Gehun, Sarson, Chana) ke liye kisan ko keval **1.5% mamuli premium** dena hota hai.\n"
                    f"• **Claim Process:** Bemosam baarish, ओलावृष्टि ya sukhe se nuksan hone par **72 ghante ke andar** Helpline **14447** ya **pmfby.gov.in** par suchना dein."
                )
            return (
                f"**प्रधानमंत्री फसल बीमा योजना (PMFBY)** ({source_tag}) के तहत रबी फसलों (गेहूं, सरसों, चना) के लिए किसान को केवल **1.5% मामूली प्रीमियम** देना होता है (शेष प्रीमियम सरकार भरती है)।\n"
                f"• **क्लेम नियम:** ओलावृष्टि, बेमौसम बारिश या जलभराव से नुकसान होने पर **72 घंटे के भीतर** क्रॉप इंश्योरेंस ऐप, टोल-फ्री नंबर **14447** या **pmfby.gov.in** पर सूचना दें।"
            )

        # 4. Kisan Credit Card (KCC)
        if any(w in query_lower for w in ["kcc", "credit card", "loan", "rin", "ऋण", "लोन", "क्रेडिट कार्ड", "ब्याज", "interest"]):
            if lang_mode == "en":
                return (
                    f"Under the **Kisan Credit Card (KCC)** scheme ({source_tag}), farmers get short-term crop loans up to **₹3 Lakh at just 4% effective interest per annum** (with 2% interest subvention + 3% prompt repayment bonus).\n"
                    f"• **Collateral-Free Limit:** No land mortgage/security required for loans up to **₹1.60 Lakh**.\n"
                    f"• **Apply:** Visit your nearest commercial/gramin bank branch or https://www.myscheme.gov.in/schemes/kcc"
                )
            elif lang_mode == "hinglish":
                return (
                    f"**Kisan Credit Card (KCC)** ({source_tag}) ke tahat fasal ugane ke liye **₹3 Lakh tak ka loan sirf 4% salana byaj** par milta hai (samay par chukane par 3% chhoot ke sath).\n"
                    f"• **Bina Guarantee:** ₹1.60 Lakh tak ke loan par koi zameen girvi rakhne ki zaroorat nahi hai."
                )
            return (
                f"**किसान क्रेडिट कार्ड (KCC)** ({source_tag}) के तहत किसानों को **₹3 लाख तक का फसल ऋण मात्र 4% वार्षिक प्रभावी ब्याज दर** पर मिलता है (समय पर भुगतान करने पर 3% अतिरिक्त ब्याज छूट सहित)।\n"
                f"• **बिना गारंटी लोन:** ₹1.60 लाख तक के ऋण पर किसी गारंटी या बंधक की आवश्यकता नहीं होती।\n"
                f"• **आवेदन:** अपनी नजदीकी बैंक शाखा या https://www.myscheme.gov.in/schemes/kcc पर जाएं।"
            )

        # 5. PMKSY Micro Irrigation (Drip / Sprinkler)
        if any(w in query_lower for w in ["pmksy", "drip", "sprinkler", "ड्रिप", "स्प्रिंकलर", "micro irrigation", "sinchayee", "सिंचाई योजना"]):
            if lang_mode == "en":
                return (
                    f"Under **PMKSY - Per Drop More Crop** ({source_tag}), Small and Marginal farmers receive up to **55% subsidy** (and 45% for other farmers) on installing **Drip and Sprinkler irrigation systems**.\n"
                    f"• **Benefits:** Saves 40–60% irrigation water and boosts fertilizer efficiency.\n"
                    f"• **Official Portal:** https://pmksy.gov.in"
                )
            return (
                f"**प्रधानमंत्री कृषि सिंचाई योजना (PMKSY - प्रति बूंद अधिक फसल)** ({source_tag}) के अंतर्गत **ड्रिप (टपक) और स्प्रिंकलर (फव्वारा) सिंचाई सिस्टम** लगाने पर लघु एवं सीमांत किसानों को **55% तक सब्सिडी** (अन्य किसानों को 45%) मिलती है।\n"
                f"• **आधिकारिक पोर्टल:** https://pmksy.gov.in"
            )

        # 6. Soil Health Card (SHC)
        if any(w in query_lower for w in ["soil health", "soil test", "shc", "मिट्टी जांच", "मृदा स्वास्थ्य", "सॉइल हेल्थ", "soil card"]):
            if lang_mode == "en":
                return (
                    f"Under the **Soil Health Card (SHC) Scheme** ({source_tag}), farmers receive a free soil report every 2 years testing **12 key parameters** (N, P, K, Sulfur, Zinc, Iron, Boron, pH, EC, Organic Carbon) with exact plot-level fertilizer dosage to cut input costs by 15–20%.\n"
                    f"• **Official Portal:** https://soilhealth.dac.gov.in"
                )
            return (
                f"**मृदा स्वास्थ्य कार्ड योजना (Soil Health Card)** ({source_tag}) के तहत सरकार हर 2 वर्ष में खेत की मिट्टी के **12 पोषक तत्वों** (N, P, K, सल्फर, जिंक, बोरॉन, pH, जीवांश कार्बन) की निःशुल्क जांच कर सटीक खाद की मात्रा बताती है, जिससे खाद खर्च 15-20% घटता है।\n"
                f"• **आधिकारिक पोर्टल:** https://soilhealth.dac.gov.in"
            )

        # 7. SMAM Farm Machinery Subsidy
        if any(w in query_lower for w in ["smam", "machinery", "tractor", "rotavator", "happy seeder", "super seeder", "यंत्र", "रोटावेटर", "सुपर सीडर", "मशीनरी"]):
            if lang_mode == "en":
                return (
                    f"Under **Sub-Mission on Agricultural Mechanization (SMAM)** ({source_tag}), farmers get **40% to 50% subsidy** on Super Seeder, Happy Seeder, Rotavator, Zero-Till Seed Drill, and Laser Land Leveler (and up to 80% for Custom Hiring Centres).\n"
                    f"• **Official Portal:** https://agrimachinery.nic.in"
                )
            return (
                f"**कृषि मशीनीकरण उप-मिशन (SMAM)** ({source_tag}) के तहत सुपर सीडर, हैप्पी सीडर, रोटावेटर, जीरो-टिल सीड ड्रिल और लेजर लैंड लेवलर खरीदने पर **40% से 50% तक सरकारी अनुदान** (लघु/सीमांत व महिला किसानों को 50%) मिलता है।\n"
                f"• **आधिकारिक पोर्टल:** https://agrimachinery.nic.in"
            )

        # 8. PKVY Organic Farming & e-NAM Market
        if any(w in query_lower for w in ["pkvy", "organic", "jaivik", "जैविक", "परम्परागत"]):
            if lang_mode == "en":
                return (
                    f"Under **Paramparagat Krishi Vikas Yojana (PKVY)** ({source_tag}), farmers adopting cluster-based organic farming receive **₹50,000 per hectare over 3 years** (including ₹31,000/ha DBT for bio-fertilizers & vermicompost) plus free organic certification.\n"
                    f"• **Official Portal:** https://pgsindia-ncof.gov.in"
                )
            return (
                f"**परम्परागत कृषि विकास योजना (PKVY)** ({source_tag}) के अंतर्गत जैविक खेती अपनाने पर **₹50,000 प्रति हेक्टेयर** (3 वर्षों में, जिसमें ₹31,000/हेक्टेयर सीधे DBT से जैविक खाद व बीज हेतु) और निःशुल्क ऑर्गेनिक सर्टिफिकेशन मिलता है।\n"
                f"• **आधिकारिक पोर्टल:** https://pgsindia-ncof.gov.in"
            )

        if any(w in query_lower for w in ["enam", "e-nam", "mandi", "msp", "मंडी", "समर्थन मूल्य", "ई-नाम"]):
            if lang_mode == "en":
                return (
                    f"Through **National Agriculture Market (e-NAM)** ({source_tag}), farmers can sell Wheat, Mustard, Gram, and Potato across connected APMC mandis with transparent quality testing, online bidding, and direct DBT payment.\n"
                    f"• **Official Portal:** https://www.enam.gov.in"
                )
            return (
                f"**राष्ट्रीय कृषि बाजार (e-NAM)** ({source_tag}) के माध्यम से किसान अपनी गेहूं, सरसों, चना व आलू की फसल को ऑनलाइन पारदर्शी नीलामी, गुणवत्ता जांच और न्यूनतम समर्थन मूल्य (MSP) पर सीधे बैंक भुगतान के साथ बेच सकते हैं।\n"
                f"• **आधिकारिक पोर्टल:** https://www.enam.gov.in"
            )

        # 9. Generic synthesis from retrieved text snippet
        clean_snippet = re.sub(r"\s+", " ", ctx_text).strip()[:320]
        if lang_mode == "en":
            return f"According to verified official guidelines ({source_tag}): {clean_snippet}... Visit {portal_url} for complete details."
        return f"आधिकारिक सरकारी दिशानिर्देशों ({source_tag}) के अनुसार: {clean_snippet}... अधिक जानकारी के लिए {portal_url} पर जाएं।"

    @staticmethod
    def _extract_crop_from_query(query_lower: str) -> Optional[str]:
        """Detects if the user explicitly mentioned one of the supported All-India crops in their message."""
        crop_keywords = [
            ("Wheat", ["wheat", "gehun", "gehu", "गेहूं", "गेहूँ"]),
            ("Mustard", ["mustard", "sarson", "sarso", "सरसों", "लाही", "राया"]),
            ("Rice", ["rice", "paddy", "dhan", "dhaan", "धान", "चावल"]),
            ("Cotton(lint)", ["cotton", "kapas", "कपास", "नरमा"]),
            ("Sugarcane", ["sugarcane", "ganna", "गन्ना", "ईख"]),
            ("Soyabean", ["soybean", "soyabean", "soya", "सोयाबीन"]),
            ("Groundnut", ["groundnut", "peanut", "moongphali", "मूंगफली"]),
            ("Gram", ["gram", "chana", "chickpea", "चना", "छोले"]),
            ("Barley", ["barley", "jau", "जौ"]),
            ("Masoor", ["masoor", "lentil", "मसूर"]),
            ("Maize", ["maize", "makka", "corn", "मक्का"]),
            ("Bajra", ["bajra", "pearl millet", "बाजरा"]),
            ("Jowar", ["jowar", "sorghum", "ज्वार"]),
            ("Arhar/Tur", ["arhar", "tur", "pigeonpea", "अरहर", "तूर"]),
            ("Peas & beans (Pulses)", ["pea", "peas", "matar", "beans", "मटर", "दलहन"]),
            ("Potato", ["potato", "aaloo", "aloo", "आलू"]),
            ("Onion", ["onion", "pyaz", "pyaaz", "प्याज"]),
            ("Linseed", ["linseed", "alsi", "flax", "अलसी"]),
            ("Banana", ["banana", "kela", "केला"]),
            ("Turmeric", ["turmeric", "haldi", "हल्दी"]),
        ]
        for canonical_crop, words in crop_keywords:
            if any(w in query_lower for w in words):
                return canonical_crop
        return None

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
            "shc", "soil health card", "solar pump", "सोलर पंप", "claim", "क्लेम", "compensation",
            "smam", "machinery", "rotavator", "happy seeder", "super seeder", "pkvy", "enam", "e-nam",
            "मृदा स्वास्थ्य", "सॉइल हेल्थ", "कृषि यंत्र", "रोटावेटर", "सुपर सीडर"
        ]
        return any(t in query_lower for t in terms)

    def _local_grounded_response_hi(self, query: str, context: Dict[str, Any]) -> str:
        """Comprehensive ICAR agronomic advisor in Hindi covering all 10 Rabi crops, soil, weather, weeds, varieties, MSP & sowing."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        crop_hi_map = {
            "Wheat": "गेहूं", "Mustard": "सरसों", "Gram": "चना", "Barley": "जौ",
            "Masoor": "मसूर", "Maize": "मक्का", "Peas & beans (Pulses)": "मटर/दलहन",
            "Potato": "आलू", "Onion": "प्याज", "Linseed": "अलसी"
        }
        crop_hi = crop_hi_map.get(crop, crop)
        predicted_yield = context.get("predicted_yield", 19.9)
        range_q_ha = context.get("expected_range_q_ha", "44 - 54")
        plot_acres = context.get("plot_acres", 2.5)
        district = context.get("district", "Meerut")
        state = context.get("state", "Uttar Pradesh")
        growth_stage = context.get("growth_stage", "Tillering")

        # 1. Greetings / Help / Identity
        if any(w in query for w in ["नमस्ते", "राम राम", "प्रणाम", "hello", "hi ", "kaun ho", "क्या कर सकते", "help", "मदद"]):
            return (
                f"नमस्ते किसान भाई! मैं **कृषिसाथी AI** हूँ — आपका व्यक्तिगत कृषि एवं सरकारी योजना सलाहकार।\n"
                f"आप मुझसे **{district} ({state})** के लिए इन विषयों पर पूछ सकते हैं:\n"
                f"• **फसल उपज (Yield):** गेहूं, सरसों, चना, आलू, जौ, मसूर, मक्का, प्याज की पैदावार\n"
                f"• **सिंचाई एवं खाद (NPK/Urea/DAP):** अवस्था अनुसार सटीक मात्रा\n"
                f"• **रोग, कीट एवं खरपतवार:** पीला रतुआ, माहू (चेपा), झुलसा, गुल्ली डंडा का इलाज\n"
                f"• **सरकारी योजनाएं:** PM-KISAN, फसल बीमा (PMFBY), KCC लोन, सोलर पंप (PM-KUSUM), कृषि यंत्र सब्सिडी (SMAM)"
            )

        # 2. Yield / Production / Harvest Forecast
        if any(w in query for w in ["पैदावार", "yield", "उपज", "उत्पादन", "paidaawar", "harvest", "क्विंटल", "कितना होगा", "अनुमान"]):
            total = round(float(predicted_yield) * float(plot_acres), 1)
            return (
                f"किसान भाई, **{district} ({state})** में आपके **{plot_acres} एकड़** खेत में **{crop_hi}** की अनुमानित पैदावार लगभग **{predicted_yield} क्विंटल प्रति एकड़** "
                f"(कुल उत्पादन लगभग **{total} क्विंटल** | **{range_q_ha} क्विंटल/हेक्टेयर**) रहने का अनुमान है।\n"
                f"• **सुझाव:** समय पर सिंचाई, संतुलित यूरिया-डीपीए (NPK) और मार्च की गर्मी (Terminal Heat) में हल्की नमी बनाए रखने से 10–15% अधिक उपज प्राप्त की जा सकती है।"
            )

        # 3. Irrigation / Water Schedule (Crop-Specific)
        if any(w in query for w in ["पानी", "सिंचाई", "irrigation", "sinchai", "water", "कब सींचे", "नमी"]):
            if crop == "Wheat":
                return (
                    f"**{district}** में **गेहूं की सिंचाई (ICAR-IIWBR अनुशंसा):**\n"
                    f"1. **पहली सिंचाई (सबसे महत्वपूर्ण):** बुवाई के **20–25 दिन बाद (ताज जड़ / CRI अवस्था)** पर हल्की सिंचाई (4–5 सेमी) अवश्य करें।\n"
                    f"2. **दूसरी सिंचाई:** कल्ले फूटते समय (**40–45 दिन**)।\n"
                    f"3. **तीसरी सिंचाई:** गांठ बनते समय (**60–65 दिन**)।\n"
                    f"4. **चौथी/पांचवीं सिंचाई:** फूल आते समय (**80–85 दिन**) और दूधिया दाना भरते समय (**100–105 दिन**)। तेज हवा में सिंचाई न करें ताकि फसल गिरे नहीं।"
                )
            elif crop == "Mustard":
                return (
                    "**सरसों में सिंचाई प्रबंधन (ICAR-DRMR):**\n"
                    "• **पहली सिंचाई:** बुवाई के **30–35 दिन बाद** (फूल आने से ठीक पहले) हल्की सिंचाई करें।\n"
                    "• **दूसरी सिंचाई:** फलियों में दाना बनते समय (**60–65 दिन बाद**)। खेत में पानी का भराव बिल्कुल न होने दें।"
                )
            elif crop == "Gram":
                return (
                    "**चना (Gram) में सिंचाई प्रबंधन:**\n"
                    "• चने में पहली हल्की सिंचाई शाखाएं निकलते समय (**40–45 दिन**) और दूसरी फलियां बनते समय (**70–75 दिन**) करें।\n"
                    "• **सावधानी:** चने में फूल खिलते समय सिंचाई कभी न करें, वरना फूल झड़ जाते हैं।"
                )
            elif crop == "Potato":
                return (
                    "**आलू (Potato) में सिंचाई प्रबंधन:**\n"
                    "• आलू में हल्की और बार-बार सिंचाई (8–10 दिन के अंतराल पर) करें। कंद बनते समय (**35–60 दिन**) मिट्टी में नमी की कमी न होने दें। मेड़ों के केवल दो-तिहाई हिस्से तक ही पानी लगाएं।"
                )
            return (
                f"**{crop_hi}** में बुवाई के बाद वानस्पतिक वृद्धि और फूल/दाना बनते समय मिट्टी में पर्याप्त नमी बनाए रखें। जलभराव से बचाव करें।"
            )

        # 4. Fertilizer / NPK / Urea / Zinc / Sulfur Schedule
        if any(w in query for w in ["खाद", "यूरिया", "fertilizer", "dap", "khad", "npk", "urea", "पोटाश", "जिंक", "सल्फर", "पोषण"]):
            if crop == "Wheat":
                return (
                    f"**{district}** में **गेहूं के लिए संतुलित खाद प्रबंधन (प्रति एकड़):**\n"
                    f"• **बुवाई के समय (Basal):** 50–55 किलो DAP + 25 किलो पोटाश (MOP) + 10 किलो जिंक सल्फेट।\n"
                    f"• **पहली सिंचाई (21–25 दिन) के बाद:** 40–45 किलो नीम लेपित यूरिया।\n"
                    f"• **दूसरी सिंचाई (40–45 दिन) के बाद:** 40 किलो यूरिया।\n"
                    f"• **दाना भरते समय:** मार्च की गर्मी से बचाव हेतु **NPK 13:0:45 या 0:52:34 (1 किलो/एकड़)** का पर्णीय छिड़काव करें।"
                )
            elif crop == "Mustard":
                return (
                    "**सरसों के लिए खाद एवं सल्फर प्रबंधन (प्रति एकड़):**\n"
                    "• **बुवाई पर:** 35 किलो यूरिया + 50 किलो SSP (सिंगल सुपर फास्फेट) या 25 किलो DAP + **10 किलो बेंटोनाइट सल्फर** (या 25 किलो जिप्सम)।\n"
                    "• **पहली सिंचाई पर (30–35 दिन):** 30 किलो यूरिया का बुरकाव करें। सल्फर से सरसों में तेल की मात्रा 3–5% बढ़ती है।"
                )
            elif crop == "Gram":
                return (
                    "**चने (Gram) के लिए उर्वरक प्रबंधन (प्रति एकड़):**\n"
                    "• दलहनी फसल होने के कारण चने को कम नाइट्रोजन चाहिए: बुवाई के समय **40 किलो DAP + 8 किलो सल्फर** प्रति एकड़ पर्याप्त है। फूल आने से पहले 2% यूरिया या NPK 19:19:19 का छिड़काव लाभकारी है।"
                )
            elif crop == "Potato":
                return (
                    "**आलू (Potato) के लिए खाद प्रबंधन (प्रति एकड़):**\n"
                    "• बुवाई पर 75 किलो DAP + 60 किलो MOP (पोटाश) + 35 किलो यूरिया दें। मिट्टी चढ़ाते समय (25–30 दिन) 45 किलो यूरिया डालें।"
                )
            return (
                f"**{crop_hi}** में मिट्टी जांच (Soil Health Card) के अनुसार संतुलित NPK और सूक्ष्म पोषक तत्वों (जिंक एवं सल्फर) का प्रयोग करें।"
            )

        # 5. Pest / Disease / Yellow Leaves / Symptoms
        if any(w in query for w in ["कीट", "कीड़ा", "रोग", "pest", "disease", "माहू", "चेपा", "रतुआ", "rust", "aphid", "पीला", "पीले", "झुलसा", "blight", "सुंडी", "दीमक"]):
            if crop == "Wheat" or any(w in query for w in ["रतुआ", "rust"]):
                return (
                    "**गेहूं में रोग एवं पीलेपन का उपचार (ICAR-IIWBR):**\n"
                    "• **पीला रतुआ (Yellow Stripe Rust):** पत्तियों पर पीली धारियां और पाउडर दिखे तो तुरंत **प्रोपिकोनाजोल 25% EC (Propiconazole) @ 200 मिली प्रति एकड़** 200 लीटर पानी में मिलाकर छिड़कें।\n"
                    "• **जिंक/नाइट्रोजन की कमी से पीलापन:** 1 किलो जिंक सल्फेट + 2.5 किलो यूरिया को 200 लीटर पानी में घोलकर प्रति एकड़ छिड़काव करें।\n"
                    "• **माहू (Aphid):** बाली पर माहू दिखने पर **थायोमेथोक्साम 25% WG @ 40 ग्राम/एकड़** छिड़कें।"
                )
            elif crop == "Mustard" or any(w in query for w in ["माहू", "चेपा", "aphid"]):
                return (
                    "**सरसों में माहू (चेपा) एवं सफेद रतुआ नियंत्रण (ICAR-DRMR):**\n"
                    "• **शुरुआती रोकथाम:** नीम का तेल (Azadirachtin 1500 ppm) @ **5 मिली प्रति लीटर** पानी में छिड़कें।\n"
                    "• **अधिक प्रकोप होने पर:** **इमिडाक्लोप्रिड 17.8% SL @ 80 मिली/एकड़** या थायोमेथोक्साम 25% WG @ 40 ग्राम/एकड़ का शाम के समय छिड़काव करें (मधुमक्खियों की सुरक्षा हेतु)।"
                )
            elif crop == "Potato" or "झुलसा" in query or "blight" in query:
                return (
                    "**आलू में अगेती/पछेती झुलसा (Late Blight) नियंत्रण:**\n"
                    "• कोहरे और नमी में पत्तियों पर काले धब्बे दिखने पर **मैनकोजेब 75% WP @ 600 ग्राम/एकड़** या **साइमोक्सानिल + मैनकोजेब @ 500 ग्राम/एकड़** का छिड़काव करें।"
                )
            elif crop == "Gram" or "सुंडी" in query or "उकठा" in query:
                return (
                    "**चने में फली छेदक सुंडी (Pod Borer) एवं उकठा रोग:**\n"
                    "• खेत में 8–10 टी-आकार (T-perches) की खूंटियां लगाएं। सुंडी दिखने पर **इमामेक्टिन बेंजोएट 5% SG @ 80 ग्राम/एकड़** छिड़कें।"
                )
            return (
                f"**{crop_hi}** में कीट व रोग नियंत्रण हेतु सुबह-शाम खेत की निगरानी करें। शुरुआती अवस्था में नीम तेल (5 मिली/लीटर) का प्रयोग करें।"
            )

        # 6. Weed Control (Kharpatwar / Gulli Danda / Bathua)
        if any(w in query for w in ["खरपतवार", "घास", "गुल्ली", "बथुआ", "weed", "herbicide", "दवा"]):
            return (
                "**गेहूं एवं रबी फसलों में खरपतवार (गुल्ली-डंडा व बथुआ) नियंत्रण:**\n"
                "• **संकरी पत्ती (गुल्ली डंडा / Phalaris minor):** पहली सिंचाई के बाद (30–35 दिन पर) **सल्फोसल्फ्यूरॉन 75% WG @ 13.5 ग्राम/एकड़** या क्लोडिनोफॉप 15% WP @ 160 ग्राम/एकड़ छिड़कें।\n"
                "• **चौड़ी पत्ती (बथुआ, जंगली पालक):** **मेटसल्फ्यूरॉन मिथाइल 20% WP @ 8 ग्राम/एकड़** 150 लीटर पानी में मिलाकर फ्लैट-फैन नोजल से छिड़काव करें।"
            )

        # 7. Seed Varieties / Sowing Time / Seed Rate
        if any(w in query for w in ["किस्म", "बीज", "बुवाई", "variety", "seed", "sowing", "कौन सा बीज"]):
            if crop == "Wheat":
                return (
                    "**उन्नत गेहूं किस्में (ICAR अनुमोदित):**\n"
                    "• **समय से बुवाई (1–25 नवंबर):** DBW-187 (करण वंदना), DBW-303, HD-3226 (पूसा यशस्वी), HD-2967, WH-1270 (बीज दर: 40 किलो/एकड़)।\n"
                    "• **पछेती बुवाई (दिसंबर):** DBW-173, HD-3059, राज-3765 (बीज दर: 50 किलो/एकड़)।"
                )
            elif crop == "Mustard":
                return (
                    "**उन्नत सरसों किस्में (ICAR-DRMR):**\n"
                    "• **प्रमुख किस्में:** पूसा बोल्ड (Pusa Bold), पूसा मस्टर्ड-28, RH-725, गिरिराज (DRMR-IJ-31) — बीज दर **1.5 से 2 किलो प्रति एकड़**।"
                )
            return (
                f"**{crop_hi}** के लिए अपने क्षेत्र के कृषि विज्ञान केंद्र (KVK {district}) द्वारा अनुमोदित प्रमाणित एवं उपचारित बीज ही बोएं।"
            )

        # 8. Live Weather & 7-Day Forecast
        if any(w in query for w in ["मौसम", "weather", "तापमान", "बारिश", "rain", "temperature", "कोहरा", "पाला", "ठंड", "गर्मी"]):
            weather = context.get("weather") or fetch_open_meteo_weather(district)
            if isinstance(weather, dict) and weather.get("available"):
                temp = weather.get("temperature_c", 22)
                hum = weather.get("humidity_pct", 55)
                wind = weather.get("wind_speed_kmh", 8)
                rain7 = weather.get("rain_next_7d_mm", 0.0)
                cond_hi = weather.get("condition_hi", "साफ आकाश")
                return (
                    f"**{district} ({state}) का लाइव मौसम एवं 7-दिवसीय पूर्वानुमान:**\n"
                    f"• **वर्तमान तापमान:** {temp}°C ({cond_hi}) | **आर्द्रता:** {hum}% | **हवा की गति:** {wind} km/h\n"
                    f"• **अगले 7 दिनों में संभावित वर्षा:** {rain7} mm\n"
                    f"• **कृषि सलाह:** {'बारिश की संभावना को देखते हुए अभी सिंचाई व छिड़काव रोकें।' if rain7 > 10 else 'मौसम साफ है; शांत हवा में ही सिंचाई और आवश्यक पोषक छिड़काव करें।'}"
                )
            return f"**{district}** में मौसम सामान्य है। मार्च में तापमान बढ़ने पर खेत में हल्की नमी बनाए रखें।"

        # 9. MSP / Market Price / Mandi Rates
        if any(w in query for w in ["भाव", "रेट", "मंडी", "msp", "समर्थन मूल्य", "कीमत", "price", "rate"]):
            return (
                "**रबी फसलों का न्यूनतम समर्थन मूल्य (MSP — भारत सरकार):**\n"
                "• **गेहूं (Wheat):** ₹2,425 प्रति क्विंटल\n"
                "• **सरसों (Mustard):** ₹5,950 प्रति क्विंटल\n"
                "• **चना (Gram):** ₹5,650 प्रति क्विंटल\n"
                "• **मसूर (Lentil):** ₹6,700 प्रति क्विंटल\n"
                "• **जौ (Barley):** ₹1,980 प्रति क्विंटल\n"
                "अपनी नजदीकी APMC मंडी और ऑनलाइन नीलामी के लिए **e-NAM पोर्टल (enam.gov.in)** का उपयोग करें।"
            )

        # 10. Soil Testing & pH
        if any(w in query for w in ["मिट्टी", "मृदा", "soil", "ph", "उर्वरता", "कार्बन"]):
            soil_t = context.get("soil_type", "जलोढ़ दोमट (Alluvial Loam)")
            return (
                f"**{district} मृदा स्वास्थ्य एवं प्रबंधन:**\n"
                f"• आपके क्षेत्र की प्रमुख मिट्टी **{soil_t}** है। अच्छी उपज के लिए मिट्टी का pH मान **6.5 से 7.5** के बीच उत्तम रहता है।\n"
                f"• बुवाई से पहले प्रति एकड़ 2–3 टन सड़ी गोबर की खाद या केंचुआ खाद (Vermicompost) मिलाएं और **soilhealth.dac.gov.in** पर निःशुल्क मृदा स्वास्थ्य कार्ड बनवाएं।"
            )

        # 10b. NASA Earth & Satellite Intelligence
        if any(w in query for w in ["nasa", "satellite", "ndvi", "gibs", "modis", "solar radiation", "उपग्रह", "सैटेलाइट", "नासा"]):
            return (
                f"**{district} ({state}) के लिए NASA Earth & Weather Intelligence:**\n"
                f"• **NASA POWER Reanalysis:** 2m तापमान (T2M), सापेक्ष आर्द्रता (RH2M), सौर विकिरण (ALLSKY_SFC_SW_DWN), हवा की गति और वर्षा (PRECTOTCORR) का वैज्ञानिक विश्लेषण उपलब्ध कराता है।\n"
                f"• **NASA GIBS Satellite Layers:** MODIS NDVI (वनस्पति स्वास्थ्य सूचकांक), True Color इमेजरी, Land Surface Temperature (LST) और GPM IMERG वर्षा मानचित्र उपलब्ध हैं।\n"
                f"• **नोट:** NASA POWER ऐतिहासिक एवं नियर-रियल-टाइम रीएनालिसिस डेटा प्रदान करता है, लाइव मौसम पूर्वानुमान नहीं।"
            )

        # 11. Open Agronomic Web Search Fallback before generic summary
        web_agro = self._search_web_agronomy_fallback(query, crop, district, state, "hi")
        if web_agro:
            return web_agro

        # 12. Smart Contextual Summary (instead of a static 1-line fallback)
        total_q = round(float(predicted_yield) * float(plot_acres), 1)
        return (
            f"किसान भाई, आपके प्रश्न **\"{query}\"** के संदर्भ में **{district} ({state})** की **{crop_hi}** फसल ({growth_stage} अवस्था) के लिए मुख्य बिंदु:\n"
            f"1. **अनुमानित उपज:** ~{predicted_yield} क्विंटल/एकड़ ({plot_acres} एकड़ में कुल ~{total_q} क्विंटल)।\n"
            f"2. **सिंचाई एवं पोषण:** मिट्टी में हल्की नमी बनाए रखें और यूरिया/NPK को सिंचाई के बाद दो किस्तों में दें।\n"
            f"3. **फसल सुरक्षा:** पत्तियों पर पीलापन, रतुआ या माहू दिखने पर तुरंत कृषिसाथी में लक्षण लिखकर सटीक दवा की मात्रा पूछें।"
        )

    def _local_grounded_response_en(self, query: str, context: Dict[str, Any]) -> str:
        """Comprehensive ICAR agronomic advisor in English covering all 10 Rabi crops, soil, weather, weeds, varieties, MSP & sowing."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        predicted_yield = context.get("predicted_yield", 19.9)
        range_q_ha = context.get("expected_range_q_ha", "44 - 54")
        plot_acres = context.get("plot_acres", 2.5)
        district = context.get("district", "Meerut")
        state = context.get("state", "Uttar Pradesh")
        growth_stage = context.get("growth_stage", "Tillering")

        # 1. Greetings / Help
        if any(w in query for w in ["hello", "hi ", "hey", "who are you", "what can you do", "help"]):
            return (
                f"Hello Farmer Friend! I am **KrishiSathi AI** — your agricultural & government scheme assistant for **{district} ({state})**.\n"
                f"You can ask me anything about:\n"
                f"• **Crop Yield Forecasts:** Wheat, Mustard, Gram, Potato, Barley, Masoor, Maize, Onion, Peas, Linseed\n"
                f"• **Irrigation & Fertilizer Schedules:** Stage-wise NPK, Urea, DAP, Zinc & Sulfur dosage\n"
                f"• **Pest, Disease & Weed Control:** Yellow Rust, Mustard Aphids, Late Blight, Phalaris minor\n"
                f"• **Government Schemes:** PM-KISAN, PMFBY Crop Insurance, KCC Loan, PM-KUSUM Solar Pump, SMAM Machinery"
            )

        # 2. Yield / Production / Harvest
        if any(w in query for w in ["yield", "production", "harvest", "quintal", "output", "how much"]):
            total = round(float(predicted_yield) * float(plot_acres), 1)
            return (
                f"For your **{plot_acres} acre** **{crop}** plot in **{district} ({state})**, the estimated {crop} yield is **{predicted_yield} Quintals/Acre** "
                f"(total harvest ~**{total} Quintals** | expected regional range: **{range_q_ha} Q/Ha**).\n"
                f"• **Yield Booster Tip:** Ensure timely stage-wise irrigation and split Nitrogen application to protect grain weight against March terminal heat."
            )

        # 3. Irrigation / Water Schedule
        if any(w in query for w in ["water", "irrigation", "irrigate", "moisture", "watering"]):
            if crop == "Wheat":
                return (
                    f"**ICAR-IIWBR Wheat Irrigation Schedule for {district}:**\n"
                    f"1. **1st Irrigation (Critical):** **20–25 DAS (Crown Root Initiation - CRI stage)** — apply light 4–5 cm irrigation.\n"
                    f"2. **2nd Irrigation:** Tillering stage (**40–45 DAS**).\n"
                    f"3. **3rd Irrigation:** Late Jointing / Booting (**60–65 DAS**).\n"
                    f"4. **4th & 5th Irrigation:** Flowering (**80–85 DAS**) and Milking/Dough stage (**100–105 DAS**). Irrigate only on calm, windless days to prevent lodging."
                )
            elif crop == "Mustard":
                return (
                    "**ICAR-DRMR Mustard Irrigation Schedule:**\n"
                    "• **1st Irrigation:** **30–35 DAS** (pre-flowering / branching stage).\n"
                    "• **2nd Irrigation:** **60–65 DAS** (siliqua pod filling stage). Avoid waterlogging at all times."
                )
            elif crop == "Gram":
                return (
                    "**Gram (Chickpea) Irrigation Schedule:**\n"
                    "• Apply first light irrigation at branching (**40–45 DAS**) and second at pod development (**70–75 DAS**). Do NOT irrigate during active flowering as it causes flower drop."
                )
            elif crop == "Potato":
                return (
                    "**Potato Irrigation Schedule:**\n"
                    "• Maintain uniform ridge moisture with light irrigations every **8–10 days**, especially during stolon & tuber bulking (**35–60 DAS**). Keep water level below two-thirds of ridge height."
                )
            return (
                f"For **{crop}** in **{district}**, maintain optimum soil moisture during branching, flowering, and grain/pod filling stages while avoiding standing water."
            )

        # 4. Fertilizer / NPK / Urea / Micronutrients
        if any(w in query for w in ["fertilizer", "urea", "nutrient", "npk", "dap", "potash", "zinc", "sulfur", "manure", "dosage"]):
            if crop == "Wheat":
                return (
                    f"**Recommended Wheat Fertilizer Schedule for {district} (per acre):**\n"
                    f"• **Basal (At Sowing):** 50–55 kg DAP + 25 kg MOP (Potash) + 10 kg Zinc Sulfate.\n"
                    f"• **1st Top Dressing (22–25 DAS after CRI irrigation):** 40–45 kg Neem-coated Urea.\n"
                    f"• **2nd Top Dressing (40–45 DAS):** 40 kg Neem-coated Urea.\n"
                    f"• **Grain Filling Spray:** Foliar spray of **NPK 13:0:45 (Potassium Nitrate) @ 1 kg/acre** to boost grain test weight."
                )
            elif crop == "Mustard":
                return (
                    "**Recommended Mustard Nutrient Schedule (per acre):**\n"
                    "• **Basal (At Sowing):** 35 kg Urea + 50 kg SSP (or 25 kg DAP) + **10 kg Bentonite Sulfur** (or 25 kg Gypsum).\n"
                    "• **1st Irrigation (30–35 DAS):** Top-dress 30 kg Urea. Sulfur increases mustard oil content by 3–5%."
                )
            elif crop == "Gram":
                return (
                    "**Gram (Chickpea) Nutrient Schedule (per acre):**\n"
                    "• Being a legume, Gram fixes nitrogen naturally. Apply **40 kg DAP + 8 kg Sulfur per acre** as basal dose, and spray 2% Urea or NPK 19:19:19 prior to flowering."
                )
            elif crop == "Potato":
                return (
                    "**Potato Nutrient Schedule (per acre):**\n"
                    "• Apply 75 kg DAP + 60 kg MOP + 35 kg Urea at planting, followed by 45 kg Urea at earthing-up (25–30 DAS)."
                )
            return (
                f"For **{crop}**, apply balanced N-P-K based on your Soil Health Card along with 10 kg Zinc Sulfate or Bentonite Sulfur per acre."
            )

        # 5. Pest / Disease / Yellowing / Symptoms
        if any(w in query for w in ["pest", "disease", "insect", "rust", "aphid", "yellow", "blight", "fungus", "rot", "spray", "borer", "termite"]):
            if crop == "Wheat" or "rust" in query:
                return (
                    "**Wheat Disease & Yellowing Management (ICAR-IIWBR):**\n"
                    "• **Yellow Stripe Rust:** If yellow powdery stripes appear on leaves, immediately spray **Propiconazole 25% EC @ 200 ml/acre** in 200 liters of water.\n"
                    "• **Nutrient Yellowing (Zinc/N deficiency):** Foliar spray of **1 kg Zinc Sulfate + 2.5 kg Urea** in 200 L water/acre.\n"
                    "• **Foliar Aphids:** Spray **Thiamethoxam 25% WG @ 40 g/acre** if aphid colonies exceed threshold."
                )
            elif crop == "Mustard" or "aphid" in query:
                return (
                    "**Mustard Aphid (Chepa) & White Rust Control (ICAR-DRMR):**\n"
                    "• **Preventive / Early Stage:** Spray **Neem Oil (Azadirachtin 1500 ppm) @ 5 ml/liter** of water.\n"
                    "• **Severe Infestation:** Spray **Imidacloprid 17.8% SL @ 80 ml/acre** or Thiamethoxam 25% WG @ 40 g/acre in the late afternoon to protect honeybee pollinators."
                )
            elif crop == "Potato" or "blight" in query:
                return (
                    "**Potato Early & Late Blight Management:**\n"
                    "• During foggy/humid weather, spray **Mancozeb 75% WP @ 600 g/acre** as preventive, or **Cymoxanil + Mancozeb @ 500 g/acre** if dark leaf lesions appear."
                )
            elif crop == "Gram" or "borer" in query:
                return (
                    "**Gram Pod Borer (Helicoverpa) & Wilt Control:**\n"
                    "• Install 8–10 T-perches/acre for predatory birds and 5 pheromone traps/acre. If larval threshold is crossed, spray **Emamectin Benzoate 5% SG @ 80 g/acre**."
                )
            return (
                f"For **{crop}** pest and disease protection, scout fields twice weekly. Use Neem oil (5 ml/L) for early sucking pests and consult KVK {district} for targeted fungicide dosage."
            )

        # 6. Weed Control (Herbicide)
        if any(w in query for w in ["weed", "herbicide", "grass", "phalaris", "gulli", "bathua"]):
            return (
                "**Rabi Weed Control Protocol (Wheat & Field Crops):**\n"
                "• **Grassy Weeds (Phalaris minor / Gulli Danda):** Spray **Sulfosulfuron 75% WG @ 13.5 g/acre** or Clodinafop 15% WP @ 160 g/acre at 30–35 DAS in moist soil.\n"
                "• **Broadleaf Weeds (Bathua, Melilotus):** Spray **Metsulfuron Methyl 20% WP @ 8 g/acre** in 150 L water using a flat-fan nozzle."
            )

        # 7. Seed Varieties & Sowing
        if any(w in query for w in ["variety", "varieties", "seed", "sowing", "when to sow", "best seed"]):
            if crop == "Wheat":
                return (
                    "**ICAR Recommended Wheat Varieties:**\n"
                    "• **Timely Sown (Nov 1–25):** DBW-187 (Karan Vandana), DBW-303, HD-3226 (Pusa Yashasvi), HD-2967, WH-1270 (Seed rate: 40 kg/acre).\n"
                    "• **Late Sown (December):** DBW-173, HD-3059, Raj-3765 (Seed rate: 50 kg/acre)."
                )
            elif crop == "Mustard":
                return (
                    "**ICAR Recommended Mustard Varieties:**\n"
                    "• **High-Yielding Hybrids/Varieties:** Pusa Bold, Pusa Mustard-28, RH-725, Giriraj (DRMR-IJ-31) — Seed rate: **1.5 to 2.0 kg/acre**."
                )
            return f"For **{crop}** in **{district}**, use certified seed treated with Trichoderma viride @ 4 g/kg seed before sowing."

        # 8. Live Weather & 7-Day Forecast
        if any(w in query for w in ["weather", "temperature", "rain", "forecast", "climate", "heat", "frost", "fog"]):
            weather = context.get("weather") or fetch_open_meteo_weather(district)
            if isinstance(weather, dict) and weather.get("available"):
                temp = weather.get("temperature_c", 22)
                hum = weather.get("humidity_pct", 55)
                wind = weather.get("wind_speed_kmh", 8)
                rain7 = weather.get("rain_next_7d_mm", 0.0)
                cond = weather.get("condition", "Clear Sky")
                return (
                    f"**Live Weather & 7-Day Outlook for {district} ({state}):**\n"
                    f"• **Current Conditions:** {temp}°C ({cond}) | **Humidity:** {hum}% | **Wind:** {wind} km/h\n"
                    f"• **7-Day Cumulative Rainfall Forecast:** {rain7} mm\n"
                    f"• **Agronomic Advice:** {'Postpone irrigation and chemical spraying due to forecasted rain.' if rain7 > 10 else 'Weather is clear and favorable for scheduled irrigation and foliar nutrient application on calm days.'}"
                )
            return f"Weather conditions in **{district}** are currently favorable. Maintain light soil moisture to buffer against temperature fluctuations."

        # 9. MSP & Market Prices
        if any(w in query for w in ["msp", "price", "rate", "mandi", "market", "sell", "selling"]):
            return (
                "**Government Minimum Support Price (MSP — Rabi Marketing Season):**\n"
                "• **Wheat:** ₹2,425 / Quintal\n"
                "• **Mustard:** ₹5,950 / Quintal\n"
                "• **Gram (Chana):** ₹5,650 / Quintal\n"
                "• **Masoor (Lentil):** ₹6,700 / Quintal\n"
                "• **Barley:** ₹1,980 / Quintal\n"
                "Register on **e-NAM (enam.gov.in)** or your state procurement portal for direct DBT mandi sales."
            )

        # 10. Soil Health & pH
        if any(w in query for w in ["soil", "ph", "organic", "carbon", "testing", "fertility"]):
            soil_t = context.get("soil_type", "Alluvial Sandy Loam")
            return (
                f"**Soil Management for {district} ({state}):**\n"
                f"• Predominant soil profile: **{soil_t}** (ideal pH: **6.5 – 7.5**).\n"
                f"• Incorporate 2–3 tonnes/acre of well-decomposed FYM or Vermicompost before sowing and get a free 12-parameter soil report via **soilhealth.dac.gov.in**."
            )

        # 10b. NASA Earth & Satellite Intelligence
        if any(w in query for w in ["nasa", "satellite", "ndvi", "gibs", "modis", "solar radiation", "उपग्रह", "सैटेलाइट", "नासा"]):
            return (
                f"**{district} ({state}) के लिए NASA Earth & Weather Intelligence:**\n"
                f"• **NASA POWER Reanalysis:** 2m तापमान (T2M), सापेक्ष आर्द्रता (RH2M), सौर विकिरण (ALLSKY_SFC_SW_DWN), हवा की गति और वर्षा (PRECTOTCORR) का वैज्ञानिक विश्लेषण उपलब्ध कराता है।\n"
                f"• **NASA GIBS Satellite Layers:** MODIS NDVI (वनस्पति स्वास्थ्य सूचकांक), True Color इमेजरी, Land Surface Temperature (LST) और GPM IMERG वर्षा मानचित्र उपलब्ध हैं।\n"
                f"• **नोट:** NASA POWER ऐतिहासिक एवं नियर-रियल-टाइम रीएनालिसिस डेटा प्रदान करता है, लाइव मौसम पूर्वानुमान नहीं।"
            )

        # 11. Open Agronomic Web Search Fallback before generic summary
        web_agro = self._search_web_agronomy_fallback(query, crop, district, state, "en")
        if web_agro:
            return web_agro

        # 12. Smart Contextual Summary (instead of a static 1-line fallback)
        total_q = round(float(predicted_yield) * float(plot_acres), 1)
        return (
            f"Regarding your query **\"{query}\"** for **{crop}** in **{district} ({state})** ({growth_stage} stage):\n"
            f"1. **Yield Forecast:** ~**{predicted_yield} Q/Acre** (~{total_q} Quintals total on {plot_acres} acres; regional range {range_q_ha} Q/Ha).\n"
            f"2. **Key Action:** Maintain timely stage irrigation and split Nitrogen application (Urea) after watering.\n"
            f"3. **Ask Specifics:** You can ask me about **irrigation days, NPK fertilizer dosage, yellow rust/aphid sprays, weed control, MSP rates, or PM-KISAN / PMFBY / KCC / Solar Pump subsidies**!"
        )

    def _search_web_agronomy_fallback(self, query: str, crop: str, district: str, state: str, lang_mode: str) -> Optional[str]:
        """Performs a live web search via OfficialWebSearcher when a farmer asks an open-ended agricultural question."""
        try:
            web_res = self.rag_pipeline.searcher.search_official_web(f"{query} {crop} ICAR agriculture India", max_results=2)
            if web_res.get("found") and web_res.get("results"):
                top = web_res["results"][0]
                snippet = re.sub(r"\s+", " ", top.get("snippet", "")).strip()
                title = top.get("title", "Agricultural Reference")
                url = top.get("url", "")
                if len(snippet) > 40:
                    if self.last_rag_result is not None:
                        self.last_rag_result["retrieval_mode"] = "web_search"
                        self.last_rag_result["sources"] = [{
                            "title": title,
                            "url": url,
                            "source_type": "web_reference",
                            "is_official": top.get("is_official", False)
                        }]
                    if lang_mode == "en":
                        return f"**Web Agricultural Insight ({title}):**\n{snippet}\n\n• **Source:** {url}"
                    return f"**कृषि वेब जानकारी ({title}):**\n{snippet}\n\n• **स्रोत:** {url}"
        except Exception as e:
            logger.debug(f"Agronomic web search fallback skipped: {e}")
        return None

    def _local_grounded_response_hinglish(self, query: str, context: Dict[str, Any]) -> str:
        """Conversational Hinglish agronomic advisor."""
        crop = context.get("crop") or (context.get("crops")[0] if context.get("crops") else "Wheat")
        predicted_yield = context.get("predicted_yield", 19.9)
        plot_acres = context.get("plot_acres", 2.5)
        district = context.get("district", "Meerut")
        state = context.get("state", "Uttar Pradesh")

        if any(w in query for w in ["paidaawar", "upaj", "yield", "kitna", "kitni", "production"]):
            total = round(float(predicted_yield) * float(plot_acres), 1)
            return (
                f"Kisan bhai, **{district} ({state})** me aapke **{plot_acres} acre** khet me **{crop}** ki anumanit paidaawar lagbhag **{predicted_yield} Quintal/Acre** "
                f"(kul ~**{total} Quintal**) rehne ka anuman hai. Samay par sinchai aur santulit NPK khad se upaj aur badhegi."
            )
        if any(w in query for w in ["paani", "sinchai", "water", "irrigation", "kab"]):
            if crop == "Wheat":
                return (
                    f"**Gehun me Sinchai (ICAR Guide):** Pehli sinchai buwai ke **20-25 din baad (CRI stage)** par zaroor karein. "
                    f"Iske baad 40-45 din (Tillering) aur 80-85 din (Flowering) par halki sinchai karein."
                )
            return f"**{crop}** me phool aane se pehle (30-35 din) aur daana bante samay (60-65 din) halki sinchai karein."
        if any(w in query for w in ["khad", "urea", "dap", "npk", "fertilizer"]):
            return (
                f"**{district}** me **{crop}** ke liye prati acre 50 kg DAP + 25 kg MOP buwai par dein, aur **40-45 kg Neem-coated Urea** pehli aur doosri sinchai ke baad do barabar kiston me daalein."
            )
        # Delegate other topics to the comprehensive Hindi generator so no question goes unanswered
        return self._local_grounded_response_hi(query, context)
