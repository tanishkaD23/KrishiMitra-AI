"""Government scheme eligibility evaluator for smallholder farmers."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import SCHEMES_DATA_DIR


class SchemeEligibilityEngine:
    """Evaluates farmer profile against central and state agricultural schemes."""

    def __init__(self, schemes_file: Optional[Path] = None):
        self.schemes_file = schemes_file or (SCHEMES_DATA_DIR / "central_schemes.json")
        self._schemes: List[Dict[str, Any]] = []
        self._load_schemes()

    def _load_schemes(self):
        if self.schemes_file.exists():
            with open(self.schemes_file, "r", encoding="utf-8") as f:
                self._schemes = json.load(f)

    @staticmethod
    def classify_farmer_category(acres: float) -> str:
        """Classifies landholding based on Indian Agriculture Census guidelines:

        Marginal: < 1.0 ha (~2.47 acres)
        Small: 1.0 - 2.0 ha (2.47 - 4.94 acres)
        Medium: 2.0 - 4.0 ha
        Large: > 4.0 ha
        """
        if acres <= 2.47:
            return "Marginal"
        elif acres <= 4.94:
            return "Small"
        elif acres <= 9.88:
            return "Medium"
        else:
            return "Large"

    def evaluate_eligibility(self, farmer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Matches farmer profile with available schemes and returns eligible schemes

        with personalized reasons and application documents.
        """
        acres = float(farmer_profile.get("plot_acres", 1.0))
        farmer_category = self.classify_farmer_category(acres)
        crop = farmer_profile.get("crop", "Wheat")
        state = farmer_profile.get("state", "Uttar Pradesh")
        irrigation = farmer_profile.get("irrigation_source", "Tube well / Borewell")

        eligible_schemes = []

        for scheme in self._schemes:
            elig = scheme.get("eligibility", {})
            is_eligible = True
            eligibility_reasons = []

            # 1. State check
            allowed_states = elig.get("states", ["All"])
            if "All" not in allowed_states and state not in allowed_states:
                is_eligible = False

            # 2. Land range check
            min_land = elig.get("min_land_acres")
            max_land = elig.get("max_land_acres")
            if min_land is not None and acres < min_land:
                is_eligible = False
            if max_land is not None and acres > max_land:
                is_eligible = False

            # 3. Farmer category check
            allowed_categories = elig.get("farmer_categories", [])
            if allowed_categories and farmer_category not in allowed_categories:
                is_eligible = False

            # 4. Crop specific check
            allowed_crops = elig.get("crops")
            if allowed_crops and crop not in allowed_crops:
                is_eligible = False

            # 5. Irrigation requirement check
            irrigation_req = elig.get("irrigation_need")
            if irrigation_req and irrigation not in irrigation_req:
                is_eligible = False

            if is_eligible:
                eligibility_reasons.append(
                    f"Farmer category is '{farmer_category}' with {acres} acres of cultivable land."
                )
                if allowed_crops and crop in allowed_crops:
                    eligibility_reasons.append(f"Notified crop '{crop}' is actively supported under this scheme.")

                eligible_schemes.append(
                    {
                        "id": scheme["id"],
                        "name_en": scheme["name_en"],
                        "name_hi": scheme["name_hi"],
                        "category": scheme["category"],
                        "benefit_en": scheme["benefit_en"],
                        "benefit_hi": scheme["benefit_hi"],
                        "farmer_category": farmer_category,
                        "eligibility_reasons": eligibility_reasons,
                        "documents_required": scheme.get("documents_required", []),
                        "portal_url": scheme.get("portal_url", ""),
                    }
                )

        return eligible_schemes
