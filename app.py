"""
EcoSort AI - Flask Web Application
Backend API for waste classification with IBM Granite + RAG
"""
import os
import sys
import tempfile
import base64
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.supervisor import EcoSortSupervisor
from agents.classifier import WasteClassifierAgent
from agents.rag_agent import RAGAgent
from agents.location_impact import LocationAgent, ImpactTrackerAgent

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Initialize supervisor
supervisor = EcoSortSupervisor()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/classify', methods=['POST'])
def classify():
    """Classify waste item from text or image"""
    try:
        data = request.get_json() or {}
        item_description = data.get('item', '').strip()
        image_base64 = data.get('image')
        weight_kg = float(data.get('weight', 1.0))
        user_location = data.get('location')
        
        if not item_description and not image_base64:
            return jsonify({'error': 'Item description or image required'}), 400
        
        # Handle image upload (save temp file for processing)
        image_path = None
        if image_base64:
            try:
                # Remove data URL prefix if present
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                image_data = base64.b64decode(image_base64)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', dir=app.config['UPLOAD_FOLDER'])
                temp_file.write(image_data)
                temp_file.close()
                image_path = temp_file.name
            except Exception as e:
                return jsonify({'error': f'Image processing failed: {str(e)}'}), 400
        
        # Process through supervisor
        if user_location:
            lat, lon = user_location
            supervisor.location.set_user_location(lat, lon)
        
        response = supervisor.process_request(
            user_input=item_description or "waste item from image",
            weight_kg=weight_kg,
            image_path=image_path
        )
        
        # Clean up temp file
        if image_path and os.path.exists(image_path):
            os.unlink(image_path)
        
        return jsonify({
            'status': 'success',
            'classification': response.classification,
            'guidelines': response.guidelines,
            'facilities': response.facilities,
            'impact': response.impact,
            'image_upload': response.image_upload,
            'user_friendly': response.user_friendly
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Ask a specific disposal question"""
    try:
        data = request.get_json()
        category = data.get('category')
        question = data.get('question')
        
        if not category or not question:
            return jsonify({'error': 'Category and question required'}), 400
        
        result = supervisor.ask_question(category, question)
        return jsonify({
            'answer': result.answer,
            'sources': result.sources,
            'confidence': result.confidence,
            'category': result.category
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/centers', methods=['GET'])
def get_centers():
    """Get nearby recycling centers"""
    try:
        category = request.args.get('category')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if lat and lon:
            supervisor.location.set_user_location(lat, lon)
        
        if category:
            centers = supervisor.get_centers_nearby(category)
        else:
            centers = supervisor.get_centers_nearby()
        
        return jsonify({
            'centers': [
                {
                    'name': c.name,
                    'address': c.address,
                    'category': c.category,
                    'distance_km': c.distance_km,
                    'hours': c.hours,
                    'phone': c.phone,
                    'accepts': c.accepts
                }
                for c in centers
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/impact', methods=['POST'])
def calculate_impact():
    """Calculate environmental impact"""
    try:
        data = request.get_json()
        category = data.get('category')
        weight_kg = float(data.get('weight', 1.0))
        
        if not category:
            return jsonify({'error': 'Category required'}), 400
        
        metrics = supervisor.calculate_impact(category, weight_kg)
        fun_fact = supervisor.impact.get_fun_fact(category)
        
        return jsonify({
            'co2_saved_kg': metrics.co2_saved_kg,
            'landfill_diverted_kg': metrics.landfill_diverted_kg,
            'trees_equivalent': metrics.trees_equivalent,
            'energy_saved_kwh': metrics.energy_saved_kwh,
            'water_saved_liters': metrics.water_saved_liters,
            'fun_fact': fun_fact
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all waste categories"""
    from src.config.settings import WASTE_CATEGORIES, DISPOSAL_GUIDELINES
    return jsonify({
        'categories': WASTE_CATEGORIES,
        'guidelines': DISPOSAL_GUIDELINES
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'EcoSort AI'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)