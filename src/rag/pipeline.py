"""Unified Scheme RAG Pipeline with Fallback Web-Search Engine.
Orchestrates PDF retrieval -> Web search fallback -> Verification & Grounding.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.rag.scheme_indexer import SchemePDFIndexer
from src.rag.web_search import OfficialWebSearcher

logger = logging.getLogger(__name__)


class SchemeRAGPipeline:
    """End-to-end RAG orchestrator for KrishiMitra AI:
    1. Searches indexed official scheme PDFs.
    2. If insufficient, falls back to targeted web search prioritizing official government portals.
    3. If neither provides reliable evidence, reports unverified status rather than fabricating answers.
    """

    def __init__(self, indexer: Optional[SchemePDFIndexer] = None, searcher: Optional[OfficialWebSearcher] = None):
        self.indexer = indexer or SchemePDFIndexer()
        self.searcher = searcher or OfficialWebSearcher()

    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Runs multi-stage retrieval: PDF First -> Web Search Fallback -> Verification."""
        query_clean = query.strip()
        access_date = datetime.now().strftime("%Y-%m-%d")

        # ---------------------------------------------------------
        # Step 1: Search Indexed Scheme PDFs
        # ---------------------------------------------------------
        pdf_res = self.indexer.search_schemes(query_clean, top_k=3, threshold=3.0)

        if pdf_res.get("is_sufficient"):
            context_text = "\n\n".join([f"[{ch['scheme_name']} - Page {ch['page']}]:\n{ch['text']}" for ch in pdf_res["chunks"]])
            return {
                "retrieval_mode": "pdf",
                "verified": True,
                "context_text": context_text,
                "sources": pdf_res["sources"],
                "has_official_source": True,
                "access_date": access_date,
                "message": "Information verified from official government scheme guidelines on record."
            }

        # ---------------------------------------------------------
        # Step 2: Fallback to Official Web Search
        # ---------------------------------------------------------
        logger.info(f"PDF context insufficient for '{query_clean[:60]}'. Falling back to official web search...")
        web_res = self.searcher.search_official_web(query_clean, max_results=4)

        # For government schemes, benefits, and rules, we require at least one verified official source (.gov.in, mnre.gov.in, upagriculture, etc.)
        if web_res.get("found") and web_res.get("has_official_source"):
            snippets = []
            sources = []
            for item in web_res["results"]:
                snippets.append(f"Source: {item['title']} ({item['url']})\nSnippet: {item['snippet']}")
                sources.append({
                    "title": item["title"],
                    "url": item["url"],
                    "source_type": item["source_type"],
                    "is_official": item["is_official"],
                    "access_date": access_date
                })

            context_text = "\n\n".join(snippets)
            return {
                "retrieval_mode": "web_search",
                "verified": True,
                "context_text": context_text,
                "sources": sources,
                "has_official_source": True,
                "access_date": access_date,
                "message": "Information retrieved from live official/government web sources."
            }

        # ---------------------------------------------------------
        # Step 3: No Reliable Evidence Found
        # ---------------------------------------------------------
        return {
            "retrieval_mode": "unverified",
            "verified": False,
            "context_text": "",
            "sources": [],
            "has_official_source": False,
            "access_date": access_date,
            "message": "Reliable official information could not be verified from government records or portals."
        }
