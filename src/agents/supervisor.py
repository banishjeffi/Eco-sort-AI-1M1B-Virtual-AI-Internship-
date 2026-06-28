"""
Supervisor Agent - Orchestrates all agents for end-to-end waste assistance
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import json

from .classifier import WasteClassifierAgent, ClassificationResult
from .rag_agent import RAGAgent, RAGResult
from .location_impact import LocationAgent, ImpactTrackerAgent, RecyclingCenter, ImpactMetrics
from src.utils.cos_client import COSClient, UploadResult


@dataclass
class EcoSortResponse:
    """Complete response from EcoSort AI"""
    status: str
    classification: Optional[Dict[str, Any]] = None
    guidelines: Optional[Dict[str, Any]] = None
    facilities: Optional[List[Dict[str, Any]]] = None
    impact: Optional[Dict[str, Any]] = None
    image_upload: Optional[Dict[str, Any]] = None
    user_friendly: str = ""


class EcoSortSupervisor:
    """Main orchestrator - coordinates all agents"""
    
    def __init__(self, user_lat: float = 28.6139, user_lon: float = 77.2090):
        self.classifier = WasteClassifierAgent()
        self.rag = RAGAgent()
        self.location = LocationAgent(user_lat, user_lon)
        self.impact = ImpactTrackerAgent()
        self.cos = None
        self._init_cos()
    
    def _init_cos(self):
        """Initialize COS client if credentials available"""
        try:
            from src.utils.cos_client import create_cos_client_from_env
            self.cos = create_cos_client_from_env()
        except Exception:
            self.cos = None
    
    def process_request(
        self, 
        user_input: str, 
        user_location: Optional[tuple] = None,
        image_path: Optional[str] = None,
        weight_kg: float = 1.0
    ) -> EcoSortResponse:
        """
        Process a user request through the full agent pipeline
        
        Args:
            user_input: Text description of waste item
            user_location: Optional (lat, lon) tuple
            image_path: Optional path to waste image for upload
            weight_kg: Estimated weight for impact calculation
        
        Returns:
            Complete EcoSortResponse with all agent outputs
        """
        # Update location if provided
        if user_location:
            self.location.set_user_location(user_location[0], user_location[1])
        
        # Step 1: Classify waste
        print(f"[INFO] Classifying: {user_input}")
        classification = self.classifier.classify(user_input)
        
        # Step 2: Get disposal guidelines via RAG
        print(f"[INFO] Retrieving guidelines for: {classification.category}")
        guidelines = self.rag.query(classification.category, f"How to dispose of {user_input}?")
        
        # Step 3: Find nearby facilities
        print(f"[INFO] Finding centers for: {classification.category}")
        facilities = self.location.find_centers(classification.category)
        
        # Step 4: Calculate environmental impact
        print(f"[INFO] Calculating impact for: {classification.category}")
        impact = self.impact.calculate_savings(classification.category, weight_kg)
        
        # Step 5: Upload image if provided
        image_upload = None
        if image_path and self.cos:
            print(f"[INFO] Uploading image: {image_path}")
            upload_result = self.cos.upload_image(image_path)
            image_upload = {
                "success": upload_result.success,
                "object_key": upload_result.object_key,
                "presigned_url": upload_result.presigned_url,
                "size_kb": round(upload_result.size_bytes / 1024, 1)
            }
        
        # Build response
        response = EcoSortResponse(
            status="success",
            classification={
                "category": classification.category,
                "confidence": classification.confidence,
                "reason": classification.reason,
                "disposal_instruction": classification.disposal_instruction,
                "safety_note": classification.safety_note,
                "source": classification.source,
                "did_you_know": classification.did_you_know
            },
            guidelines={
                "answer": guidelines.answer,
                "sources": guidelines.sources,
                "confidence": guidelines.confidence
            },
            facilities=[
                {
                    "name": f.name,
                    "address": f.address,
                    "category": f.category,
                    "distance_km": f.distance_km,
                    "hours": f.hours,
                    "phone": f.phone,
                    "accepts": f.accepts
                }
                for f in facilities
            ],
            impact={
                "co2_saved_kg": impact.co2_saved_kg,
                "landfill_diverted_kg": impact.landfill_diverted_kg,
                "trees_equivalent": impact.trees_equivalent,
                "energy_saved_kwh": impact.energy_saved_kwh,
                "water_saved_liters": impact.water_saved_liters,
                "fun_fact": self.impact.get_fun_fact(classification.category)
            },
            image_upload=image_upload
        )
        
        # Generate user-friendly response
        response.user_friendly = self._format_user_response(response)
        
        return response
    
    def _format_user_response(self, response: EcoSortResponse) -> str:
        """Format complete response for user display"""
        cls = response.classification
        guid = response.guidelines
        fac = response.facilities
        imp = response.impact
        img = response.image_upload
        
        lines = [
            f"[EcoSort AI - Waste Analysis]",
            f"",
            f"[Item Classification]",
            f"  Category: **{cls['category']}** ({cls['confidence']*100:.0f}% confident)",
            f"  Reason: {cls['reason']}",
            f"",
            f"[Disposal Instructions]",
            f"  [OK] {cls['disposal_instruction']}",
            f"  [WARN] {cls['safety_note']}" if cls['safety_note'] != "None" else "  [OK] No special safety concerns",
        ]
        
        if cls.get('did_you_know'):
            lines.append(f"  [TIP] *Did you know? {cls['did_you_know']}*")
        
        lines.extend([
            f"",
            f"[Detailed Guidance]",
            f"  {guid['answer']}",
            f"",
            f"[Nearby Collection Centers]",
        ])
        
        if fac:
            for i, f in enumerate(fac[:3], 1):
                lines.append(f"  {i}. **{f['name']}** - {f['distance_km']} km")
                lines.append(f"     {f['address']} | {f['hours']}")
                if f['phone']:
                    lines.append(f"     [PHONE] {f['phone']}")
        else:
            lines.append("  No centers found within 10km. Check municipal website.")
        
        lines.extend([
            f"",
            f"[Your Environmental Impact]",
            f"  [CO2] CO2 saved: {imp['co2_saved_kg']} kg",
            f"  [RECYCLE] Landfill diverted: {imp['landfill_diverted_kg']} kg",
            f"  [TREE] Tree equivalent: {imp['trees_equivalent']} trees/year",
            f"  [ENERGY] Energy saved: {imp['energy_saved_kwh']} kWh",
            f"  [WATER] Water saved: {imp['water_saved_liters']} liters",
            f"  [TIP] *{imp['fun_fact']}*"
        ])
        
        if img and img.get('success'):
            lines.extend([
                f"",
                f"[CLOUD] Image Stored in IBM COS",
                f"  Key: {img['object_key']}",
                f"  Size: {img['size_kb']} KB",
                f"  Access: {img['presigned_url'][:50]}..."
            ])
        
        return "\n".join(lines)
    
    def ask_question(self, category: str, question: str) -> RAGResult:
        """Ask a specific disposal question"""
        return self.rag.query(category, question)
    
    def get_centers_nearby(self, category: Optional[str] = None) -> List[RecyclingCenter]:
        """Get all nearby centers, optionally filtered by category"""
        if category:
            return self.location.find_centers(category)
        return self.location.find_all_nearby()
    
    def calculate_impact(self, category: str, weight_kg: float = 1.0) -> ImpactMetrics:
        """Calculate impact for a category"""
        return self.impact.calculate_savings(category, weight_kg)