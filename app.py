#!/usr/bin/env python3
"""
CVD Expert System - Flask Backend API
Provides diagnosis endpoints and serves frontend.
"""

from flask import Flask, request, jsonify, send_from_directory
import os
from services.sparql_service import SparqlService
import uuid
from datetime import datetime
from azure.cosmos import CosmosClient
import json


# Import knowledge service
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.knowledge_service import KnowledgeService

app = Flask(__name__, static_folder='static')

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Check if running in Azure Functions (HOME is usually /home)
if os.environ.get('HOME') == '/home':
    # In Azure Functions (Docker), code is often in /home/site/wwwroot
    # But usually __file__ is reliable. We check just in case.
    pass

OWL_FILE = os.path.join(BASE_DIR, "cvd_sroiq_complete.owl")
OWL_FILE = os.path.join(BASE_DIR, "cvd_sroiq_complete.owl")

# Cosmos DB Configuration
COSMOS_CONN_STR = os.environ.get('COSMOS_DB_CONNECTION_STRING')
COSMOS_DB_NAME = os.environ.get('COSMOS_DB_DATABASE_NAME', 'CVDExpertSystem')
COSMOS_CONTAINER_NAME = os.environ.get('COSMOS_DB_CONTAINER_NAME', 'DiagnosisHistory')


# Initialize knowledge service (lazily)
knowledge_service = None


def get_knowledge_service():
    """Get or create knowledge service instance."""
    global knowledge_service
    if knowledge_service is None:
        if not os.path.exists(OWL_FILE):
            raise FileNotFoundError(
                f"Ontology file not found: {OWL_FILE}. "
                "Please run build_ontology.py first."
            )
        knowledge_service = KnowledgeService(OWL_FILE)
    return knowledge_service


def init_cosmos_container():
    """Initialize Cosmos DB container if connection string is available."""
    if not COSMOS_CONN_STR:
        return None
    
    try:
        client = CosmosClient.from_connection_string(COSMOS_CONN_STR)
        database = client.create_database_if_not_exists(id=COSMOS_DB_NAME)
        container = database.create_container_if_not_exists(
            id=COSMOS_CONTAINER_NAME,
            partition_key={'paths': ['/patient_id'], 'kind': 'Hash'}
        )
        return container
    except Exception as e:
        print(f"Error initializing Cosmos DB: {e}")
        return None


def save_to_history(result: dict, patient_data: dict):
    """Save diagnosis result to history (Cosmos DB or CSV fallback)."""
    
    # Try Cosmos DB first
    saved_successfully = False
    container = init_cosmos_container()
    if container:
        try:
            # Prepare item for Cosmos DB
            item = {
                "id": str(uuid.uuid4()),  # Unique ID for the record
                "patient_id": result.get('patient_id', 'unknown'),
                "timestamp": result.get('timestamp', datetime.now().isoformat()),
                "demographics": patient_data.get('demographics', {}),
                "diagnosis_result": result,
                "input_data": patient_data
            }
            container.create_item(body=item)
            print("Saved to Cosmos DB")
            saved_successfully = True
        except Exception as e:
            print(f"Failed to save to Cosmos DB: {e}")
    
    # If not saved to Cosmos DB, try SPARQL (Semantic Persistence)
    if not saved_successfully:
        sparql_endpoint = os.environ.get("SPARQL_ENDPOINT")
        if sparql_endpoint:
            try:
                sparql_service = SparqlService(sparql_endpoint)
                sparql_service.save_diagnosis(patient_data, result)
                print("Saved to SPARQL Endpoint")
                saved_successfully = True
            except Exception as e:
                print(f"Error saving to SPARQL: {str(e)}")

    if not saved_successfully:
        print("Failed to save diagnosis history to any configured persistence layer.")


def generate_lifestyle_recommendations(diagnoses: list, patient_data: dict) -> list:
    """Generate lifestyle recommendations based on diagnoses."""
    recommendations = []
    
    diagnosis_names = [d['name'].lower() for d in diagnoses]
    
    # Always recommend these
    recommendations.append({
        "category": "Umum",
        "items": [
            "Kontrol rutin ke dokter setiap 3-6 bulan",
            "Patuhi pengobatan yang diresepkan",
            "Jaga pola tidur 7-8 jam per malam"
        ]
    })
    
    # Hypertension
    if any('hipertensi' in d for d in diagnosis_names):
        recommendations.append({
            "category": "Tekanan Darah",
            "items": [
                "Batasi asupan garam < 2g/hari",
                "Diet DASH (buah, sayur, rendah lemak)",
                "Hindari stres berlebihan",
                "Olahraga aerobik 30 menit, 5x/minggu"
            ]
        })
    
    # Diabetes
    if any('diabetes' in d or 'prediabetes' in d for d in diagnosis_names):
        recommendations.append({
            "category": "Gula Darah",
            "items": [
                "Batasi karbohidrat sederhana (gula, nasi putih)",
                "Makan teratur 3x sehari",
                "Cek gula darah rutin",
                "Target HbA1c < 7%"
            ]
        })
    
    # Dyslipidemia
    if any('dislipidemia' in d or 'ldl' in d for d in diagnosis_names):
        recommendations.append({
            "category": "Kolesterol",
            "items": [
                "Batasi lemak jenuh dan trans",
                "Konsumsi ikan 2x/minggu",
                "Tingkatkan serat (oat, kacang)",
                "Hindari gorengan"
            ]
        })
    
    # Heart Failure
    if any('gagal jantung' in d or 'hfref' in d.lower() for d in diagnosis_names):
        recommendations.append({
            "category": "Gagal Jantung",
            "items": [
                "Batasi cairan 1.5-2L/hari",
                "Timbang berat badan setiap hari",
                "Hindari aktivitas berat",
                "Tidur dengan kepala agak tinggi"
            ]
        })
    
    # Obesity
    if any('obesitas' in d or 'overweight' in d for d in diagnosis_names):
        recommendations.append({
            "category": "Berat Badan",
            "items": [
                "Target penurunan 5-10% dalam 6 bulan",
                "Kurangi porsi makan",
                "Hindari makan malam terlalu larut",
                "Aktivitas fisik minimal 150 menit/minggu"
            ]
        })
    
    # Smoking (from history)
    if patient_data.get('history', {}).get('smoking'):
        recommendations.append({
            "category": "Berhenti Merokok",
            "items": [
                "Berhenti merokok SEGERA",
                "Konsultasi program berhenti merokok",
                "Gunakan terapi pengganti nikotin jika perlu",
                "Merokok meningkatkan risiko serangan jantung 2-4x"
            ]
        })
    
    return recommendations


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory(app.static_folder, path)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        get_knowledge_service()
        return jsonify({
            "status": "healthy",
            "ontology_loaded": True,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """
    Main diagnosis endpoint.
    
    Expects JSON body with:
    - demographics: {name, age, gender}
    - vitals: {sbp, dbp, hr, bmi, weight, height}
    - labs: {fbg, hba1c, ldl, hdl, ef, troponin, gfr, etc.}
    - symptoms: ["nyeri_dada", "sesak_napas", "edema", etc.]
    - comorbid: {asthma, pregnancy, liver_disease}
    - history: {smoking, cad}
    - scores: {ascvd, cha2ds2vasc}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get knowledge service
        ks = get_knowledge_service()
        
        # Run diagnosis (includes lifestyle_recommendations from ontology)
        result = ks.diagnose(data)
        
        # Save to History
        save_to_history(result, data)
        
        return jsonify(result)
        
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get diagnosis history."""
    try:
        # Try Cosmos first
        if COSMOS_CONN_STR:
            history = get_history_from_cosmos()
            if history is not None:
                return jsonify({"history": history})
        
        # Try SPARQL if configured
        sparql_endpoint = os.environ.get("SPARQL_ENDPOINT")
        if sparql_endpoint:
            try:
                sparql_service = SparqlService(sparql_endpoint)
                history = sparql_service.get_history()
                return jsonify({"history": history})
            except Exception as e:
                print(f"Error fetching from SPARQL: {e}")
                
        return jsonify({"history": []})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_history_from_cosmos():
    """Fetch history from Cosmos DB."""
    container = init_cosmos_container()
    if not container:
        return None
        
    try:
        # Query latest 50 items
        query = "SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT 50"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Transform to flat format for frontend compatibility
        history = []
        for item in items:
            res = item.get('diagnosis_result', {})
            demo = item.get('demographics', {})
            
            flat = {
                'timestamp': res.get('timestamp'),
                'patient_name': demo.get('name', 'Unknown'),
                'age': demo.get('age', ''),
                'gender': demo.get('gender', ''),
                'diagnoses': '; '.join([d['name'] for d in res.get('diagnoses', [])]),
                'medications': '; '.join([m['name'] for m in res.get('medications', [])]),
                'contraindications': '; '.join([c['drug'] for c in res.get('contraindications', [])]),
                'risk_category': res.get('risk_category', ''),
                'ascvd_score': res.get('ascvd_score', ''),
                'severity': res.get('severity', ''),
                'rules_fired': res.get('rules_fired', 0),
                'emergency': res.get('emergency', False)
            }
            history.append(flat)
            
        return history
    except Exception as e:
        print(f"Error querying Cosmos: {e}")
        return None


@app.route('/api/ontology/stats', methods=['GET'])
def ontology_stats():
    """Get ontology statistics."""
    try:
        ks = get_knowledge_service()
        onto = ks.onto
        
        return jsonify({
            "classes": len(list(onto.classes())),
            "object_properties": len(list(onto.object_properties())),
            "data_properties": len(list(onto.data_properties())),
            "individuals": len(list(onto.individuals())),
            "swrl_rules": len(list(onto.rules()))
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/descriptions', methods=['GET'])
def get_descriptions():
    """Get parameter descriptions from ontology for tooltips."""
    try:
        ks = get_knowledge_service()
        descriptions = ks.get_parameter_descriptions()
        return jsonify(descriptions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(e):
    print(f"❌ 404 Error: Path '{request.path}' not found. URL: {request.url}")
    return jsonify({"error": "Not found", "path": request.path}), 404


@app.route('/api/debug_routing')
def debug_routing():
    """Debug endpoint to inspect request environment."""
    return jsonify({
        "path": request.path,
        "url": request.url,
        "script_root": request.script_root,
        "headers": dict(request.headers),
        "environ_keys": list(request.environ.keys())
    })


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  CVD Expert System - Starting Server")
    print("=" * 60)
    print(f"  Ontology: {OWL_FILE}")
    print(f"  Frontend: http://localhost:5000")
    print("=" * 60)
    
    # Pre-load ontology
    try:
        print("\n⏳ Loading ontology...")
        get_knowledge_service()
        print("✅ Ontology loaded successfully!\n")
    except FileNotFoundError:
        print("⚠️  Ontology not found. Please run build_ontology.py first.\n")
    except Exception as e:
        print(f"⚠️  Warning: {e}\n")
    
    import sys
    port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 5000
    app.run(host='0.0.0.0', port=port, debug=True)
