"""EcoSort AI - Configuration Management"""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

@dataclass
class WatsonxConfig:
    project_id: str
    api_key: str
    region: str
    model_id: str
    
    @classmethod
    def from_env(cls):
        return cls(
            project_id=os.getenv("WATSONX_PROJECT_ID", ""),
            api_key=os.getenv("WATSONX_API_KEY", ""),
            region=os.getenv("WATSONX_REGION", "us-south"),
            model_id=os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")
        )
    
    def validate(self):
        missing = []
        if not self.project_id: missing.append("WATSONX_PROJECT_ID")
        if not self.api_key: missing.append("WATSONX_API_KEY")
        if missing:
            raise ValueError(f"Missing required Watsonx config: {', '.join(missing)}")

@dataclass
class COSConfig:
    api_key_id: str
    service_instance_id: str
    endpoint: str
    bucket_name: str
    
    @classmethod
    def from_env(cls):
        return cls(
            api_key_id=os.getenv("COS_API_KEY_ID", ""),
            service_instance_id=os.getenv("COS_SERVICE_INSTANCE_ID", ""),
            endpoint=os.getenv("COS_ENDPOINT", "https://s3.us-south.cloud-object-storage.appdomain.cloud"),
            bucket_name=os.getenv("COS_BUCKET_NAME", "ecosort-waste-images")
        )
    
    def validate(self):
        missing = []
        if not self.api_key_id: missing.append("COS_API_KEY_ID")
        if not self.service_instance_id: missing.append("COS_SERVICE_INSTANCE_ID")
        if missing:
            raise ValueError(f"Missing required COS config: {', '.join(missing)}")

@dataclass
class AppConfig:
    max_image_size_mb: int = 10
    allowed_formats: tuple = ("jpg", "jpeg", "png", "webp")
    classification_threshold: float = 0.7
    
    @classmethod
    def from_env(cls):
        return cls(
            max_image_size_mb=int(os.getenv("MAX_IMAGE_SIZE_MB", "10")),
            allowed_formats=tuple(os.getenv("ALLOWED_FORMATS", "jpg,jpeg,png,webp").split(",")),
            classification_threshold=float(os.getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7"))
        )

def load_configs():
    """Load and validate all configurations"""
    watsonx = WatsonxConfig.from_env()
    cos = COSConfig.from_env()
    app = AppConfig.from_env()
    
    # Validate required configs
    try:
        watsonx.validate()
    except ValueError as e:
        print(f"[WARN] Watsonx config incomplete: {e}")
    
    try:
        cos.validate()
    except ValueError as e:
        print(f"[WARN] COS config incomplete: {e}")
    
    return watsonx, cos, app

# Waste categories and their disposal guidelines
WASTE_CATEGORIES = [
    "Organic",
    "Recyclable (Plastic)",
    "Recyclable (Metal)", 
    "Recyclable (Glass)",
    "Recyclable (Paper/Cardboard)",
    "E-waste",
    "Hazardous",
    "Landfill/Reject"
]

DISPOSAL_GUIDELINES = {
    "Organic": "Compost or green bin. Great for garden soil!",
    "Recyclable (Plastic)": "Rinse clean, place in dry/recyclable bin. Check local recycling codes.",
    "Recyclable (Metal)": "Rinse cans, place in recycling. Aluminum & steel are infinitely recyclable.",
    "Recyclable (Glass)": "Rinse bottles/jars, place in glass recycling. 100% recyclable forever.",
    "Recyclable (Paper/Cardboard)": "Clean & dry only. Greasy pizza boxes -> organic. Clean cardboard -> recycle.",
    "E-waste": "[WARN] NEVER in regular trash. Take to authorized e-waste collector. Contains toxic materials.",
    "Hazardous": "[WARN] NEVER in regular trash. Batteries, chemicals, paint -> hazardous waste facility.",
    "Landfill/Reject": "Last resort. Sanitary pads, ceramics, mixed materials. Minimize this category."
}

EMISSION_FACTORS = {
    "Organic": 0.5,
    "Recyclable (Plastic)": 1.5,
    "Recyclable (Metal)": 5.0,
    "Recyclable (Glass)": 0.8,
    "Recyclable (Paper/Cardboard)": 1.0,
    "E-waste": 80.0,
    "Hazardous": 10.0,
    "Landfill/Reject": 0.1
}

SAMPLE_WASTE_ITEMS = {
    "plastic bottle": "Recyclable (Plastic)",
    "banana peel": "Organic",
    "old phone": "E-waste",
    "battery": "Hazardous",
    "aluminum can": "Recyclable (Metal)",
    "glass jar": "Recyclable (Glass)",
    "cardboard box": "Recyclable (Paper/Cardboard)",
    "pizza box (greasy)": "Organic",
    "pizza box (clean lid)": "Recyclable (Paper/Cardboard)",
    "used cooking oil": "Hazardous",
    "expired medicine": "Hazardous",
    "broken ceramic mug": "Landfill/Reject"
}