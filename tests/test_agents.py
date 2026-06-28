"""
Tests for EcoSort AI agents
Run with: pytest tests/ -v
"""
import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.classifier import WasteClassifierAgent, ClassificationResult
from agents.rag_agent import RAGAgent, RAGResult
from agents.location_impact import LocationAgent, ImpactTrackerAgent, ImpactMetrics
from agents.supervisor import EcoSortSupervisor, EcoSortResponse


class TestWasteClassifier:
    """Test waste classification"""
    
    @pytest.fixture
    def classifier(self):
        return WasteClassifierAgent()
    
    def test_organic_classification(self, classifier):
        result = classifier.classify("banana peel")
        assert isinstance(result, ClassificationResult)
        assert result.category == "Organic"
        assert result.confidence > 0.5
    
    def test_recyclable_plastic(self, classifier):
        result = classifier.classify("plastic water bottle")
        assert result.category == "Recyclable (Plastic)"
        assert result.confidence > 0.8
    
    def test_e_waste(self, classifier):
        result = classifier.classify("old smartphone")
        assert result.category == "E-waste"
        assert result.confidence > 0.9
    
    def test_hazardous(self, classifier):
        result = classifier.classify("used battery")
        assert result.category == "Hazardous"
        assert result.confidence > 0.9
    
    def test_metal_recyclable(self, classifier):
        result = classifier.classify("aluminum can")
        assert result.category == "Recyclable (Metal)"
    
    def test_glass_recyclable(self, classifier):
        result = classifier.classify("glass jar")
        assert result.category == "Recyclable (Glass)"
    
    def test_paper_recyclable(self, classifier):
        result = classifier.classify("cardboard box")
        assert result.category == "Recyclable (Paper/Cardboard)"
    
    def test_unknown_item(self, classifier):
        result = classifier.classify("random unknown item xyz")
        assert result.category == "Landfill/Reject"
        assert result.confidence < 0.5


class TestRAGAgent:
    """Test RAG retrieval and generation"""
    
    @pytest.fixture
    def rag(self):
        return RAGAgent()
    
    def test_organic_query(self, rag):
        result = rag.query("Organic", "How to compost food waste?")
        assert isinstance(result, RAGResult)
        assert result.category == "Organic"
        assert len(result.answer) > 10
        assert result.confidence > 0.5
    
    def test_hazardous_battery_query(self, rag):
        result = rag.query("Hazardous", "Where to dispose batteries?")
        assert "battery" in result.answer.lower() or "hazardous" in result.answer.lower()
    
    def test_e_waste_query(self, rag):
        result = rag.query("E-waste", "How to recycle old phone?")
        assert "recycle" in result.answer.lower() or "e-waste" in result.answer.lower()
    
    def test_unknown_category(self, rag):
        result = rag.query("UnknownCategory", "Test question")
        # Should fall back gracefully
        assert isinstance(result, RAGResult)


class TestLocationAgent:
    """Test location services"""
    
    @pytest.fixture
    def location(self):
        return LocationAgent()
    
    def test_find_centers_e_waste(self, location):
        centers = location.find_centers("E-waste")
        assert len(centers) > 0
        assert all("E-waste" in (c.accepts or [c.category]) for c in centers)
    
    def test_find_centers_organic(self, location):
        centers = location.find_centers("Organic")
        assert len(centers) > 0
    
    def test_find_all_nearby(self, location):
        centers = location.find_all_nearby()
        assert len(centers) >= 3


class TestImpactTracker:
    """Test environmental impact calculations"""
    
    @pytest.fixture
    def impact(self):
        return ImpactTrackerAgent()
    
    def test_organic_impact(self, impact):
        metrics = impact.calculate_savings("Organic", 1.0)
        assert isinstance(metrics, ImpactMetrics)
        assert metrics.co2_saved_kg > 0
        assert metrics.landfill_diverted_kg > 0
    
    def test_e_waste_high_impact(self, impact):
        metrics = impact.calculate_savings("E-waste", 1.0)
        assert metrics.co2_saved_kg > 50  # E-waste has high impact
    
    def test_weight_scaling(self, impact):
        m1 = impact.calculate_savings("Organic", 1.0)
        m2 = impact.calculate_savings("Organic", 2.0)
        assert m2.co2_saved_kg == pytest.approx(m1.co2_saved_kg * 2, rel=0.01)
    
    def test_fun_fact(self, impact):
        fact = impact.get_fun_fact("E-waste")
        assert len(fact) > 10
        assert "gold" in fact.lower() or "ore" in fact.lower()


class TestSupervisor:
    """Test full supervisor pipeline"""
    
    @pytest.fixture
    def supervisor(self):
        return EcoSortSupervisor()
    
    def test_full_pipeline(self, supervisor):
        response = supervisor.process_request("plastic bottle")
        assert isinstance(response, EcoSortResponse)
        assert response.status == "success"
        assert response.classification is not None
        assert response.classification["category"] == "Recyclable (Plastic)"
        assert response.guidelines is not None
        assert response.facilities is not None
        assert response.impact is not None
        assert len(response.user_friendly) > 100
    
    def test_e_waste_pipeline(self, supervisor):
        response = supervisor.process_request("old laptop")
        assert response.classification["category"] == "E-waste"
        assert len(response.facilities) > 0
        assert response.impact["co2_saved_kg"] > 50
    
    def test_organic_pipeline(self, supervisor):
        response = supervisor.process_request("food scraps")
        assert response.classification["category"] == "Organic"
    
    def test_ask_question(self, supervisor):
        result = supervisor.ask_question("Organic", "Can I compost meat?")
        assert isinstance(result, RAGResult)
        assert len(result.answer) > 10
    
    def test_user_friendly_format(self, supervisor):
        response = supervisor.process_request("aluminum can")
        output = response.user_friendly
        assert "EcoSort AI" in output
        assert "Recyclable (Metal)" in output
        assert "CO2 saved" in output
        assert "Nearby Collection Centers" in output


class TestIntegration:
    """Integration tests"""
    
    def test_multiple_categories(self):
        classifier = WasteClassifierAgent()
        supervisor = EcoSortSupervisor()
        
        test_cases = [
            ("plastic bottle", "Recyclable (Plastic)"),
            ("banana peel", "Organic"),
            ("old phone", "E-waste"),
            ("battery", "Hazardous"),
            ("aluminum can", "Recyclable (Metal)"),
            ("glass jar", "Recyclable (Glass)"),
            ("cardboard", "Recyclable (Paper/Cardboard)"),
            ("diaper", "Landfill/Reject"),
        ]
        
        for item, expected_cat in test_cases:
            result = classifier.classify(item)
            assert result.category == expected_cat, f"Failed for {item}: got {result.category}"
            
            # Full pipeline
            response = supervisor.process_request(item)
            assert response.classification["category"] == expected_cat


if __name__ == "__main__":
    pytest.main([__file__, "-v"])