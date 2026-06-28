"""EcoSort AI - IBM Watsonx.ai Granite Model Client"""
import os
import logging
from typing import Optional, Dict, Any, List
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes

from src.config.settings import load_configs, WASTE_CATEGORIES, DISPOSAL_GUIDELINES

logger = logging.getLogger(__name__)

class GraniteClassifier:
    """Waste classification using IBM Granite model via watsonx.ai"""
    
    def __init__(self):
        self.watsonx_config, _, _ = load_configs()
        self.model: Optional[ModelInference] = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Granite model with watsonx.ai credentials"""
        try:
            credentials = Credentials(
                url=f"https://{self.watsonx_config.region}.ml.cloud.ibm.com",
                api_key=self.watsonx_config.api_key
            )
            
            params = {
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 300,
                GenParams.MIN_NEW_TOKENS: 10,
                GenParams.TEMPERATURE: 0.1,
                GenParams.TOP_K: 10,
                GenParams.TOP_P: 0.9,
                GenParams.REPETITION_PENALTY: 1.1,
                GenParams.STOP_SEQUENCES: ["\n\n", "---", "User:", "Assistant:"]
            }
            
            self.model = ModelInference(
                model_id=self.watsonx_config.model_id,
                credentials=credentials,
                params=params,
                project_id=self.watsonx_config.project_id
            )
            logger.info(f"Initialized Granite model: {self.watsonx_config.model_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Granite model: {e}")
            self.model = None
    
    def _build_classification_prompt(self, user_input: str) -> str:
        """Build the classification prompt for Granite"""
        categories_str = ", ".join(WASTE_CATEGORIES)
        
        prompt = f"""You are EcoSort AI, a waste classification assistant powered by IBM Granite.
Classify the waste item into ONE of these categories:
{categories_str}

User input: "{user_input}"

Respond ONLY with this format:
Category: [exact category name from list above]
Reason: [one sentence explaining why]
Disposal: [one sentence disposal instruction]
Safety: [one sentence safety note if applicable, else "None"]
Confidence: [0.0 to 1.0]

Example:
Category: Recyclable (Plastic)
Reason: PET plastic bottles are widely recyclable
Disposal: Rinse clean and place in recycling bin
Safety: Ensure bottle is empty before disposal
Confidence: 0.95

Now classify:"""
        return prompt
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Classify waste item using Granite model.
        Returns dict with category, reason, disposal, safety, confidence.
        """
        if not self.model:
            return self._fallback_classification(user_input)
        
        try:
            prompt = self._build_classification_prompt(user_input)
            response = self.model.generate_text(prompt=prompt)
            
            return self._parse_response(response, user_input)
            
        except Exception as e:
            logger.error(f"Granite classification failed: {e}")
            return self._fallback_classification(user_input)
    
    def _parse_response(self, response: str, user_input: str) -> Dict[str, Any]:
        """Parse Granite's response into structured data"""
        result = {
            "category": "Unclassified",
            "reason": "Failed to parse response",
            "disposal": "Check local guidelines",
            "safety": "None",
            "confidence": 0.0,
            "raw_response": response
        }
        
        try:
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith("Category:"):
                    result["category"] = line.replace("Category:", "").strip()
                elif line.startswith("Reason:"):
                    result["reason"] = line.replace("Reason:", "").strip()
                elif line.startswith("Disposal:"):
                    result["disposal"] = line.replace("Disposal:", "").strip()
                elif line.startswith("Safety:"):
                    result["safety"] = line.replace("Safety:", "").strip()
                elif line.startswith("Confidence:"):
                    conf_str = line.replace("Confidence:", "").strip()
                    result["confidence"] = float(conf_str)
            
            # Validate category
            if result["category"] not in WASTE_CATEGORIES:
                result["category"] = "Unclassified"
                result["confidence"] = 0.0
                
        except Exception as e:
            logger.error(f"Failed to parse Granite response: {e}")
        
        return result
    
    def _fallback_classification(self, user_input: str) -> Dict[str, Any]:
        """Rule-based fallback when Granite is unavailable"""
        user_lower = user_input.lower()
        
        # Keyword-based classification
        keyword_map = {
            "Organic": ["banana", "food", "peel", "vegetable", "fruit", "garden", "compost", "kitchen waste"],
            "Recyclable (Plastic)": ["plastic", "bottle", "container", "pet", "hdpe", "wrapper", "bag"],
            "Recyclable (Metal)": ["can", "aluminum", "tin", "foil", "metal"],
            "Recyclable (Glass)": ["glass", "jar", "bottle", "broken glass"],
            "Recyclable (Paper/Cardboard)": ["cardboard", "paper", "newspaper", "magazine", "box", "carton"],
            "E-waste": ["phone", "laptop", "computer", "tablet", "charger", "cable", "electronic", "circuit", "battery"],
            "Hazardous": ["battery", "paint", "chemical", "oil", "medicine", "medication", "pesticide", "cleaner"],
            "Landfill/Reject": ["diaper", "sanitary", "ceramic", "mirror", "styrofoam", "tissue"]
        }
        
        for category, keywords in keyword_map.items():
            if any(kw in user_lower for kw in keywords):
                return {
                    "category": category,
                    "reason": f"Matched keywords for {category}",
                    "disposal": DISPOSAL_GUIDELINES.get(category, "Follow local guidelines"),
                    "safety": "Verify with local waste authority",
                    "confidence": 0.75,
                    "fallback": True
                }
        
        return {
            "category": "Unclassified",
            "reason": "No matching keywords found",
            "disposal": "Check local waste guidelines",
            "safety": "None",
            "confidence": 0.0,
            "fallback": True
        }

    def classify_batch(self, items: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple items"""
        return [self.classify(item) for item in items]


class GraniteRAG:
    """RAG-powered disposal guidance using Granite"""
    
    def __init__(self):
        self.watsonx_config, _, _ = load_configs()
        self.model: Optional[ModelInference] = None
        self._initialize_model()
        
        # In-memory knowledge base (replace with vector DB in production)
        self.knowledge_base = {
            "cooking oil": "Never pour down drain. Cool, seal in container, drop at collection point. Many cities have biodiesel partners.",
            "pizza box": "Greasy parts -> organic/compost. Clean lid only -> recycle. Cut clean parts for recycling.",
            "battery": "Never in regular trash. Alkaline -> hazardous drop-off. Lithium-ion -> e-waste recycler (fire risk).",
            "medicine": "Never flush. Return to pharmacy take-back program. Use drug disposal boxes at police stations.",
            "e-waste": "Contains toxic materials (lead, mercury). ONLY authorized recyclers. Wipe data first.",
            "plastic codes": "Check triangle symbol: #1 PET, #2 HDPE widely recycled. #3-7 vary by municipality.",
            "composting": "Fruit/veg scraps, coffee grounds, eggshells -> compost. No meat, dairy, oils.",
            "hazardous waste": "Paint, chemicals, cleaners, pesticides -> hazardous waste facility. Check city collection days.",
            "recycling rules": "Clean, dry, empty. No plastic bags in recycling. Flatten cardboard. Lids off bottles.",
        }
    
    def _initialize_model(self):
        """Initialize Granite for RAG generation"""
        try:
            credentials = Credentials(
                url=f"https://{self.watsonx_config.region}.ml.cloud.ibm.com",
                api_key=self.watsonx_config.api_key
            )
            
            params = {
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 400,
                GenParams.TEMPERATURE: 0.2,
                GenParams.TOP_K: 20,
                GenParams.TOP_P: 0.9,
                GenParams.REPETITION_PENALTY: 1.1,
            }
            
            self.model = ModelInference(
                model_id=self.watsonx_config.model_id,
                credentials=credentials,
                params=params,
                project_id=self.watsonx_config.project_id
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG model: {e}")
            self.model = None
    
    def query(self, user_question: str) -> Dict[str, Any]:
        """Answer disposal question using RAG"""
        # Retrieve relevant knowledge
        retrieved = self._retrieve(user_question)
        
        if self.model and retrieved:
            return self._generate_with_granite(user_question, retrieved)
        else:
            return self._fallback_answer(user_question, retrieved)
    
    def _retrieve(self, query: str) -> List[str]:
        """Simple keyword-based retrieval"""
        query_lower = query.lower()
        results = []
        
        for topic, content in self.knowledge_base.items():
            if any(word in query_lower for word in topic.split()):
                results.append(f"Topic: {topic}\n{content}")
        
        # Return top 3 matches
        return results[:3]
    
    def _generate_with_granite(self, question: str, context: List[str]) -> Dict[str, Any]:
        """Generate answer using Granite with retrieved context"""
        context_str = "\n\n".join(context)
        
        prompt = f"""You are EcoSort AI, a waste management assistant. Use ONLY the following information to answer.

Context:
{context_str}

Question: {question}

Answer clearly and concisely. Include a practical tip if relevant.
If the context doesn't contain the answer, say so."""
        
        try:
            response = self.model.generate_text(prompt=prompt)
            return {
                "answer": response.strip(),
                "sources": context,
                "grounded": True,
                "model": "granite"
            }
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            return self._fallback_answer(question, context)
    
    def _fallback_answer(self, question: str, context: List[str]) -> Dict[str, Any]:
        """Fallback when Granite unavailable"""
        if context:
            answer = "Based on waste guidelines: " + " ".join([c.split('\n')[1] for c in context[:2]])
        else:
            answer = "I don't have specific information about that. Please check your local municipal waste guidelines."
        
        return {
            "answer": answer,
            "sources": context,
            "grounded": len(context) > 0,
            "model": "fallback"
        }