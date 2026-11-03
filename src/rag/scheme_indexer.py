"""Scheme PDF Indexer and Semantic Keyword Retriever for KrishiMitra AI.
Indexes official government scheme PDFs (PM-KISAN, PMFBY, KCC, PMKSY, Soil Health Card)
and evaluates retrieval sufficiency before deciding to fallback to web search.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Primary official scheme portals for accurate citation
SCHEME_PORTALS = {
    "pm_kisan": "https://pmkisan.gov.in",
    "pmfby": "https://pmfby.gov.in",
    "kcc": "https://www.myscheme.gov.in/schemes/kcc",
    "pmksy": "https://pmksy.gov.in",
    "soil_health_card": "https://soilhealth.dac.gov.in",
    "pm_kusum": "https://pmkusum.mnre.gov.in",
    "smam": "https://agrimachinery.nic.in",
    "pkvy": "https://pgsindia-ncof.gov.in",
    "enam": "https://www.enam.gov.in"
}

SCHEME_DISPLAY_NAMES = {
    "pm_kisan": "PM-KISAN Samman Nidhi (पीएम-किसान सम्मान निधि)",
    "pmfby": "Pradhan Mantri Fasal Bima Yojana (प्रधानमंत्री फसल बीमा योजना)",
    "kcc": "Kisan Credit Card Scheme (किसान क्रेडिट कार्ड योजना)",
    "pmksy": "Pradhan Mantri Krishi Sinchayee Yojana (पीएम कृषि सिंचाई योजना)",
    "soil_health_card": "Soil Health Card Scheme (मृदा स्वास्थ्य कार्ड योजना)",
    "pm_kusum": "PM-KUSUM Solar Agriculture Scheme (पीएम-कुसुम सोलर पंप योजना)",
    "smam": "Sub-Mission on Agricultural Mechanization (SMAM कृषि यंत्र अनुदान)",
    "pkvy": "Paramparagat Krishi Vikas Yojana (PKVY जैविक खेती योजना)",
    "enam": "National Agriculture Market (e-NAM एवं एमएसपी मंडी सुविधा)"
}

# Bilingual synonyms map for matching Hindi/English agricultural terms
SYNONYMS = {
    "pm_kisan": ["pm-kisan", "pm kisan", "pmkisan", "पीएम किसान", "किसान सम्मान निधि", "6000", "किस्त", "installment", "ekyc", "ईकेवाईसी"],
    "pmfby": ["pmfby", "fasal bima", "crop insurance", "फसल बीमा", "बीमा", "क्लेम", "claim", "premium", "प्रीमियम", "loss assessment", "bima"],
    "kcc": ["kcc", "kisan credit card", "किसान क्रेडिट कार्ड", "ऋण", "लोन", "loan", "interest subvention", "साहूकार", "क्रेडिट", "credit card"],
    "pmksy": ["pmksy", "krishi sinchayee", "micro irrigation", "सिंचाई योजना", "ड्रिप", "स्प्रिंकलर", "drip", "sprinkler", "जल संचयन", "per drop more crop"],
    "soil_health_card": ["soil health", "soil test", "मिट्टी जांच", "मृदा स्वास्थ्य", "मृदा परीक्षण", "shc", "rkvy", "सॉइल हेल्थ कार्ड", "soil card"],
    "pm_kusum": ["kusum", "pm-kusum", "pm kusum", "solar pump", "सोलर पंप", "सौर ऊर्जा", "ट्यूबवेल सोलर", "solarize", "mnre", "कुसुम"],
    "smam": ["smam", "machinery", "tractor", "rotavator", "happy seeder", "super seeder", "seed drill", "laser leveler", "कृषि यंत्र", "रोटावेटर", "सुपर सीडर", "हैप्पी सीडर", "मशीनरी", "यंत्र"],
    "pkvy": ["pkvy", "paramparagat", "organic", "jaivik", "जैविक खेती", "परम्परागत", "vermicompost", "केंचुआ खाद", "bio-fertilizer"],
    "enam": ["enam", "e-nam", "mandi", "msp", "minimum support price", "मंडी", "ई-नाम", "समर्थन मूल्य", "सरकारी खरीद", "apmc"]
}


class SchemePDFIndexer:
    """Extracts, indexes, caches, and retrieves chunks from official scheme PDFs."""

    def __init__(self, schemes_dir: Optional[Path] = None, cache_file: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.schemes_dir = schemes_dir or (base_dir / "data" / "rag" / "schemes")
        self.cache_file = cache_file or (base_dir / "data" / "rag" / "scheme_index.json")
        self.chunks: List[Dict[str, Any]] = []
        self._load_or_build_index()

    def _load_or_build_index(self):
        """Loads cached index if valid and fresh, otherwise builds from scheme PDFs."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    if self.chunks:
                        self._append_central_schemes_json()
                        logger.info(f"Loaded {len(self.chunks)} scheme chunks from cache: {self.cache_file.name}")
                        return
            except Exception as e:
                logger.warning(f"Failed loading cache {self.cache_file}: {e}. Rebuilding index...")

        self.rebuild_index()
        self._append_central_schemes_json()

    def _append_central_schemes_json(self):
        """Appends verified central schemes from data/schemes/central_schemes.json into the RAG index."""
        base_dir = Path(__file__).resolve().parent.parent.parent
        json_path = base_dir / "data" / "schemes" / "central_schemes.json"
        if not json_path.exists():
            return
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                schemes_data = json.load(f)
            existing_ids = {ch.get("id") for ch in self.chunks}
            key_map = {
                "pm-kisan": "pm_kisan",
                "pmfby": "pmfby",
                "soil-health-card": "soil_health_card",
                "pmksy-micro-irrigation": "pmksy",
                "kcc": "kcc",
                "pm-kusum": "pm_kusum",
                "smam-machinery": "smam",
                "pkvy-organic": "pkvy",
                "enam-market": "enam"
            }
            for sc in schemes_data:
                raw_id = sc.get("id", "")
                scheme_key = key_map.get(raw_id, raw_id.replace("-", "_"))
                chunk_id = f"central_json_{scheme_key}"
                if chunk_id in existing_ids:
                    continue
                elig = sc.get("eligibility", {})
                docs = ", ".join(sc.get("documents_required", []))
                combined_text = (
                    f"Scheme: {sc.get('name_en')} / {sc.get('name_hi')}. "
                    f"Category: {sc.get('category')}. "
                    f"Benefits (EN): {sc.get('benefit_en')} "
                    f"Benefits (HI): {sc.get('benefit_hi')} "
                    f"Eligibility (EN): {elig.get('criteria_en', '')} "
                    f"Eligibility (HI): {elig.get('criteria_hi', '')} "
                    f"Required Documents: {docs}. "
                    f"Official Portal: {sc.get('portal_url', 'https://myscheme.gov.in')}"
                )
                self.chunks.append({
                    "id": chunk_id,
                    "scheme_key": scheme_key,
                    "scheme_name": SCHEME_DISPLAY_NAMES.get(scheme_key, sc.get("name_en", scheme_key.upper())),
                    "file_name": "central_schemes.json (Verified Official Guidelines)",
                    "page": 1,
                    "text": combined_text,
                    "portal_url": sc.get("portal_url", SCHEME_PORTALS.get(scheme_key, "https://myscheme.gov.in")),
                    "is_official": True,
                    "source_type": "official_pdf"
                })
        except Exception as e:
            logger.warning(f"Could not append central_schemes.json to index: {e}")

    def rebuild_index(self):
        """Extracts text from all scheme PDFs and creates indexed passages."""
        import pdfplumber

        new_chunks = []
        if not self.schemes_dir.exists():
            logger.warning(f"Schemes directory not found: {self.schemes_dir}")
            self.chunks = []
            return

        for root, _, files in os.walk(self.schemes_dir):
            for file_name in files:
                file_path = Path(root) / file_name
                scheme_key = Path(root).name.lower()

                # Process PDF files
                if file_name.endswith(".pdf"):
                    try:
                        with pdfplumber.open(file_path) as pdf:
                            for page_idx, page in enumerate(pdf.pages):
                                text = page.extract_text()
                                if not text or len(text.strip()) < 50:
                                    continue
                                clean_text = self._clean_text(text)
                                # Break large pages into overlapping sub-chunks
                                sub_chunks = self._chunk_text(clean_text, chunk_size=350, overlap=50)
                                for c_idx, sub in enumerate(sub_chunks):
                                    new_chunks.append({
                                        "id": f"{scheme_key}_{file_name}_p{page_idx+1}_c{c_idx}",
                                        "scheme_key": scheme_key,
                                        "scheme_name": SCHEME_DISPLAY_NAMES.get(scheme_key, scheme_key.upper()),
                                        "file_name": file_name,
                                        "page": page_idx + 1,
                                        "text": sub,
                                        "portal_url": SCHEME_PORTALS.get(scheme_key, "https://myscheme.gov.in"),
                                        "is_official": True,
                                        "source_type": "official_pdf"
                                    })
                    except Exception as e:
                        logger.error(f"Error reading PDF {file_path}: {e}")

                # Process text documents (e.g. README notes)
                elif file_name.endswith(".txt"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as tf:
                            txt = tf.read().strip()
                            if txt and len(txt) > 30 and not "No PM-KUSUM document was included" in txt:
                                new_chunks.append({
                                    "id": f"{scheme_key}_{file_name}",
                                    "scheme_key": scheme_key,
                                    "scheme_name": SCHEME_DISPLAY_NAMES.get(scheme_key, scheme_key.upper()),
                                    "file_name": file_name,
                                    "page": 1,
                                    "text": txt,
                                    "portal_url": SCHEME_PORTALS.get(scheme_key, "https://myscheme.gov.in"),
                                    "is_official": True,
                                    "source_type": "official_doc"
                                })
                    except Exception as e:
                        logger.error(f"Error reading text {file_path}: {e}")

        self.chunks = new_chunks
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({"chunks": self.chunks, "total": len(self.chunks), "updated_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            logger.info(f"Indexed {len(self.chunks)} chunks saved to {self.cache_file}")
        except Exception as e:
            logger.warning(f"Could not write cache file: {e}")

    def search_schemes(self, query: str, top_k: int = 3, threshold: float = 3.0) -> Dict[str, Any]:
        """Searches indexed PDF chunks using keyword and synonym scoring.
        Returns retrieved chunks, confidence score, and sufficiency flag.
        """
        if not self.chunks:
            return {"is_sufficient": False, "score": 0.0, "chunks": [], "sources": []}

        query_clean = query.lower()
        # Tokenize query words
        tokens = [w for w in re.findall(r"[\w\u0900-\u097F]+", query_clean) if len(w) > 2]

        # Detect which scheme(s) are explicitly requested in query
        target_schemes = []
        for s_key, syns in SYNONYMS.items():
            if any(syn in query_clean for syn in syns):
                target_schemes.append(s_key)

        # Check if the query is explicitly asking about a government scheme or yojana
        is_scheme_query = any(w in query_clean for w in ["scheme", "schemes", "yojana", "योजना"])

        # If user explicitly asked for a scheme, but NO known scheme matched target_schemes:
        # e.g., "Moon Martian potato scheme" or "मंगल ग्रह खेती अनुदान योजना 2099"
        # It is either an unknown / fictitious scheme or an unindexed scheme.
        # Local scheme PDFs ONLY contain PM-KISAN, PMFBY, KCC, PMKSY, and Soil Health Card.
        # We must NOT treat local PDFs as sufficient!
        if is_scheme_query and not target_schemes:
            return {
                "is_sufficient": False,
                "best_score": 0.0,
                "chunks": [],
                "sources": [],
                "reason": "Unrecognized or unindexed scheme requested."
            }

        # If user explicitly asked for a scheme that is NOT indexed in local PDFs (e.g. PM-KUSUM),
        # immediately mark insufficient so the pipeline can fall back to official web search!
        if target_schemes:
            available_indexed_schemes = {ch["scheme_key"] for ch in self.chunks}
            has_any_target_indexed = any(ts in available_indexed_schemes for ts in target_schemes)
            if not has_any_target_indexed:
                return {
                    "is_sufficient": False,
                    "score": 0.0,
                    "chunks": [],
                    "sources": [],
                    "reason": f"Target scheme(s) {target_schemes} not present in local PDF index."
                }

        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

        for chunk in self.chunks:
            scheme_key = chunk["scheme_key"]

            # If user explicitly targeted a specific scheme, don't confuse with unrelated schemes
            if target_schemes and scheme_key not in target_schemes:
                continue

            text_lower = chunk["text"].lower()
            score = 0.0

            # 1. Scheme identity match
            scheme_synonyms = SYNONYMS.get(scheme_key, [])
            for syn in scheme_synonyms:
                if syn in query_clean:
                    score += 2.5
                    if syn in text_lower:
                        score += 2.0

            # 2. Token overlap scoring
            for token in tokens:
                if token in text_lower:
                    score += 1.0
                    # Boost exact phrase matches
                    if len(token) > 4:
                        score += 0.5

            # 3. Contextual intent words
            intent_keywords = [
                ("eligibility", 1.5), ("पात्रता", 2.0),
                ("benefit", 1.5), ("लाभ", 2.0),
                ("installment", 2.0), ("किस्त", 2.0),
                ("ekyc", 2.5), ("ईकेवाईसी", 2.5),
                ("premium", 2.0), ("प्रीमियम", 2.0),
                ("deadline", 2.0), ("अंतिम तिथि", 2.0),
                ("documents", 1.5), ("दस्तावेज", 1.5),
                ("interest", 1.5), ("ब्याज", 1.5)
            ]
            for kw, weight in intent_keywords:
                if kw in query_clean and kw in text_lower:
                    score += weight

            if score > 0.5:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_chunks[:top_k]

        best_score = top_matches[0][0] if top_matches else 0.0

        # Substantive content verification:
        # Common generic words that appear in virtually all government scheme documents
        generic_stopwords = {
            "scheme", "schemes", "yojana", "योजना", "government", "sarkar", "सरकार",
            "farmer", "farmers", "kisan", "किसान", "india", "bharat", "भारत",
            "apply", "application", "deadline", "date", "online", "portal", "subsidy", "अनुदान"
        }
        substantive_tokens = [t for t in tokens if t not in generic_stopwords]

        # A query is deemed sufficient only if:
        # 1. A recognized target scheme was identified and matched (e.g. pm_kisan, pmfby, kcc), OR
        # 2. If no scheme name was identified, substantive domain tokens must match with a high score (>= 4.5)
        has_substantive_match = False
        if top_matches:
            top_text = top_matches[0][1]["text"].lower()
            if target_schemes:
                has_substantive_match = True
            elif substantive_tokens and any(st in top_text for st in substantive_tokens):
                has_substantive_match = True

        is_sufficient = (best_score >= threshold) and has_substantive_match and (len(top_matches) > 0)

        # Build clean source citations
        sources = []
        seen_files = set()
        for _, ch in top_matches:
            file_key = f"{ch['scheme_name']} (Page {ch['page']})"
            if file_key not in seen_files:
                sources.append({
                    "title": f"{ch['scheme_name']} - {ch['file_name']} (Page {ch['page']})",
                    "url": ch["portal_url"],
                    "source_type": "official_pdf",
                    "is_official": True,
                    "access_date": datetime.now().strftime("%Y-%m-%d"),
                    "page": ch["page"]
                })
                seen_files.add(file_key)

        return {
            "is_sufficient": is_sufficient,
            "best_score": round(best_score, 2),
            "chunks": [ch for _, ch in top_matches],
            "sources": sources
        }

    def _clean_text(self, text: str) -> str:
        """Removes duplicate whitespace and artifacts from PDF text."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _chunk_text(self, text: str, chunk_size: int = 350, overlap: int = 50) -> List[str]:
        """Splits continuous text into overlapping word windows."""
        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(words), step):
            sub = " ".join(words[i:i + chunk_size])
            chunks.append(sub)
            if i + chunk_size >= len(words):
                break
        return chunks
