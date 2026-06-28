"""
RAG Agent - Retrieves disposal guidelines using vector search over knowledge base
"""
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


@dataclass
class RAGResult:
    answer: str
    sources: List[str]
    confidence: float
    category: str


class RAGAgent:
    """Retrieval-Augmented Generation for waste disposal guidelines"""
    
    # Embedded knowledge base (in production, use vector DB)
    KNOWLEDGE_BASE = {
        "Organic": [
            "Organic waste includes food scraps, fruit/vegetable peels, coffee grounds, tea bags, garden waste",
            "Compost organic waste at home or use municipal green bin collection",
            "Do not include meat, dairy, or oily foods in home compost - attracts pests",
            "CPCB Guidelines: Wet waste must be segregated at source in green bins"
        ],
        "Recyclable (Plastic)": [
            "Clean plastic bottles (PET #1, HDPE #2) are widely recyclable",
            "Rinse containers thoroughly - food residue contaminates recycling batches",
            "Remove caps and labels - they may be different plastic types",
            "Plastic bags/film require separate drop-off at store collection points",
            "CPCB Plastic Waste Management Rules 2016: Producers responsible for collection"
        ],
        "Recyclable (Metal)": [
            "Aluminum cans, steel/tin cans, clean foil are 100% recyclable",
            "Rinse cans - no need to remove labels",
            "Aluminum recycling saves 95% energy vs primary production",
            "Scrap metal dealers accept larger metal items"
        ],
        "Recyclable (Glass)": [
            "Glass bottles and jars are infinitely recyclable without quality loss",
            "Rinse and remove caps/lids (metal lids recycle separately)",
            "Do NOT include: ceramics, mirrors, window glass, light bulbs",
            "Colors can be mixed in most municipal programs"
        ],
        "Recyclable (Paper/Cardboard)": [
            "Clean, dry paper and cardboard only - flatten boxes",
            "NO pizza boxes with grease, used tissues, paper towels, waxed paper",
            "Shredded paper: bag separately or compost",
            "1 ton recycled paper saves 17 trees, 7000 gallons water, 4100 kWh energy"
        ],
        "Hazardous": [
            "Batteries: All types (alkaline, lithium, button) -> hazardous waste center",
            "Paint, solvents, chemicals -> hazardous waste facility only",
            "Expired medicines -> pharmacy take-back programs or hazardous waste",
            "Used motor oil/cooking oil -> designated collection points",
            "CPCB: Hazardous waste must not mix with municipal waste"
        ],
        "E-waste": [
            "Phones, laptops, tablets, chargers, cables -> authorized e-waste recycler ONLY",
            "E-Waste Management Rules 2022: Producers must set up collection centers",
            "Wipe personal data before disposal - factory reset devices",
            "Remove batteries if possible - recycle separately",
            "E-waste contains gold, silver, copper, palladium - valuable recovery"
        ],
        "Landfill/Reject": [
            "Sanitary pads, diapers, ceramics, broken glass (wrapped), styrofoam",
            "Mixed materials that cannot be separated",
            "Minimize this category - explore reuse/repair first",
            "CPCB: Landfill only for non-recyclable, non-compostable, non-hazardous waste"
        ]
    }
    
    RAG_PROMPT = """You are EcoSort AI's knowledge agent. Answer the user's question using ONLY the provided context.
If the context doesn't contain the answer, say: "I don't have specific information about that in my knowledge base."

Context:
{context}

User Question: {question}

Answer clearly and concisely. Include a practical tip if relevant."""

    def __init__(self):
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize IBM Granite for RAG generation"""
        if not WATSONX_AVAILABLE:
            return
            
        api_key = os.getenv("WATSONX_API_KEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        
        if not api_key or not project_id:
            return
        
        try:
            credentials = Credentials(url=url, api_key=api_key)
            self.model = ModelInference(
                model_id="ibm/granite-13b-instruct-v2",
                credentials=credentials,
                project_id=project_id,
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 250,
                    GenParams.TEMPERATURE: 0.2,
                    GenParams.TOP_P: 1.0
                }
            )
        except Exception:
            self.model = None
    
    def _retrieve_context(self, category: str, question: str) -> List[str]:
        """Retrieve relevant chunks from knowledge base"""
        # Simple keyword-based retrieval (in production: vector similarity search)
        base_chunks = self.KNOWLEDGE_BASE.get(category, [])
        general_chunks = self.KNOWLEDGE_BASE.get("General", [])
        
        # Add category-specific chunks
        all_chunks = base_chunks + general_chunks
        
        # Simple relevance scoring
        question_lower = question.lower()
        scored = []
        for chunk in all_chunks:
            score = sum(1 for word in question_lower.split() if word in chunk.lower())
            if score > 0:
                scored.append((score, chunk))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [c for _, c in scored[:3]]  # Top 3 relevant chunks
    
    def query(self, category: str, question: str) -> RAGResult:
        """Answer a disposal question using RAG"""
        context_chunks = self._retrieve_context(category, question)
        context = "\n".join(f"- {c}" for c in context_chunks)
        
        if self.model and context_chunks:
            return self._granite_generate(category, question, context, context_chunks)
        else:
            return self._fallback_answer(category, question, context_chunks)
    
    def _granite_generate(self, category: str, question: str, context: str, sources: List[str]) -> RAGResult:
        """Generate answer using Granite"""
        try:
            prompt = self.RAG_PROMPT.format(context=context, question=question)
            answer = self.model.generate_text(prompt=prompt)
            
            return RAGResult(
                answer=answer.strip(),
                sources=sources,
                confidence=0.85,
                category=category
            )
        except Exception:
            return self._fallback_answer(category, question, sources)
    
    def _fallback_answer(self, category: str, question: str, sources: List[str]) -> RAGResult:
        """Rule-based answer when Granite unavailable"""
        q_lower = question.lower()
        
        fallback_answers = {
            "Organic": {
                "compost": "Yes, compost fruit/veg scraps, coffee grounds, garden waste. Avoid meat/dairy/oils.",
                "green bin": "Use municipal green bin for wet waste collection. Check your city schedule.",
                "default": "Compost at home or use green bin. Do not mix with recyclables."
            },
            "Recyclable (Plastic)": {
                "rinse": "Always rinse containers - food residue ruins entire recycling batches.",
                "cap": "Remove caps - they're often different plastic. Check local rules for caps.",
                "bag": "Plastic bags need store drop-off. Don't put in curbside bin.",
                "default": "Rinse clean, remove caps/labels, recycle in blue bin. Bags -> store drop-off."
            },
            "Recyclable (Metal)": {
                "rinse": "Quick rinse is enough. Labels can stay on.",
                "foil": "Clean foil balls (tennis ball size) recycle. Dirty foil -> trash.",
                "default": "Rinse cans, recycle. Scrap metal -> dealer."
            },
            "Recyclable (Glass)": {
                "broken": "Broken glass: wrap in paper, label 'broken', put in trash. NOT recycling.",
                "jar": "Rinse jars, remove metal lids (recycle separately), recycle glass.",
                "default": "Rinse bottles/jars, recycle. No ceramics/mirrors/bulbs."
            },
            "Recyclable (Paper/Cardboard)": {
                "pizza": "Greasy parts -> organic/compost. Clean lid only -> recycle.",
                "shred": "Shredded paper: bag in paper bag or compost.",
                "wet": "Wet paper -> compost or trash. Keep recycling dry.",
                "default": "Clean & dry only. Flatten boxes. No tissues/paper towels."
            },
            "Hazardous": {
                "battery": "ALL batteries -> hazardous waste center. Many stores have drop-off bins.",
                "medicine": "Pharmacy take-back or hazardous waste. NEVER flush.",
                "paint": "Dry latex paint -> trash. Oil paint/solvents -> hazardous center.",
                "oil": "Used oil -> auto shop or collection center. 1L contaminates 1M L water.",
                "default": "Take to hazardous waste facility. Never regular trash/drain."
            },
            "E-waste": {
                "phone": "Factory reset, remove SIM/SD, authorized e-waste recycler only.",
                "laptop": "Wipe hard drive (DBAN or similar), authorized recycler. Some offer pickup.",
                "data": "Always wipe data. Remove batteries if possible.",
                "default": "Authorized e-waste recycler ONLY. Check E-Waste Rules 2022 collection centers."
            },
            "Landfill/Reject": {
                "default": "Last resort. Minimize by repairing, donating, or finding specialized recycling."
            }
        }
        
        cat_fallbacks = fallback_answers.get(category, fallback_answers["Landfill/Reject"])
        answer = cat_fallbacks.get("default", cat_fallbacks.get("default", ""))
        
        # Try keyword matching
        for keyword, specific in cat_fallbacks.items():
            if keyword != "default" and keyword in q_lower:
                answer = specific
                break
        
        return RAGResult(
            answer=answer,
            sources=sources,
            confidence=0.7,
            category=category
        )