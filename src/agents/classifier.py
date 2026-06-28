"""
Waste Classifier Agent - Uses IBM Granite via watsonx.ai for waste classification
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reason: str
    disposal_instruction: str
    safety_note: str
    source: str = "granite"
    did_you_know: Optional[str] = None


class WasteClassifierAgent:
    """Classifies waste items using IBM Granite model"""
    
    CATEGORIES = [
        "Organic",
        "Recyclable (Plastic)",
        "Recyclable (Metal)", 
        "Recyclable (Glass)",
        "Recyclable (Paper/Cardboard)",
        "Hazardous",
        "E-waste",
        "Landfill/Reject"
    ]
    
    SYSTEM_PROMPT = """You are EcoSort AI, a waste classification assistant powered by IBM Granite.
Your task is to classify waste items into ONE of these categories:
1. Organic - food scraps, garden waste, greasy paper
2. Recyclable (Plastic) - clean plastic bottles, containers
3. Recyclable (Metal) - aluminum cans, metal tins
4. Recyclable (Glass) - glass bottles, jars
5. Recyclable (Paper/Cardboard) - clean paper, cardboard boxes
6. Hazardous - batteries, paint, chemicals, medicines, oil
7. E-waste - electronics, phones, laptops, cables
8. Landfill/Reject - mixed materials, ceramics, diapers, styrofoam

For each item, provide:
- Category (exact match from above)
- Confidence (0.0-1.0)
- Reason (1 sentence)
- Disposal instruction (1 sentence)
- Safety note (1 sentence or "None")
- Did you know? (1 interesting fact, optional)

Return ONLY valid JSON with these exact keys: category, confidence, reason, disposal_instruction, safety_note, did_you_know"""

    def __init__(self):
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize IBM Granite model via watsonx.ai"""
        if not WATSONX_AVAILABLE:
            print("[WARN] ibm-watsonx-ai not installed. Using rule-based fallback.")
            return
            
        api_key = os.getenv("WATSONX_API_KEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        
        if not api_key or not project_id:
            print("[WARN] Watsonx credentials not found. Using rule-based fallback.")
            return
        
        try:
            credentials = Credentials(url=url, api_key=api_key)
            self.model = ModelInference(
                model_id="ibm/granite-13b-instruct-v2",
                credentials=credentials,
                project_id=project_id,
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 300,
                    GenParams.TEMPERATURE: 0.1,
                    GenParams.TOP_P: 1.0
                }
            )
            print("[OK] IBM Granite model initialized successfully")
        except Exception as e:
            print(f"[WARN] Failed to initialize Granite: {e}. Using fallback.")
            self.model = None
    
    def _fallback_classify(self, item: str) -> ClassificationResult:
        """Rule-based classification when Granite is unavailable"""
        item_lower = item.lower()
        
        rules = {
            "organic": ["banana", "peel", "food", "vegetable", "fruit", "coffee", "tea", "garden", "leaf", "grass"],
            "recyclable (plastic)": ["plastic", "bottle", "container", "wrapper", "bag", "pouch"],
            "recyclable (metal)": ["aluminum", "can", "tin", "foil", "metal"],
            "recyclable (glass)": ["glass", "jar", "bottle"],
            "recyclable (paper/cardboard)": ["cardboard", "paper", "box", "newspaper", "magazine"],
            "hazardous": ["battery", "paint", "chemical", "medicine", "oil", "solvent", "acid"],
            "e-waste": ["phone", "laptop", "computer", "tablet", "charger", "cable", "electronic", "circuit"],
            "landfill/reject": ["diaper", "styrofoam", "ceramic", "mirror", "tissue", "sanitary"]
        }
        
        for category, keywords in rules.items():
            if any(kw in item_lower for kw in keywords):
                return self._get_result_for_category(category, item)
        
        return ClassificationResult(
            category="Landfill/Reject",
            confidence=0.3,
            reason="Unable to classify with confidence",
            disposal_instruction="Check local guidelines for mixed materials",
            safety_note="When in doubt, do not mix with recyclables",
            source="fallback"
        )
    
    def _get_result_for_category(self, category: str, item: str) -> ClassificationResult:
        """Get predefined result for a category"""
        results = {
            "organic": ClassificationResult(
                category="Organic",
                confidence=0.9,
                reason=f"{item} is biodegradable organic matter",
                disposal_instruction="Place in green/compost bin or home compost",
                safety_note="Remove any plastic packaging first",
                source="fallback",
                did_you_know="Composting 1kg food waste saves ~0.5kg CO2"
            ),
            "recyclable (plastic)": ClassificationResult(
                category="Recyclable (Plastic)",
                confidence=0.95,
                reason=f"{item} is made of recyclable plastic (PET/HDPE/PP)",
                disposal_instruction="Rinse clean and place in blue/recycling bin",
                safety_note="Remove caps and labels if different plastic type",
                source="fallback",
                did_you_know="Recycling 1 plastic bottle saves energy for 6hrs of 60W bulb"
            ),
            "recyclable (metal)": ClassificationResult(
                category="Recyclable (Metal)",
                confidence=0.98,
                reason=f"{item} is aluminum/metal - infinitely recyclable",
                disposal_instruction="Rinse and place in recycling bin",
                safety_note="None",
                source="fallback",
                did_you_know="Aluminum can -> new can in 60 days; saves 95% energy vs new"
            ),
            "recyclable (glass)": ClassificationResult(
                category="Recyclable (Glass)",
                confidence=0.98,
                reason=f"{item} is glass - 100% recyclable forever",
                disposal_instruction="Rinse and place in glass recycling bin",
                safety_note="Do not include broken glass - wrap safely",
                source="fallback",
                did_you_know="Glass takes 1 million years to decompose in landfill"
            ),
            "recyclable (paper/cardboard)": ClassificationResult(
                category="Recyclable (Paper/Cardboard)",
                confidence=0.9,
                reason=f"{item} is clean paper/cardboard fiber",
                disposal_instruction="Flatten boxes, keep dry, place in recycling",
                safety_note="Greasy/wet cardboard goes to organic waste",
                source="fallback",
                did_you_know="1 ton recycled paper saves 17 trees"
            ),
            "hazardous": ClassificationResult(
                category="Hazardous",
                confidence=0.99,
                reason=f"{item} contains toxic/hazardous substances",
                disposal_instruction="Take to hazardous waste collection center - NEVER regular bin",
                safety_note="Store in sealed container away from children/pets",
                source="fallback",
                did_you_know="1 liter oil contaminates 1 million liters water"
            ),
            "e-waste": ClassificationResult(
                category="E-waste",
                confidence=0.99,
                reason=f"{item} contains valuable metals & hazardous components",
                disposal_instruction="Drop at authorized e-waste recycler only",
                safety_note="Wipe personal data before disposal. Remove batteries if possible.",
                source="fallback",
                did_you_know="1 ton e-waste = more gold than 1 ton gold ore"
            ),
            "landfill/reject": ClassificationResult(
                category="Landfill/Reject",
                confidence=0.7,
                reason=f"{item} is mixed material or non-recyclable",
                disposal_instruction="Place in general waste/black bin",
                safety_note="Do not put in recycling - contaminates entire batch",
                source="fallback",
                did_you_know="Diapers take 500+ years to decompose"
            )
        }
        return results.get(category, ClassificationResult(
            category="Landfill/Reject",
            confidence=0.3,
            reason="Unknown item type",
            disposal_instruction="Check local municipal guidelines",
            safety_note="When unsure, keep out of recycling",
            source="fallback"
        ))
    
    def classify(self, item_description: str, image_data: Optional[str] = None) -> ClassificationResult:
        """
        Classify a waste item
        
        Args:
            item_description: Text description of the waste item
            image_data: Optional base64 encoded image (for future vision model support)
        
        Returns:
            ClassificationResult with category, confidence, and guidance
        """
        if self.model:
            return self._granite_classify(item_description, image_data)
        else:
            return self._fallback_classify(item_description)
    
    def _granite_classify(self, item: str, image_data: Optional[str] = None) -> ClassificationResult:
        """Use IBM Granite for classification"""
        try:
            prompt = f"{self.SYSTEM_PROMPT}\n\nItem: {item}\n\nJSON Response:"
            response = self.model.generate_text(prompt=prompt)
            
            # Parse JSON from response
            result = json.loads(response.strip())
            
            return ClassificationResult(
                category=result.get("category", "Landfill/Reject"),
                confidence=float(result.get("confidence", 0.5)),
                reason=result.get("reason", ""),
                disposal_instruction=result.get("disposal_instruction", ""),
                safety_note=result.get("safety_note", "None"),
                source="granite",
                did_you_know=result.get("did_you_know")
            )
        except Exception as e:
            print(f"Granite classification failed: {e}. Falling back.")
            return self._fallback_classify(item)