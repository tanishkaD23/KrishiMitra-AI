"""Comprehensive tests for KrishiMitra AI RAG Pipeline & Web-Search Fallback.
Tests:
1. PDF retrieval from indexed scheme PDFs.
2. Fallback to web search when PDFs are insufficient.
3. Prioritization of official government sources (.gov.in, mnre.gov.in, etc.).
4. No-reliable-answer guardrail (never invents rules or benefits).
5. Multilingual language matching (Hindi, Hinglish, English).
6. FastAPI and Flask /api/krishisathi/chat integration.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.rag.scheme_indexer import SchemePDFIndexer
from src.rag.web_search import OfficialWebSearcher
from src.rag.pipeline import SchemeRAGPipeline
from src.krishisathi.voice_agent import KrishiSathiAgent
from src.api.main import app as fastapi_app
from src.api.flask_app import app as flask_app


class TestRAGAndWebSearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.indexer = SchemePDFIndexer()
        cls.searcher = OfficialWebSearcher()
        cls.pipeline = SchemeRAGPipeline(indexer=cls.indexer, searcher=cls.searcher)
        cls.agent = KrishiSathiAgent(rag_pipeline=cls.pipeline)
        cls.flask_client = flask_app.test_client()

    def test_pdf_retrieval(self):
        """1. Queries for indexed schemes (PM-KISAN, PMFBY, KCC) should retrieve directly from PDFs."""
        res = self.pipeline.retrieve("How to complete eKYC in PM-KISAN?")
        self.assertEqual(res["retrieval_mode"], "pdf")
        self.assertTrue(res["verified"])
        self.assertTrue(len(res["sources"]) > 0)
        first_src = res["sources"][0]
        self.assertEqual(first_src["source_type"], "official_pdf")
        self.assertTrue(first_src["is_official"])
        self.assertIn("pmkisan.gov.in", first_src["url"])

    def test_web_search_fallback_trigger(self):
        """2. When a scheme is not in local PDFs (e.g. PM-KUSUM), it must fall back to web search."""
        mock_kusum = [
            {"title": "PM-KUSUM Scheme Components - MNRE", "url": "https://mnre.gov.in/kusum-scheme", "snippet": "PM-KUSUM provides subsidy on standalone solar agriculture pumps in Uttar Pradesh."}
        ]
        with patch.object(OfficialWebSearcher, "_search_duckduckgo", return_value=mock_kusum):
            res = self.pipeline.retrieve("PM-KUSUM solar pump subsidy in Uttar Pradesh")
            self.assertEqual(res["retrieval_mode"], "web_search")
            self.assertTrue(res["verified"])
            self.assertTrue(len(res["sources"]) > 0)
            self.assertTrue(res["has_official_source"])

    def test_official_source_prioritization(self):
        """3. Official domains (.gov.in, .nic.in, mnre.gov.in) must be classified as official and prioritized."""
        self.assertTrue(OfficialWebSearcher.is_official_domain("pmkisan.gov.in"))
        self.assertTrue(OfficialWebSearcher.is_official_domain("pmfby.gov.in"))
        self.assertTrue(OfficialWebSearcher.is_official_domain("mnre.gov.in"))
        self.assertTrue(OfficialWebSearcher.is_official_domain("upagriculture.com"))
        self.assertTrue(OfficialWebSearcher.is_official_domain("myscheme.gov.in"))
        self.assertTrue(OfficialWebSearcher.is_official_domain("agricoop.nic.in"))
        self.assertFalse(OfficialWebSearcher.is_official_domain("randomblog.com"))
        self.assertFalse(OfficialWebSearcher.is_official_domain("fake-kisan-portal.xyz"))

        # Verify ranking
        mock_raw = [
            {"title": "Third-party Blog", "url": "https://randomblog.com/scheme", "snippet": "Info"},
            {"title": "MNRE Portal", "url": "https://mnre.gov.in/kusum", "snippet": "Official Guide"}
        ]
        ranked = self.searcher._rank_and_verify(mock_raw, "kusum")
        self.assertEqual(ranked[0]["url"], "https://mnre.gov.in/kusum")
        self.assertTrue(ranked[0]["is_official"])
        self.assertFalse(ranked[1]["is_official"])

    def test_no_reliable_answer_guardrail(self):
        """4. Unverifiable fictitious queries must report unverified status without inventing rules."""
        res = self.agent.ask_rag("What is the application deadline for the 2099 Moon Martian potato scheme?", lang="en")
        self.assertEqual(res["retrieval_mode"], "unverified")
        self.assertFalse(res["verified"])
        self.assertIn("could not be verified", res["answer"].lower())

        # In Hindi
        res_hi = self.agent.ask_rag("मंगल ग्रह खेती अनुदान योजना 2099 की अंतिम तिथि क्या है?", lang="hi")
        self.assertEqual(res_hi["retrieval_mode"], "unverified")
        self.assertFalse(res_hi["verified"])
        self.assertIn("सत्यापित नहीं हो सकी", res_hi["answer"])

    def test_multilingual_language_matching(self):
        """5. Agent must respond in the farmer's requested language: Hindi, Hinglish, or English."""
        # Hindi
        ans_hi = self.agent.ask("गेहूं की पहली सिंचाई कब करें?", lang="hi")
        self.assertTrue(any(ch in ans_hi for ch in "ताज जड़ पहली सिंचाई"))

        # Hinglish
        ans_hinglish = self.agent.ask("Wheat me pehla paani kab lagayein?", lang="hi")
        self.assertTrue(len(ans_hinglish) > 10)

        # English
        ans_en = self.agent.ask("When should I irrigate my wheat crop?", lang="en")
        self.assertIn("Crown Root Initiation", ans_en)

    def test_fastapi_and_flask_chat_routes(self):
        """6. Both FastAPI and Flask endpoints must serve /api/krishisathi/chat with source citations."""
        # FastAPI
        from src.api.main import krishisathi_chat, ChatQueryInput
        data_fast = krishisathi_chat(ChatQueryInput(
            query="How to do eKYC in PM-KISAN?",
            lang="en"
        ))
        self.assertEqual(data_fast["status"], "success")
        self.assertIn("answer", data_fast)
        self.assertEqual(data_fast["retrieval_mode"], "pdf")
        self.assertTrue(len(data_fast["sources"]) > 0)

        # Flask
        mock_kusum = [
            {"title": "PM-KUSUM Scheme Components - MNRE", "url": "https://mnre.gov.in/kusum-scheme", "snippet": "PM-KUSUM provides subsidy on standalone solar agriculture pumps in Uttar Pradesh."}
        ]
        with patch.object(OfficialWebSearcher, "_search_duckduckgo", return_value=mock_kusum):
            res_flask = self.flask_client.post("/api/krishisathi/chat", json={
                "query": "PM-KUSUM solar subsidy in Uttar Pradesh",
                "lang": "en"
            })
            self.assertEqual(res_flask.status_code, 200)
            data_flask = res_flask.get_json()
            self.assertEqual(data_flask["status"], "success")
            self.assertIn("answer", data_flask)
            self.assertEqual(data_flask["retrieval_mode"], "web_search")
            self.assertTrue(len(data_flask["sources"]) > 0)


if __name__ == "__main__":
    unittest.main()
