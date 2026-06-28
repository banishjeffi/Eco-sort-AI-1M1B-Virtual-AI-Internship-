"""
Location Agent - Finds nearby recycling centers
Impact Tracker - Calculates environmental impact metrics
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class RecyclingCenter:
    name: str
    address: str
    category: str
    distance_km: float
    hours: str
    phone: Optional[str] = None
    accepts: List[str] = None
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class ImpactMetrics:
    co2_saved_kg: float
    landfill_diverted_kg: float
    trees_equivalent: float
    energy_saved_kwh: float
    water_saved_liters: float


class LocationAgent:
    """Finds nearby recycling centers (mock data for demo, replace with Maps API)"""
    
    # Mock database - replace with Google Maps / OpenStreetMap API in production
    MOCK_CENTERS = [
        RecyclingCenter(
            name="GreenEco Recyclers",
            address="123 Industrial Area, Phase 2",
            category="E-waste",
            distance_km=1.2,
            hours="Mon-Sat 9AM-6PM",
            phone="+91-XXXXX-XXXXX",
            accepts=["E-waste", "Hazardous"],
            latitude=28.6139,
            longitude=77.2090
        ),
        RecyclingCenter(
            name="City Compost Hub",
            address="456 Green Park Road",
            category="Organic",
            distance_km=0.8,
            hours="Daily 6AM-8PM",
            phone="+91-XXXXX-XXXXX",
            accepts=["Organic"],
            latitude=28.6145,
            longitude=77.2085
        ),
        RecyclingCenter(
            name="SafeHazard Facility",
            address="789 Chemical Zone",
            category="Hazardous",
            distance_km=3.5,
            hours="Mon-Fri 10AM-4PM",
            phone="+91-XXXXX-XXXXX",
            accepts=["Hazardous", "E-waste"],
            latitude=28.6150,
            longitude=77.2100
        ),
        RecyclingCenter(
            name="Metro Recycling Center",
            address="321 Circular Road",
            category="Recyclable (Plastic)",
            distance_km=1.5,
            hours="Daily 8AM-8PM",
            phone="+91-XXXXX-XXXXX",
            accepts=["Recyclable (Plastic)", "Recyclable (Metal)", "Recyclable (Glass)", "Recyclable (Paper/Cardboard)"],
            latitude=28.6130,
            longitude=77.2080
        ),
        RecyclingCenter(
            name="Paper & Cardboard Co.",
            address="555 Old Mill Road",
            category="Recyclable (Paper/Cardboard)",
            distance_km=2.1,
            hours="Mon-Sat 8AM-5PM",
            phone="+91-XXXXX-XXXXX",
            accepts=["Recyclable (Paper/Cardboard)"],
            latitude=28.6120,
            longitude=77.2110
        )
    ]
    
    def __init__(self, user_lat: float = 28.6139, user_lon: float = 77.2090):
        self.user_lat = user_lat
        self.user_lon = user_lon
    
    def find_centers(self, category: str, max_distance_km: float = 10.0) -> List[RecyclingCenter]:
        """Find centers accepting the given waste category"""
        matches = [
            c for c in self.MOCK_CENTERS
            if category in (c.accepts or [c.category])
            and c.distance_km <= max_distance_km
        ]
        return sorted(matches, key=lambda x: x.distance_km)
    
    def find_all_nearby(self, max_distance_km: float = 10.0) -> List[RecyclingCenter]:
        """Get all centers within distance"""
        return [c for c in self.MOCK_CENTERS if c.distance_km <= max_distance_km]
    
    def set_user_location(self, lat: float, lon: float):
        """Update user location for distance calculations"""
        self.user_lat = lat
        self.user_lon = lon
        # Recalculate distances (simplified - in production use Haversine)
        for center in self.MOCK_CENTERS:
            # Simple mock distance update
            center.distance_km = round(abs(center.latitude - lat) * 111 + 
                                      abs(center.longitude - lon) * 111, 1)


class ImpactTrackerAgent:
    """Calculates environmental impact of proper waste disposal"""
    
    # Emission factors (kg CO2e per kg waste properly processed)
    EMISSION_FACTORS = {
        "Organic": 0.5,           # Composting vs landfill methane
        "Recyclable (Plastic)": 1.5,    # Recycling vs virgin plastic
        "Recyclable (Metal)": 5.0,      # Aluminum recycling saves 95% energy
        "Recyclable (Glass)": 0.8,      # Recycling vs new glass
        "Recyclable (Paper/Cardboard)": 1.0,  # Recycling vs virgin pulp
        "E-waste": 80.0,         # Precious metal recovery vs mining
        "Hazardous": 10.0,       # Proper treatment vs environmental damage
        "Landfill/Reject": 0.1   # Minimal benefit
    }
    
    # Additional impact metrics per kg
    ADDITIONAL_METRICS = {
        "Organic": {"energy_kwh": 0.5, "water_l": 10, "trees": 0.025},
        "Recyclable (Plastic)": {"energy_kwh": 5.0, "water_l": 50, "trees": 0.05},
        "Recyclable (Metal)": {"energy_kwh": 15.0, "water_l": 100, "trees": 0.2},
        "Recyclable (Glass)": {"energy_kwh": 2.0, "water_l": 20, "trees": 0.03},
        "Recyclable (Paper/Cardboard)": {"energy_kwh": 4.0, "water_l": 30, "trees": 0.15},
        "E-waste": {"energy_kwh": 200.0, "water_l": 500, "trees": 1.0},
        "Hazardous": {"energy_kwh": 20.0, "water_l": 200, "trees": 0.3},
        "Landfill/Reject": {"energy_kwh": 0.1, "water_l": 1, "trees": 0.001}
    }
    
    def calculate_savings(self, category: str, weight_kg: float = 1.0) -> ImpactMetrics:
        """Calculate environmental impact for properly disposing waste"""
        co2_factor = self.EMISSION_FACTORS.get(category, 0.1)
        additional = self.ADDITIONAL_METRICS.get(category, 
            {"energy_kwh": 0.1, "water_l": 1, "trees": 0.001})
        
        co2_saved = weight_kg * co2_factor
        landfill_diverted = weight_kg * 0.95  # 95% diversion rate
        trees = co2_saved / 21.8  # 1 tree absorbs ~21.8 kg CO2/year
        energy = weight_kg * additional["energy_kwh"]
        water = weight_kg * additional["water_l"]
        
        return ImpactMetrics(
            co2_saved_kg=round(co2_saved, 2),
            landfill_diverted_kg=round(landfill_diverted, 2),
            trees_equivalent=round(trees, 2),
            energy_saved_kwh=round(energy, 2),
            water_saved_liters=round(water, 2)
        )
    
    def format_impact(self, metrics: ImpactMetrics, category: str, weight_kg: float = 1.0) -> str:
        """Format impact metrics for user display"""
        lines = [
            f"Environmental Impact ({weight_kg} kg {category})",
            f"  CO2 saved: {metrics.co2_saved_kg} kg",
            f"  Landfill diverted: {metrics.landfill_diverted_kg} kg",
            f"  Tree equivalent: {metrics.trees_equivalent} trees/year",
            f"  Energy saved: {metrics.energy_saved_kwh} kWh",
            f"  Water saved: {metrics.water_saved_liters} liters"
        ]
        return "\n".join(lines)
    
    def get_fun_fact(self, category: str) -> str:
        """Get an interesting environmental fact for the category"""
        facts = {
            "Organic": "Composting 1kg food waste = 0.5kg CO2 saved = powering a phone for 60 hours!",
            "Recyclable (Plastic)": "1 recycled plastic bottle saves energy for a 60W bulb for 6 hours!",
            "Recyclable (Metal)": "Aluminum can -> new can in 60 days. Recycling saves 95% energy!",
            "Recyclable (Glass)": "Glass takes 1,000,000 years to decompose but recycles forever!",
            "Recyclable (Paper/Cardboard)": "1 ton recycled paper saves 17 trees, 7000 gallons water!",
            "E-waste": "1 ton e-waste has more gold than 1 ton gold ore! Your phone has ~0.034g gold.",
            "Hazardous": "1 liter motor oil contaminates 1,000,000 liters water - proper disposal is critical!",
            "Landfill/Reject": "Reducing landfill waste extends landfill life and reduces methane emissions."
        }
        return facts.get(category, "Every bit of proper sorting helps the planet!")