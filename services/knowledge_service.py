"""
Knowledge Service - CVD Expert System
Handles ontology loading, patient instance creation, and Pellet reasoning.
"""

from owlready2 import *
# Set Java Memory to 1024M to prevent OOM in Azure Functions (Default is 2000M)
import owlready2
owlready2.reasoning.JAVA_MEMORY = 1024
import uuid
import os
from datetime import datetime


class KnowledgeService:
    """Service for interacting with the CVD ontology."""
    
    def __init__(self, ontology_path: str):
        """Initialize the knowledge service with ontology."""
        self.ontology_path = ontology_path
        self.onto = None
        self.reasoning_trace = []
        self._load_ontology()
    
    def _load_ontology(self):
        """Load the ontology from file."""
        if not os.path.exists(self.ontology_path):
            raise FileNotFoundError(f"Ontology file not found: {self.ontology_path}")
        
        # Use file:// protocol for owlready2
        onto_path = "file://" + self.ontology_path.replace(" ", "%20")
        self.onto = get_ontology(onto_path).load()
    
    def create_patient(self, data: dict) -> str:
        """
        Create a patient individual in the ontology.
        
        Args:
            data: Patient data dictionary with demographics, vitals, labs, etc.
            
        Returns:
            Patient ID (individual name)
        """
        self.reasoning_trace = []
        
        with self.onto:
            # Generate unique patient ID
            patient_name = data.get("demographics", {}).get("name", "Unknown")
            patient_id = f"Pasien_{patient_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
            
            # Create patient individual
            Pasien = self.onto.Pasien
            patient = Pasien(patient_id)
            
            # Set demographics (use single values, not lists, for FunctionalProperty)
            demo = data.get("demographics", {})
            if "name" in demo:
                patient.memilikiNama = demo["name"]
            if "age" in demo:
                patient.memilikiUsia = int(demo["age"])
            if "gender" in demo:
                patient.memilikiJenisKelamin = demo["gender"]
            
            # Set vital signs
            vitals = data.get("vitals", {})
            if "sbp" in vitals:
                patient.memilikiTekananSistolik = int(vitals["sbp"])
                self.reasoning_trace.append(f"📊 Input: Tekanan Sistolik = {vitals['sbp']} mmHg")
            if "dbp" in vitals:
                patient.memilikiTekananDiastolik = int(vitals["dbp"])
                self.reasoning_trace.append(f"📊 Input: Tekanan Diastolik = {vitals['dbp']} mmHg")
            if "hr" in vitals:
                patient.memilikiDenyutJantung = int(vitals["hr"])
            if "bmi" in vitals:
                patient.memilikiIMT = float(vitals["bmi"])
                self.reasoning_trace.append(f"📊 Input: BMI = {vitals['bmi']} kg/m²")
            if "weight" in vitals:
                patient.memilikiBeratBadan = float(vitals["weight"])
            if "height" in vitals:
                patient.memilikiTinggiBadan = float(vitals["height"])
            
            # Set lab results
            labs = data.get("labs", {})
            if "fbg" in labs:
                patient.memilikiGulaDarahPuasa = float(labs["fbg"])
                self.reasoning_trace.append(f"📊 Input: Gula Darah Puasa = {labs['fbg']} mg/dL")
            if "hba1c" in labs:
                patient.memilikiHbA1c = float(labs["hba1c"])
                self.reasoning_trace.append(f"📊 Input: HbA1c = {labs['hba1c']}%")
            if "ldl" in labs:
                patient.memilikiKolesterolLDL = float(labs["ldl"])
                self.reasoning_trace.append(f"📊 Input: LDL = {labs['ldl']} mg/dL")
            if "hdl" in labs:
                patient.memilikiKolesterolHDL = float(labs["hdl"])
            if "total_chol" in labs:
                patient.memilikiKolesterolTotal = float(labs["total_chol"])
            if "triglycerides" in labs:
                patient.memilikiTrigliserida = float(labs["triglycerides"])
            if "ef" in labs:
                patient.memilikiEjectionFraction = float(labs["ef"])
                self.reasoning_trace.append(f"📊 Input: Ejection Fraction = {labs['ef']}%")
            if "troponin" in labs:
                patient.memilikiTroponinI = float(labs["troponin"])
                self.reasoning_trace.append(f"📊 Input: Troponin I = {labs['troponin']} ng/mL")
            if "gfr" in labs:
                patient.memilikiGFR = float(labs["gfr"])
            if "creatinine" in labs:
                patient.memilikiKreatinin = float(labs["creatinine"])
            if "potassium" in labs:
                patient.memilikiKalium = float(labs["potassium"])
            if "bnp" in labs:
                patient.memilikiBNP = float(labs["bnp"])
            if "nt_probnp" in labs:
                patient.memilikiNTproBNP = float(labs["nt_probnp"])
            
            # Set risk scores
            scores = data.get("scores", {})
            if "ascvd" in scores:
                patient.memilikiASCVDScore = float(scores["ascvd"])
                self.reasoning_trace.append(f"📊 Input: ASCVD Score = {scores['ascvd']}%")
            if "cha2ds2vasc" in scores:
                patient.memilikiCHA2DS2VASc = int(scores["cha2ds2vasc"])
            if "hasbled" in scores:
                patient.memilikiHASBLED = int(scores["hasbled"])
            
            # Add symptoms
            symptoms = data.get("symptoms", [])
            symptom_map = {
                "nyeri_dada": "NyeriDada_Instance",
                "sesak_napas": "SesakNapas_Instance",
                "edema": "EdemaPerifer_Instance",
                "kelelahan": "Kelelahan_Instance",
                "pusing": "Pusing_Instance",
                "orthopnea": "Orthopnea_Instance",
                "palpitasi": "Palpitasi_Instance"
            }
            for symptom in symptoms:
                if symptom in symptom_map:
                    symptom_ind = self.onto[symptom_map[symptom]]
                    if symptom_ind:
                        patient.memilikiGejala.append(symptom_ind)
                        self.reasoning_trace.append(f"📊 Input: Gejala = {symptom}")
            
            # Add comorbidities
            comorbid = data.get("comorbid", {})
            if comorbid.get("asthma"):
                asma = self.onto.Asma_Instance
                if asma:
                    patient.memiliki.append(asma)
                    self.reasoning_trace.append("📊 Input: Komorbid = Asma")
            if comorbid.get("pregnancy"):
                kehamilan = self.onto.Kehamilan_Instance
                if kehamilan:
                    patient.memiliki.append(kehamilan)
                    self.reasoning_trace.append("📊 Input: Komorbid = Kehamilan")
            if comorbid.get("liver_disease"):
                liver = self.onto.PenyakitHatiAktif_Instance
                if liver:
                    patient.memiliki.append(liver)
                    self.reasoning_trace.append("📊 Input: Komorbid = Penyakit Hati")
            
            # Add history
            history = data.get("history", {})
            if history.get("cad"):
                pjk = self.onto.PJK_Instance
                if pjk:
                    patient.memilikiRiwayat.append(pjk)
                    self.reasoning_trace.append("📊 Input: Riwayat = CAD")
            if history.get("smoking"):
                merokok_instance = self.onto.Merokok_Instance
                if merokok_instance:
                    patient.memiliki.append(merokok_instance)
                    self.reasoning_trace.append("📊 Input: Riwayat = Merokok")
        
        return patient_id
    
    def run_inference(self):
        """Run Pellet reasoner to infer new facts."""
        self.reasoning_trace.append("\n🧠 Menjalankan Pellet Reasoner...")
        
        try:
            with self.onto:
                sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
            self.reasoning_trace.append("✅ Reasoning selesai")
            return True
        except Exception as e:
            self.reasoning_trace.append(f"❌ Error: {str(e)}")
            return False
    
    def get_inferred_diagnoses(self, patient_id: str) -> list:
        """Get all inferred diagnoses for a patient - reads from ontology annotations."""
        patient = self.onto[patient_id]
        if not patient:
            return []
        
        diagnoses = []
        
        # Get patient conditions via memiliki property
        patient_conditions = list(patient.memiliki)
        
        for cond in patient_conditions:
            cond_name = cond.name if hasattr(cond, 'name') else str(cond)
            
            # Get the class of this condition
            cond_classes = cond.is_a if hasattr(cond, 'is_a') else []
            
            # Read annotations from the class or instance
            display_name = cond_name  # default
            severity = "Ringan"  # default
            icd10 = None
            description = None
            
            # Try to get annotations from the class
            for cls in cond_classes:
                if hasattr(cls, 'name'):
                    # Check if this class has annotations
                    cls_obj = self.onto[cls.name]
                    if cls_obj:
                        # Read from ontology annotations
                        if hasattr(cls_obj, 'hasDisplayName') and cls_obj.hasDisplayName:
                            display_name = cls_obj.hasDisplayName[0] if isinstance(cls_obj.hasDisplayName, list) else cls_obj.hasDisplayName
                        if hasattr(cls_obj, 'hasSeverityLevel') and cls_obj.hasSeverityLevel:
                            severity = cls_obj.hasSeverityLevel[0] if isinstance(cls_obj.hasSeverityLevel, list) else cls_obj.hasSeverityLevel
                        if hasattr(cls_obj, 'hasICD10Code') and cls_obj.hasICD10Code:
                            icd10 = cls_obj.hasICD10Code[0] if isinstance(cls_obj.hasICD10Code, list) else cls_obj.hasICD10Code
                        if hasattr(cls_obj, 'hasDescription') and cls_obj.hasDescription:
                            description = cls_obj.hasDescription[0] if isinstance(cls_obj.hasDescription, list) else cls_obj.hasDescription
                        break
            
            # If no class annotations, try from instance name pattern
            if display_name == cond_name:
                # Extract display name from instance name (remove _Instance suffix)
                clean_name = cond_name.replace('_Instance', '').replace('_', ' ')
                display_name = clean_name
                
                # Try to find the class and get annotations
                class_name = cond_name.replace('_Instance', '')
                cls_obj = self.onto[class_name]
                if cls_obj:
                    if hasattr(cls_obj, 'hasDisplayName') and cls_obj.hasDisplayName:
                        display_name = cls_obj.hasDisplayName[0] if isinstance(cls_obj.hasDisplayName, list) else cls_obj.hasDisplayName
                    if hasattr(cls_obj, 'hasSeverityLevel') and cls_obj.hasSeverityLevel:
                        severity = cls_obj.hasSeverityLevel[0] if isinstance(cls_obj.hasSeverityLevel, list) else cls_obj.hasSeverityLevel
                    if hasattr(cls_obj, 'hasICD10Code') and cls_obj.hasICD10Code:
                        icd10 = cls_obj.hasICD10Code[0] if isinstance(cls_obj.hasICD10Code, list) else cls_obj.hasICD10Code
                    if hasattr(cls_obj, 'hasDescription') and cls_obj.hasDescription:
                        description = cls_obj.hasDescription[0] if isinstance(cls_obj.hasDescription, list) else cls_obj.hasDescription
            
            diagnosis_entry = {
                "name": display_name,
                "class": cond_name.replace('_Instance', ''),
                "severity": severity,
                "source": "SWRL Inference (from Ontology)"
            }
            if icd10:
                diagnosis_entry["icd10"] = icd10
            if description:
                diagnosis_entry["description"] = description
                
            diagnoses.append(diagnosis_entry)
            self.reasoning_trace.append(f"🔍 Inferred: {display_name} (Severity: {severity})")
        
        return diagnoses
    
    def get_recommended_medications(self, patient_id: str) -> list:
        """Get all recommended medications for a patient - reads from ontology annotations."""
        patient = self.onto[patient_id]
        if not patient:
            return []
        
        medications = []
        
        # Get medications via memerlukan property
        required_meds = list(patient.memerlukan)
        
        for med in required_meds:
            med_name = med.name if hasattr(med, 'name') else str(med)
            
            # Read annotations from ontology
            drug_class = "Unknown"
            dose = "As prescribed"
            frequency = "As directed"
            display_name = med_name
            
            # Try to get annotations from the medication individual
            if hasattr(med, 'hasDrugClass') and med.hasDrugClass:
                drug_class = med.hasDrugClass[0] if isinstance(med.hasDrugClass, list) else med.hasDrugClass
            if hasattr(med, 'hasDose') and med.hasDose:
                dose = med.hasDose[0] if isinstance(med.hasDose, list) else med.hasDose
            if hasattr(med, 'hasFrequency') and med.hasFrequency:
                frequency = med.hasFrequency[0] if isinstance(med.hasFrequency, list) else med.hasFrequency
            if hasattr(med, 'hasDisplayName') and med.hasDisplayName:
                display_name = med.hasDisplayName[0] if isinstance(med.hasDisplayName, list) else med.hasDisplayName
            
            # Read description from ontology
            description = None
            if hasattr(med, 'hasDescription') and med.hasDescription:
                description = med.hasDescription[0] if isinstance(med.hasDescription, list) else med.hasDescription
            
            med_entry = {
                "name": display_name,
                "class": drug_class,
                "dose": dose,
                "frequency": frequency,
                "source": "SWRL Inference (from Ontology)"
            }
            if description:
                med_entry["description"] = description
            
            medications.append(med_entry)
            self.reasoning_trace.append(f"💊 Medication: {display_name} ({drug_class})")
        
        return medications
    
    def get_contraindications(self, patient_id: str) -> list:
        """Get contraindicated medications for a patient."""
        patient = self.onto[patient_id]
        if not patient:
            return []
        
        contraindications = []
        
        contra_reasons = {
            "BetaBlocker": {"Asma_Instance": "Pasien memiliki Asma - Beta Blocker dapat memperburuk bronkospasme"},
            "ACEInhibitor": {"Kehamilan_Instance": "Pasien hamil - ACE Inhibitor teratogenik"},
            "Statin": {"PenyakitHatiAktif_Instance": "Pasien memiliki penyakit hati aktif"},
            "Metformin": {"CKD_Stage4": "eGFR < 30 - risiko asidosis laktat"},
            "Spironolactone": {"Hyperkalemia": "Kalium > 5.5 - risiko hiperkalemia berat"}
        }
        
        # Check kontraindikasiPada property
        contra_meds = list(patient.kontraindikasiPada)
        
        for med in contra_meds:
            med_name = med.name if hasattr(med, 'name') else str(med)
            reason = "Kontraindikasi berdasarkan kondisi pasien"
            
            # Try to find specific reason
            for drug_class, reasons in contra_reasons.items():
                if drug_class in med_name or (hasattr(med, 'is_a') and any(drug_class in str(t) for t in med.is_a)):
                    for cond, msg in reasons.items():
                        reason = msg
                        break
            
            contraindications.append({
                "drug": med_name,
                "reason": reason,
                "source": "SWRL Contraindication Rule"
            })
            self.reasoning_trace.append(f"⚠️ Kontraindikasi: {med_name} - {reason}")
        
        return contraindications
    
    def get_risk_category(self, patient_id: str) -> dict:
        """Get the risk category for a patient."""
        patient = self.onto[patient_id]
        if not patient:
            return {"category": "Unknown", "score": None}
        
        category = "Unknown"
        score = None
        
        # Get from memilikiKategoriRisiko
        risk_cat = patient.memilikiKategoriRisiko
        if risk_cat:
            # FunctionalProperty returns single value, not list
            cat_name = risk_cat.name if hasattr(risk_cat, 'name') else str(risk_cat)
            
            cat_map = {
                "RisikoRendah": "Risiko Rendah",
                "RisikoBorderline": "Risiko Borderline",
                "RisikoSedang": "Risiko Sedang",
                "RisikoTinggi": "Risiko Tinggi",
                "RisikoSangatTinggi": "Risiko Sangat Tinggi"
            }
            
            for key, display in cat_map.items():
                if key in cat_name:
                    category = display
                    self.reasoning_trace.append(f"📊 Risk Category: {display}")
                    break
        
        # Get ASCVD score (FunctionalProperty returns single value)
        if patient.memilikiASCVDScore:
            score = patient.memilikiASCVDScore
        
        return {"category": category, "score": score}
    
    def get_severity(self, patient_id: str) -> str:
        """Get the severity level for a patient."""
        patient = self.onto[patient_id]
        if not patient:
            return "Unknown"
        
        severity = "Ringan"  # default
        
        sev = patient.memilikiTingkatKeparahan
        if sev:
            # FunctionalProperty returns single value, not list
            s_name = sev.name if hasattr(sev, 'name') else str(sev)
            
            sev_map = {
                "Kritis": "Kritis",
                "Berat": "Berat",
                "Sedang": "Sedang",
                "Ringan": "Ringan"
            }
            
            for key, display in sev_map.items():
                if key in s_name:
                    severity = display
                    break
        
        return severity
    
    def get_reasoning_trace(self) -> list:
        """Get the reasoning trace."""
        return self.reasoning_trace
    
    def get_parameter_descriptions(self) -> dict:
        """Get descriptions for input parameters from ontology DatatypeProperties."""
        descriptions = {}
        
        # Map form field IDs to ontology property names
        field_map = {
            "sbp": "memilikiTekananSistolik",
            "dbp": "memilikiTekananDiastolik",
            "hr": "memilikiDenyutJantung",
            "bmi": "memilikiIMT",
            "fbg": "memilikiGulaDarahPuasa",
            "hba1c": "memilikiHbA1c",
            "ldl": "memilikiLDL",
            "hdl": "memilikiHDL",
            "ef": "memilikiEF",
            "troponin": "memilikiTroponinI",
            "gfr": "memilikiGFR",
            "potassium": "memilikiKalium",
            "ascvd": "memilikiASCVDScore",
            "age": "memilikiUsia",
            "gender": "memilikiJenisKelamin",
        }
        
        for field_id, prop_name in field_map.items():
            prop = self.onto[prop_name]
            if prop:
                # Get rdfs:label and rdfs:comment
                label = None
                comment = None
                
                if hasattr(prop, 'label') and prop.label:
                    label = prop.label[0] if isinstance(prop.label, list) else prop.label
                if hasattr(prop, 'comment') and prop.comment:
                    comment = prop.comment[0] if isinstance(prop.comment, list) else prop.comment
                
                descriptions[field_id] = {
                    "label": label or prop_name,
                    "description": comment or "Tidak ada deskripsi"
                }
        
        return descriptions
    
    def get_inferred_recommendations(self, patient_id: str) -> list:
        """Get lifestyle recommendations from SWRL inference via memerlukanRekomendasi property."""
        patient = self.onto[patient_id]
        if not patient:
            return []
        
        recommendations = []
        seen_recs = set()  # Track seen recommendations to avoid duplicates
        
        # Get recommendations from inferred memerlukanRekomendasi property
        patient_recs = list(patient.memerlukanRekomendasi) if hasattr(patient, 'memerlukanRekomendasi') else []
        
        for rec in patient_recs:
            rec_name = rec.name if hasattr(rec, 'name') else str(rec)
            
            # Skip if already seen
            if rec_name in seen_recs:
                continue
            seen_recs.add(rec_name)
            
            display_name = rec_name
            description = None
            priority = 99
            cat_name = "Umum"
            
            # Read annotations from the recommendation individual
            if hasattr(rec, 'hasDisplayName') and rec.hasDisplayName:
                display_name = rec.hasDisplayName[0] if isinstance(rec.hasDisplayName, list) else rec.hasDisplayName
            if hasattr(rec, 'hasDescription') and rec.hasDescription:
                description = rec.hasDescription[0] if isinstance(rec.hasDescription, list) else rec.hasDescription
            if hasattr(rec, 'hasCategory') and rec.hasCategory:
                cat_name = rec.hasCategory[0] if isinstance(rec.hasCategory, list) else rec.hasCategory
            if hasattr(rec, 'hasPriority') and rec.hasPriority:
                priority = rec.hasPriority[0] if isinstance(rec.hasPriority, list) else rec.hasPriority
            
            rec_entry = {
                "name": display_name,
                "category": cat_name,
                "priority": priority,
                "source": "SWRL Inference (from Ontology)"
            }
            if description:
                rec_entry["description"] = description
            
            recommendations.append(rec_entry)
            self.reasoning_trace.append(f"💡 Rekomendasi: {display_name} ({cat_name})")
        
        # Sort by category and priority
        recommendations.sort(key=lambda x: (x["category"], x["priority"]))
        
        return recommendations
    
    def get_lifestyle_recommendations(self, diagnoses: list, has_smoking: bool = False) -> list:
        """Get lifestyle recommendations from ontology based on diagnoses."""
        recommendations = []
        
        # Map diagnosis categories to recommendation classes
        category_map = {
            "hipertensi": "RekomendasiTekananDarah",
            "tekanan darah": "RekomendasiTekananDarah",
            "diabetes": "RekomendasiGulaDarah",
            "prediabetes": "RekomendasiGulaDarah",
            "gula darah": "RekomendasiGulaDarah",
            "dislipidemia": "RekomendasiKolesterol",
            "kolesterol": "RekomendasiKolesterol",
            "ldl": "RekomendasiKolesterol",
            "obesitas": "RekomendasiBeratBadan",
            "overweight": "RekomendasiBeratBadan",
            "gagal jantung": "RekomendasiGagalJantung",
            "hfref": "RekomendasiGagalJantung",
            "hfpef": "RekomendasiGagalJantung",
            "hfmref": "RekomendasiGagalJantung",
        }
        
        # Find which recommendation categories apply
        needed_categories = set()
        needed_categories.add("RekomendasiUmum")  # Always include
        
        for diag in diagnoses:
            diag_name = diag.get("name", "").lower()
            for keyword, category in category_map.items():
                if keyword in diag_name:
                    needed_categories.add(category)
        
        if has_smoking:
            needed_categories.add("RekomendasiBerhentiMerokok")
        
        # Read recommendation individuals from ontology
        for category in needed_categories:
            cat_class = self.onto[category]
            if cat_class:
                for ind in cat_class.instances():
                    display_name = ind.name
                    description = None
                    priority = 99
                    cat_name = category.replace("Rekomendasi", "")
                    
                    if hasattr(ind, 'hasDisplayName') and ind.hasDisplayName:
                        display_name = ind.hasDisplayName[0] if isinstance(ind.hasDisplayName, list) else ind.hasDisplayName
                    if hasattr(ind, 'hasDescription') and ind.hasDescription:
                        description = ind.hasDescription[0] if isinstance(ind.hasDescription, list) else ind.hasDescription
                    if hasattr(ind, 'hasCategory') and ind.hasCategory:
                        cat_name = ind.hasCategory[0] if isinstance(ind.hasCategory, list) else ind.hasCategory
                    if hasattr(ind, 'hasPriority') and ind.hasPriority:
                        priority = ind.hasPriority[0] if isinstance(ind.hasPriority, list) else ind.hasPriority
                    
                    rec_entry = {
                        "name": display_name,
                        "category": cat_name,
                        "priority": priority,
                        "source": "Ontology"
                    }
                    if description:
                        rec_entry["description"] = description
                    
                    recommendations.append(rec_entry)
        
        # Sort by category and priority
        recommendations.sort(key=lambda x: (x["category"], x["priority"]))
        
        return recommendations
    
    def cleanup_patient(self, patient_id: str):
        """Remove patient individual from ontology."""
        patient = self.onto[patient_id]
        if patient:
            with self.onto:
                destroy_entity(patient)
    
    def diagnose(self, data: dict) -> dict:
        """
        Complete diagnosis workflow.
        
        Args:
            data: Patient data dictionary
            
        Returns:
            Complete diagnosis result
        """
        # Create patient
        patient_id = self.create_patient(data)
        
        # Run inference
        self.run_inference()
        
        # Get results
        diagnoses = self.get_inferred_diagnoses(patient_id)
        medications = self.get_recommended_medications(patient_id)
        contraindications = self.get_contraindications(patient_id)
        risk = self.get_risk_category(patient_id)
        severity = self.get_severity(patient_id)
        reasoning = self.get_reasoning_trace()
        
        # Get lifestyle recommendations from SWRL inference (primary)
        lifestyle_recommendations = self.get_inferred_recommendations(patient_id)
        
        # Fallback to hardcoded method if SWRL didn't produce recommendations
        if not lifestyle_recommendations:
            has_smoking = data.get('history', {}).get('smoking', False)
            lifestyle_recommendations = self.get_lifestyle_recommendations(diagnoses, has_smoking)
        
        # Check for emergency
        emergency = any(d.get("severity") == "Kritis" for d in diagnoses)
        
        # Cleanup (optional - keep for history)
        # self.cleanup_patient(patient_id)
        
        return {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat(),
            "emergency": emergency,
            "diagnoses": diagnoses,
            "medications": medications,
            "contraindications": contraindications,
            "risk_category": risk["category"],
            "ascvd_score": risk["score"],
            "severity": severity,
            "lifestyle_recommendations": lifestyle_recommendations,
            "reasoning_trace": reasoning,
            "rules_fired": len([r for r in reasoning if "Inferred" in r or "Medication" in r or "Rekomendasi" in r])
        }
