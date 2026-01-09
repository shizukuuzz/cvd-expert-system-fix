
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from datetime import datetime
import uuid
import logging

class SparqlService:
    """Service for interacting with Apache Jena Fuseki via SPARQL."""
    
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self.update_endpoint = f"{endpoint_url}/update"
        self.query_endpoint = f"{endpoint_url}/query"
        self.namespace = "http://www.cvd-expert-system.org/ontology#"
        self.prefix = f"PREFIX cvd: <{self.namespace}>\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"

    def _clean_string(self, text):
        """Clean string for SPARQL literal."""
        if not text:
            return ""
        return str(text).replace('"', "'").replace('\n', ' ').strip()

    def save_diagnosis(self, patient_data: dict, diagnosis_result: dict) -> bool:
        """
        Save diagnosis result to Jena Fuseki using SPARQL INSERT.
        """
        try:
            # Generate unique ID for this diagnosis event
            diag_id = f"Diagnosa_{uuid.uuid4().hex[:8]}"
            patient_name = self._clean_string(patient_data.get('demographics', {}).get('name', 'Unknown'))
            patient_id_ref = diagnosis_result.get('patient_id') # Ref to the individual in ontology
            
            timestamp = datetime.now().isoformat()
            
            # Prepare data values
            age = patient_data.get('demographics', {}).get('age', 0)
            gender = self._clean_string(patient_data.get('demographics', {}).get('gender', 'Unknown'))
            
            # Construct RDF Triples for INSERT
            triples = []
            
            # Define Patient individual (if not exists, or update existing)
            # Note: We use the same ID logic as KnowledgeService to ensure consistency
            triples.append(f"cvd:{patient_id_ref} rdf:type cvd:Pasien .")
            triples.append(f'cvd:{patient_id_ref} cvd:memilikiNama "{patient_name}"^^xsd:string .')
            triples.append(f'cvd:{patient_id_ref} cvd:memilikiUsia "{age}"^^xsd:integer .')
            triples.append(f'cvd:{patient_id_ref} cvd:memilikiJenisKelamin "{gender}"^^xsd:string .')
            
            # Add Diagnoses properties
            for diag in diagnosis_result.get('diagnoses', []):
                diag_class = diag.get('class')
                if diag_class:
                    triples.append(f"cvd:{patient_id_ref} cvd:memiliki cvd:{diag_class}_Instance .") # Assuming instance linking or creates new
                    # Alternatively, just link to the class/concept if that's what we mean
                    # But usually output connects to specific instances. 
                    # Let's link to the stored 'memiliki' relationships.
            
            # For logging history, we might want a separate "DiagnosisEvent" object in RDF
            # Or attach timestamp to the patient (though patient has many diagnoses over time)
            # Let's create a specific History/Log object if we want time-series
            # But per user request "save result", let's attach the result directly to patient 
            # and maybe add a Data Property for the specific timestamp of THIS diagnosis
            
            # Simplified approach: Update the Patient individual with the latest facts
            
            # 1. Diagnoses
            for d in diagnosis_result.get('diagnoses', []):
                d_name = d.get('name')
                triples.append(f'cvd:{patient_id_ref} cvd:hasRecentDiagnosis "{self._clean_string(d_name)}"^^xsd:string .')

            # 2. Risk & Severity
            risk = diagnosis_result.get('risk_category')
            severity = diagnosis_result.get('severity')
            triples.append(f'cvd:{patient_id_ref} cvd:hasRecentRiskCategory "{self._clean_string(risk)}"^^xsd:string .')
            triples.append(f'cvd:{patient_id_ref} cvd:hasRecentSeverity "{self._clean_string(severity)}"^^xsd:string .')
            
            # 3. Timestamp & Medical Data
            triples.append(f'cvd:{patient_id_ref} cvd:lastDiagnosisTime "{timestamp}"^^xsd:dateTime .')
            
            # Additional CSV-matching fields
            ascvd = diagnosis_result.get('ascvd_score', 0)
            rules = diagnosis_result.get('rules_fired', 0)
            emergency = str(diagnosis_result.get('emergency', 'False')).lower()
            
            triples.append(f'cvd:{patient_id_ref} cvd:hasRecentASCVD "{ascvd}"^^xsd:float .')
            triples.append(f'cvd:{patient_id_ref} cvd:hasRulesFired "{rules}"^^xsd:integer .')
            triples.append(f'cvd:{patient_id_ref} cvd:isEmergency "{emergency}"^^xsd:boolean .')

            # 4. Medications (List)
            for m in diagnosis_result.get('medications', []):
                m_name = self._clean_string(m.get('name'))
                triples.append(f'cvd:{patient_id_ref} cvd:hasRecommendedMedication "{m_name}"^^xsd:string .')

            # 5. Contraindications (List)
            for c in diagnosis_result.get('contraindications', []):
                c_drug = self._clean_string(c.get('drug'))
                triples.append(f'cvd:{patient_id_ref} cvd:hasContraindication "{c_drug}"^^xsd:string .')

            triple_str = "\n".join(triples)
            
            query = f"""
            {self.prefix}
            
            INSERT DATA {{
                {triple_str}
            }}
            """
            
            # VISIBILITY: Print the query for the user
            print("\n" + "="*50)
            print(" [GENERATED SPARQL INSERT QUERY] ")
            print("="*50)
            print(query)
            print("="*50 + "\n")
            
            sparql = SPARQLWrapper(self.update_endpoint)
            sparql.setMethod(POST)
            sparql.setQuery(query)
            sparql.query()
            
            logging.info(f"Successfully saved diagnosis to Jena for patient {patient_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save to Jena: {str(e)}")
            return False

    def get_history(self, limit=50):
        """Retrieve diagnosis history from Jena."""
        try:
            query = f"""
            {self.prefix}
            
            SELECT ?time ?name ?age ?gender 
                   (GROUP_CONCAT(DISTINCT ?diag; separator="; ") AS ?diagnoses)
                   (GROUP_CONCAT(DISTINCT ?med; separator="; ") AS ?medications)
                   (GROUP_CONCAT(DISTINCT ?contra; separator="; ") AS ?contraindications)
                   ?risk ?ascvd ?severity ?rules ?emergency
            WHERE {{
                ?patient rdf:type cvd:Pasien ;
                         cvd:memilikiNama ?name ;
                         cvd:memilikiUsia ?age ;
                         cvd:memilikiJenisKelamin ?gender ;
                         cvd:lastDiagnosisTime ?time .
                
                OPTIONAL {{ ?patient cvd:hasRecentDiagnosis ?diag }}
                OPTIONAL {{ ?patient cvd:hasRecommendedMedication ?med }}
                OPTIONAL {{ ?patient cvd:hasContraindication ?contra }}
                
                OPTIONAL {{ ?patient cvd:hasRecentRiskCategory ?risk }}
                OPTIONAL {{ ?patient cvd:hasRecentSeverity ?severity }}
                OPTIONAL {{ ?patient cvd:hasRecentASCVD ?ascvd }}
                OPTIONAL {{ ?patient cvd:hasRulesFired ?rules }}
                OPTIONAL {{ ?patient cvd:isEmergency ?emergency }}
            }}
            GROUP BY ?time ?name ?age ?gender ?risk ?ascvd ?severity ?rules ?emergency
            ORDER BY DESC(?time)
            LIMIT {limit}
            """
            
            # VISIBILITY: Print the query for the user
            print("\n" + "="*50)
            print(" [GENERATED SPARQL COMPLEX SELECT QUERY] ")
            print("="*50)
            print(query)
            print("="*50 + "\n")
            
            sparql = SPARQLWrapper(self.query_endpoint)
            sparql.setReturnFormat(JSON)
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            history = []
            for r in results["results"]["bindings"]:
                history.append({
                    "timestamp": r.get("time", {}).get("value", ""),
                    "patient_name": r.get("name", {}).get("value", "Unknown"),
                    "age": r.get("age", {}).get("value", ""),
                    "gender": r.get("gender", {}).get("value", ""),
                    "diagnoses": r.get("diagnoses", {}).get("value", ""),
                    "medications": r.get("medications", {}).get("value", ""),
                    "contraindications": r.get("contraindications", {}).get("value", ""),
                    "risk_category": r.get("risk", {}).get("value", ""),
                    "ascvd_score": r.get("ascvd", {}).get("value", ""),
                    "severity": r.get("severity", {}).get("value", ""),
                    "rules_fired": r.get("rules", {}).get("value", 0),
                    "emergency": r.get("emergency", {}).get("value", "false")
                })
                
            return history
            
        except Exception as e:
            logging.error(f"Failed to fetch history from Jena: {str(e)}")
            return []
