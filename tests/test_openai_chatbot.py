"""Tests for KrishiSathi OpenAI LLM Chatbot Integration."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.krishisathi.voice_agent import KrishiSathiAgent
from src.api.main import app as fastapi_app
from src.api.flask_app import app as flask_app


class TestKrishiSathiOpenAIChatbot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.flask_client = flask_app.test_client()
        cls.sample_context = {
            "farmer_name": "Tanishka",
            "crop": "Wheat",
            "district": "Meerut",
            "plot_acres": 2.5,
            "growth_stage": "Tillering",
            "predicted_yield": 19.9,
            "expected_range_q_ha": "44 - 54",
            "irrigation_source": "Tube well / Borewell",
            "weather": {
                "available": True,
                "temperature_c": 25.0,
                "condition": "Sunny",
                "humidity_pct": 60,
                "precipitation_mm": 0.0
            }
        }

    def test_agent_initialization(self):
        """Agent should successfully initialize with OpenAI client when key is provided."""
        agent = KrishiSathiAgent(api_key="sk-mock-key-12345", model="gpt-4o-mini")
        self.assertIsNotNone(agent._openai_client)
        self.assertEqual(agent.model, "gpt-4o-mini")

    def test_openai_llm_successful_response(self):
        """When OpenAI API responds successfully, KrishiSathi should return the LLM content."""
        agent = KrishiSathiAgent(api_key="sk-mock-key-12345")

        mock_choice = MagicMock()
        mock_choice.message.content = "तनिष्का जी, गेहूं में कल्ले फूटते समय यूरिया की पहली खुराक दें और मिट्टी में नमी बनाए रखें।"
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        with patch.object(agent._openai_client.chat.completions, "create", return_value=mock_resp):
            answer = agent.ask("गेहूं में खाद कब डालें?", context=self.sample_context, lang="hi")
            self.assertEqual(answer, "तनिष्का जी, गेहूं में कल्ले फूटते समय यूरिया की पहली खुराक दें और मिट्टी में नमी बनाए रखें।")

    def test_openai_fallback_on_error(self):
        """When OpenAI encounters quota limits or errors, KrishiSathi must gracefully fall back to grounded expert rules."""
        agent = KrishiSathiAgent(api_key="sk-mock-key-12345")

        with patch.object(agent._openai_client.chat.completions, "create", side_effect=Exception("insufficient_quota")):
            answer_hi = agent.ask("गेहूं की पैदावार कितनी होगी?", context=self.sample_context, lang="hi")
            self.assertIn("अनुमानित पैदावार", answer_hi)
            self.assertIn("क्विंटल", answer_hi)

            answer_en = agent.ask("How much yield can I expect?", context=self.sample_context, lang="en")
            self.assertIn("estimated Wheat yield", answer_en)
            self.assertIn("Quintals", answer_en)

    def test_fastapi_chat_endpoint(self):
        """Verify POST /api/krishisathi/chat in FastAPI handles queries and returns 200 OK."""
        from src.api.main import krishisathi_chat, ChatQueryInput
        payload = ChatQueryInput(
            query="मेरी फसल में पानी कब लगाना है?",
            lang="hi",
            context=self.sample_context
        )
        res = krishisathi_chat(payload)
        self.assertEqual(res.get("status"), "success")
        self.assertTrue(len(res.get("answer", "")) > 10)
        self.assertIn("sources", res)

    def test_flask_chat_endpoint(self):
        """Verify POST /api/krishisathi/chat in Flask handles queries and returns 200 OK."""
        payload = {
            "query": "What fertilizer should I apply for Wheat?",
            "lang": "en",
            "context": self.sample_context
        }
        res = self.flask_client.post("/api/krishisathi/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(len(data.get("answer", "")) > 10)


if __name__ == "__main__":
    unittest.main()
