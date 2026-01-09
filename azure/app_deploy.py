#!/usr/bin/env python3
"""
CVD Expert System - Azure Web App Version
With Pellet Reasoner for SWRL rules
Saves inference results to Azure Cosmos DB
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import threading
from datetime import datetime

app = Flask(__name__, static_folder='static')

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OWL_FILE = os.path.join(BASE_DIR, "cvd_sroiq_complete.owl")

# Cosmos DB Configuration
COSMOS_CONNECTION_STRING = os.environ.get(
    "COSMOS_CONNECTION_STRING",
    "AccountEndpoint=https://kbr-cosmos-db.documents.azure.com:443/;AccountKey=xkUjwOSvuGObMerp7C8rLhG5eIUNztDpHOBZlpRqiXujZXVqXYzVl0weLyEhWOdeSMtMa5kjV2WtACDbCs4nSA==;"
)
COSMOS_DATABASE = "CVDExpertSystem"
COSMOS_CONTAINER = "DiagnosisHistory"

# Knowledge service (lazy loading)
_knowledge_service = None
_ks_lock = threading.Lock()

# Cosmos DB client (lazy loading)
_cosmos_container = None
_cosmos_lock = threading.Lock()


def get_cosmos_container():
    """Get or create Cosmos DB container client (lazy load)."""
    global _cosmos_container
    if _cosmos_container is not None:
        return _cosmos_container
    
    with _cosmos_lock:
        if _cosmos_container is None:
            try:
                from azure.cosmos import CosmosClient
                client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
                database = client.get_database_client(COSMOS_DATABASE)
                _cosmos_container = database.get_container_client(COSMOS_CONTAINER)
                print(f"Connected to Cosmos DB: {COSMOS_DATABASE}/{COSMOS_CONTAINER}")
            except Exception as e:
                print(f"Warning: Could not connect to Cosmos DB: {e}")
                return None
        return _cosmos_container


def save_to_cosmos(patient_id: str, input_data: dict, output_data: dict):
    """Save inference result to Cosmos DB."""
    container = get_cosmos_container()
    if container is None:
        print("Cosmos DB not available, skipping save")
        return None
    
    try:
        timestamp = datetime.now().isoformat()
        doc_id = f"{patient_id}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # Remove reasoning_trace from output (not needed in DB)
        output_clean = {k: v for k, v in output_data.items() if k != 'reasoning_trace'}
        
        document = {
            "id": doc_id,
            "patient_id": patient_id,
            "timestamp": timestamp,
            "input": input_data,
            "output": output_clean,
            "source": "Azure Web App",
            "reasoner": "Pellet"
        }
        
        container.create_item(body=document)
        print(f"Saved to Cosmos DB: {doc_id}")
        return doc_id
    except Exception as e:
        print(f"Error saving to Cosmos DB: {e}")
        return None


def get_knowledge_service():
    """Get or create knowledge service (lazy load)."""
    global _knowledge_service
    if _knowledge_service is not None:
        return _knowledge_service
    
    with _ks_lock:
        if _knowledge_service is None:
            from services.knowledge_service import KnowledgeService
            print(f"Loading ontology from {OWL_FILE}...")
            _knowledge_service = KnowledgeService(OWL_FILE)
            print("Ontology loaded!")
        return _knowledge_service


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
    """Health check - lightweight."""
    return jsonify({
        "status": "healthy",
        "ontology_exists": os.path.exists(OWL_FILE),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """Main diagnosis endpoint with Pellet reasoner."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get knowledge service (loads ontology on first call)
        ks = get_knowledge_service()
        
        # Run diagnosis
        result = ks.diagnose(data)
        result['timestamp'] = datetime.now().isoformat()
        
        # Save to Cosmos DB (async-like, don't block response)
        patient_id = result.get('patient_id', 'unknown')
        cosmos_id = save_to_cosmos(patient_id, data, result)
        if cosmos_id:
            result['cosmos_doc_id'] = cosmos_id
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get diagnosis history from Cosmos DB."""
    try:
        container = get_cosmos_container()
        if container is None:
            return jsonify({"error": "Cosmos DB not available"}), 503
        
        # Optional: filter by patient_id
        patient_id = request.args.get('patient_id')
        limit = int(request.args.get('limit', 50))
        
        if patient_id:
            query = f"SELECT * FROM c WHERE c.patient_id = @patient_id ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@patient_id", "value": patient_id}],
                enable_cross_partition_query=True
            ))
        else:
            query = f"SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
        
        return jsonify({
            "count": len(items),
            "history": items
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/descriptions', methods=['GET'])
def get_descriptions():
    """Get parameter descriptions for tooltips."""
    # Hardcoded descriptions for form fields (from ontology annotations)
    descriptions = {
        "name": {
            "label": "Nama Pasien",
            "description": "Nama lengkap pasien untuk identifikasi rekam medis."
        },
        "age": {
            "label": "Usia",
            "description": "Usia pasien dalam tahun. Faktor risiko kardiovaskular meningkat seiring usia, terutama >45 tahun untuk pria dan >55 tahun untuk wanita."
        },
        "gender": {
            "label": "Jenis Kelamin",
            "description": "Jenis kelamin biologis pasien. Pria memiliki risiko CVD lebih tinggi pada usia muda, wanita risiko meningkat pasca menopause."
        },
        "sbp": {
            "label": "Tekanan Sistolik (mmHg)",
            "description": "Tekanan darah sistolik adalah tekanan saat jantung berkontraksi. Normal <120 mmHg, Elevated 120-129, Hipertensi Stage 1: 130-139, Stage 2: ≥140 mmHg."
        },
        "dbp": {
            "label": "Tekanan Diastolik (mmHg)",
            "description": "Tekanan darah diastolik adalah tekanan saat jantung relaksasi. Normal <80 mmHg, Hipertensi Stage 1: 80-89, Stage 2: ≥90 mmHg."
        },
        "hr": {
            "label": "Denyut Jantung (bpm)",
            "description": "Jumlah detak jantung per menit saat istirahat. Normal 60-100 bpm. Bradikardia <60, Takikardia >100 bpm."
        },
        "bmi": {
            "label": "Indeks Massa Tubuh (kg/m²)",
            "description": "BMI = Berat(kg) / Tinggi(m)². Normal 18.5-24.9, Overweight 25-29.9, Obesitas ≥30. Obesitas meningkatkan risiko hipertensi, diabetes, dan penyakit jantung."
        },
        "fbg": {
            "label": "Gula Darah Puasa (mg/dL)",
            "description": "Kadar glukosa darah setelah puasa 8-12 jam. Normal <100, Prediabetes 100-125, Diabetes ≥126 mg/dL."
        },
        "hba1c": {
            "label": "HbA1c (%)",
            "description": "Hemoglobin A1c menunjukkan rata-rata gula darah 2-3 bulan terakhir. Normal <5.7%, Prediabetes 5.7-6.4%, Diabetes ≥6.5%."
        },
        "ldl": {
            "label": "Kolesterol LDL (mg/dL)",
            "description": "Low-Density Lipoprotein (kolesterol jahat). Optimal <100, Near optimal 100-129, Borderline 130-159, High 160-189, Very high ≥190 mg/dL."
        },
        "hdl": {
            "label": "Kolesterol HDL (mg/dL)",
            "description": "High-Density Lipoprotein (kolesterol baik). Rendah <40 (pria)/<50 (wanita), Optimal ≥60 mg/dL. HDL tinggi melindungi jantung."
        },
        "ef": {
            "label": "Ejection Fraction (%)",
            "description": "Persentase darah yang dipompa keluar ventrikel kiri setiap detak. Normal 55-70%, Borderline 41-54%, Reduced ≤40% (gagal jantung)."
        },
        "troponin": {
            "label": "Troponin (ng/mL)",
            "description": "Biomarker kerusakan otot jantung. Normal <0.04 ng/mL. Peningkatan menunjukkan serangan jantung atau kerusakan miokard."
        },
        "gfr": {
            "label": "eGFR (mL/min/1.73m²)",
            "description": "Estimated Glomerular Filtration Rate menilai fungsi ginjal. Normal ≥90, CKD Stage 2: 60-89, Stage 3: 30-59, Stage 4: 15-29, Stage 5: <15."
        },
        "potassium": {
            "label": "Kalium (mEq/L)",
            "description": "Kadar kalium darah. Normal 3.5-5.0 mEq/L. Hipokalemia <3.5, Hiperkalemia >5.0. Penting untuk fungsi jantung dan otot."
        },
        "ascvd": {
            "label": "Skor ASCVD (%)",
            "description": "Atherosclerotic Cardiovascular Disease 10-year Risk Score. Low <5%, Borderline 5-7.4%, Intermediate 7.5-19.9%, High ≥20%."
        },
        "cha2ds2vasc": {
            "label": "Skor CHA₂DS₂-VASc",
            "description": "Skor risiko stroke pada pasien fibrilasi atrium. 0: risiko rendah, 1: sedang, ≥2: tinggi (perlu antikoagulan)."
        }
    }
    return jsonify(descriptions)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
