"""Unit tests for agronomic advisory rules and KrishiSathi voice generation."""

import unittest
from src.advisory.agronomic_rules import AgronomicAdvisor, PersonalisedAdvisoryEngine
from src.krishisathi.voice_agent import KrishiSathiAgent


class TestAdvisory(unittest.TestCase):
    def test_wheat_advisory_late_sown_heat_alert(self):
        farmer_input = {
            "crop": "Wheat",
            "sowing_window": "Late Sown (Nov 21 - Dec 15)",
            "irrigation_source": "Tube well / Borewell",
            "march_max_temp_c": 33.5,
            "nitrogen_kg_acre": 50.0,
            "plot_acres": 2.0,
        }
        yield_result = {"predicted_yield_per_acre": 16.2}

        advisory = AgronomicAdvisor.get_advisory(farmer_input, yield_result)

        self.assertGreater(len(advisory["alerts_en"]), 0)
        self.assertTrue(any("Heat Warning" in alert for alert in advisory["alerts_en"]))
        self.assertIn("नमस्ते किसान भाई", advisory["hindi_voice_script"])

    def test_krishisathi_voice_agent_hindi_response(self):
        agent = KrishiSathiAgent()
        context = {
            "crop": "Wheat",
            "plot_acres": 2.0,
            "district": "Meerut",
            "predicted_yield": 19.5,
            "alerts_hi": ["पछुआ गर्मी से बचाव के लिए पोटेशियम नाइट्रेट का छिड़काव करें।"],
            "advisories_hi": ["पहली सिंचाई 21 दिन पर दें।"],
            "eligible_schemes": [{"name_hi": "प्रधानमंत्री फसल बीमा योजना"}],
        }

        ans_yield = agent.ask("मेरी पैदावार कितनी होगी?", context)
        self.assertTrue("19.5" in ans_yield or "पैदावार" in ans_yield)

        ans_water = agent.ask("सिंचाई कब करनी है?", context)
        self.assertTrue("सिंचाई" in ans_water or "पानी" in ans_water)

    def test_structured_cards_required_fields(self):
        farmer_input = {
            "crop": "Wheat",
            "district": "Meerut",
            "state": "Uttar Pradesh",
            "season": "Rabi",
            "growth_stage": "Crown Root Initiation (CRI)",
            "irrigation_source": "Tube well / Borewell",
            "soil_type": "Alluvial (Sandy Loam)",
            "march_max_temp_c": 32.0,
            "nitrogen_kg_acre": 48.0,
            "phosphorus_kg_acre": 22.0,
            "potassium_kg_acre": 15.0,
        }
        res = PersonalisedAdvisoryEngine.generate_advisory(farmer_input)
        self.assertEqual(res["status"], "success")
        self.assertIn("structured_cards", res)
        cards = res["structured_cards"]
        self.assertGreaterEqual(len(cards), 3)

        for card in cards:
            self.assertIn("observation", card)
            self.assertIn("recommendation", card)
            self.assertIn("reason", card)
            self.assertIn("priority", card)
            self.assertIn(card["priority"], ["urgent", "moderate", "informational"])
            self.assertIn("source", card)
            self.assertIn("source_url", card)

    def test_soil_guidance_non_overclaiming(self):
        """Ensure soil guidance clearly states district average is not farm-specific test."""
        farmer_input = {
            "crop": "Wheat",
            "district": "Meerut",
            "soil_type": "Alluvial (Sandy Loam)",
        }
        res = PersonalisedAdvisoryEngine.generate_advisory(farmer_input)
        soil_cards = [c for c in res["structured_cards"] if "soil" in c["id"]]
        self.assertGreater(len(soil_cards), 0)
        card = soil_cards[0]
        self.assertIn("not certified farm-specific", card["observation"])
        self.assertIn("Soil Health Card", card["recommendation"])

    def test_pest_disease_evidence_based_symptom_workflow(self):
        """Ensure pest/disease handling requests confirmation and does not claim definitive diagnosis."""
        farmer_input = {
            "crop": "Wheat",
            "district": "Meerut",
            "reported_symptoms": ["yellow powder on leaves", "stripes"],
        }
        res = PersonalisedAdvisoryEngine.generate_advisory(farmer_input)
        rust_cards = [c for c in res["structured_cards"] if "rust" in c["id"]]
        self.assertGreater(len(rust_cards), 0)
        card = rust_cards[0]
        self.assertEqual(card["priority"], "urgent")
        self.assertIn("not a certified lab diagnosis", card["observation"])
        self.assertIn("Perform physical wipe test", card["recommendation"])
        self.assertIn("ICAR - Indian Institute of Wheat and Barley Research", card["source"])

    def test_mustard_stage_advisory(self):
        farmer_input = {
            "crop": "Mustard",
            "district": "Meerut",
            "growth_stage": "Flowering",
            "reported_symptoms": ["small aphids on flowers"],
        }
        res = PersonalisedAdvisoryEngine.generate_advisory(farmer_input)
        cards = res["structured_cards"]
        aphid_cards = [c for c in cards if "aphid" in c["id"]]
        self.assertGreater(len(aphid_cards), 0)
        self.assertIn("Economic Threshold Level", aphid_cards[0]["recommendation"])


if __name__ == "__main__":
    unittest.main()
