# 🫀 CVD Expert System - Sistem Pakar Penyakit Kardiovaskular

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![OWL](https://img.shields.io/badge/OWL-SROIQ(D)-orange.svg)](https://www.w3.org/TR/owl2-overview/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistem pakar berbasis ontologi untuk diagnosis, rekomendasi obat, dan deteksi kontraindikasi penyakit kardiovaskular menggunakan **OWL 2 SROIQ(D)** dengan inferensi **SWRL Rules** dan **Pellet Reasoner**.

![CVD Expert System](https://img.shields.io/badge/Domain-Healthcare-red)
![Ontology](https://img.shields.io/badge/Ontology-149%20Classes-blue)
![SWRL](https://img.shields.io/badge/SWRL-65%20Rules-green)

---

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Struktur Repository](#-struktur-repository)
- [Instalasi & Setup](#-instalasi--setup)
- [Penggunaan](#-penggunaan)
- [API Endpoints](#-api-endpoints)
- [Ontologi CVD](#-ontologi-cvd)
- [Kalkulator Klinis](#-kalkulator-klinis)
- [Deployment Azure](#-deployment-azure-opsional)
- [Teknologi](#-teknologi)
- [Referensi Klinis](#-referensi-klinis)
- [Lisensi](#-lisensi)

---

## ✨ Fitur Utama

### 🔬 Diagnosis Otomatis
- Klasifikasi **Hipertensi** (Stage 1, Stage 2, Krisis) berdasarkan JNC 8
- Deteksi **Diabetes** (Prediabetes, DM Tipe 2) berdasarkan ADA 2024
- Staging **Gagal Jantung** (HFrEF, HFmrEF, HFpEF) berdasarkan ACC/AHA
- Evaluasi **Dislipidemia** berdasarkan ACC/AHA 2018
- Staging **CKD** (Stage 1-5) berdasarkan KDIGO 2024

### 💊 Rekomendasi Obat
- Rekomendasi berbasis pedoman klinis terkini
- Deteksi **kontraindikasi** otomatis
- Pertimbangan komorbiditas (multi-disease)

### 🧮 Kalkulator Klinis
| Kalkulator | Fungsi | Referensi |
|------------|--------|-----------|
| **BMI** | Indeks Massa Tubuh | WHO |
| **eGFR** | Estimasi GFR (CKD-EPI 2021) | KDIGO |
| **ASCVD** | Risiko Kardiovaskular 10 Tahun | ACC/AHA PCE |
| **CHA₂DS₂-VASc** | Risiko Stroke pada AF | ESC |
| **HAS-BLED** | Risiko Perdarahan | ESC |

### 🔄 Penalaran Semantik
- **Pellet Reasoner** untuk inferensi OWL
- **65 SWRL Rules** untuk penalaran klinis
- **Property Chains** untuk inferensi risiko otomatis

---

## 🏗 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (HTML/CSS/JS)                   │
│                    - Form Input Pasien                       │
│                    - Kalkulator Klinis                       │
│                    - Visualisasi Hasil                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Backend (app.py)                   │
│                    - REST API Endpoints                      │
│                    - Request Handling                        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│   Knowledge Service      │    │    SPARQL Service        │
│   (Owlready2 + Pellet)   │    │   (Apache Jena Fuseki)   │
│   - Load Ontology        │    │   - Triple Store         │
│   - Run SWRL Rules       │    │   - SPARQL Queries       │
│   - Inference Engine     │    │   - Data Persistence     │
└──────────────────────────┘    └──────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Ontology (cvd_sroiq_complete.owl)            │
│                 - 149 Classes                                │
│                 - 23 Object Properties                       │
│                 - 34 Data Properties                         │
│                 - 95 Individuals                             │
│                 - 65 SWRL Rules                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktur Repository

```
cvd-expert-system/
├── app.py                      # Flask backend utama
├── requirements.txt            # Dependencies Python
├── cvd_sroiq_complete.owl      # Ontologi OWL 2 SROIQ(D)
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── knowledge_service.py    # Ontology & reasoning service
│   └── sparql_service.py       # SPARQL query service
│
├── static/                     # Frontend files
│   ├── index.html              # Main UI
│   ├── script.js               # JavaScript logic
│   └── style.css               # Styling
│
└── azure/                      # Azure deployment (optional)
    ├── app_deploy.py           # Azure Web App version
    ├── Dockerfile              # Container definition
    ├── requirements.txt        # Azure dependencies
    ├── cvd_sroiq_complete.owl  # Ontology copy
    ├── local.settings.json.example  # Config template
    ├── services/
    │   └── knowledge_service.py
    └── static/
        ├── index.html
        ├── script.js
        └── style.css
```

---

## 🚀 Instalasi & Setup

### Prasyarat
- **Python 3.9+**
- **Java 11+** (untuk Pellet Reasoner)
- **Apache Jena Fuseki 5.x** (opsional, untuk SPARQL)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/USERNAME/cvd-expert-system.git
cd cvd-expert-system
```

### 2️⃣ Buat Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Verifikasi Java

```bash
java -version
# Pastikan Java 11+ terinstall
```

### 5️⃣ Jalankan Aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di: **http://localhost:5000**

---

## 📖 Penggunaan

### Web Interface

1. Buka **http://localhost:5000** di browser
2. Isi data pasien:
   - Nama, Usia, Jenis Kelamin
   - Tekanan Darah (Sistolik/Diastolik)
   - Gula Darah Puasa, HbA1c
   - Profil Lipid (LDL, HDL, Trigliserida)
   - Ejection Fraction (jika ada)
   - Kondisi penyerta (Asma, Kehamilan, dll)
3. Klik **"Diagnosa"**
4. Lihat hasil:
   - Diagnosis yang terdeteksi
   - Rekomendasi obat
   - Kontraindikasi
   - Rekomendasi gaya hidup

### Kalkulator Klinis

Gunakan tab kalkulator untuk menghitung:
- **BMI**: Masukkan berat (kg) dan tinggi (cm)
- **eGFR**: Masukkan kreatinin, usia, jenis kelamin
- **ASCVD Risk**: Masukkan profil risiko lengkap
- **CHA₂DS₂-VASc**: Checklist faktor risiko stroke
- **HAS-BLED**: Checklist faktor risiko bleeding

---

## 🔌 API Endpoints

### Diagnosis

```http
POST /api/diagnose
Content-Type: application/json

{
  "nama": "Budi Santoso",
  "usia": 55,
  "jenis_kelamin": "male",
  "tekanan_sistolik": 150,
  "tekanan_diastolik": 95,
  "gula_darah_puasa": 140,
  "hba1c": 7.2,
  "kolesterol_ldl": 160,
  "kolesterol_hdl": 35,
  "trigliserida": 200,
  "ejection_fraction": 45,
  "merokok": true,
  "memiliki_asma": false,
  "sedang_hamil": false
}
```

**Response:**
```json
{
  "success": true,
  "patient_id": "patient_12345",
  "diagnoses": [
    "HipertensiStage2",
    "DiabetesTipe2",
    "Dislipidemia"
  ],
  "medications": [
    "Amlodipine",
    "Lisinopril",
    "Metformin",
    "Atorvastatin"
  ],
  "contraindications": [],
  "lifestyle_recommendations": [
    "Batasi garam <2g/hari",
    "Diet DASH",
    "Olahraga aerobik 150 menit/minggu"
  ],
  "reasoning_time": 1.5
}
```

### Kalkulator

```http
POST /api/calculate/bmi
Content-Type: application/json

{
  "weight": 85,
  "height": 170
}
```

```http
POST /api/calculate/egfr
Content-Type: application/json

{
  "creatinine": 1.2,
  "age": 55,
  "gender": "male"
}
```

### Health Check

```http
GET /api/health
```

---

## 🧬 Ontologi CVD

### Statistik Ontologi

| Komponen | Jumlah | Deskripsi |
|----------|--------|-----------|
| **Classes** | 149 | Hirarki penyakit, obat, gejala |
| **Object Properties** | 23 | Relasi antar entitas |
| **Data Properties** | 34 | Atribut numerik pasien |
| **Individuals** | 95 | Instance obat, kondisi, rekomendasi |
| **SWRL Rules** | 65 | Aturan inferensi klinis |

### Hierarki Kelas Utama

```
Thing
├── Pasien
├── Penyakit
│   ├── PenyakitKardiovaskular
│   │   ├── Hipertensi (Stage1, Stage2, Krisis)
│   │   ├── GagalJantung (HFrEF, HFmrEF, HFpEF)
│   │   ├── AtrialFibrilasi
│   │   └── PenyakitJantungKoroner
│   ├── DiabetesMellitus (Prediabetes, Tipe1, Tipe2)
│   ├── Dislipidemia
│   └── PenyakitGinjal (CKD Stage 1-5)
├── Obat
│   ├── Antihipertensi (ACEi, ARB, CCB, BB, Diuretik)
│   ├── Antidiabetes (Metformin, SGLT2i, DPP4i)
│   ├── Antilipid (Statin)
│   └── Antikoagulan (Warfarin, DOAC)
├── Gejala
├── FaktorRisiko
└── Rekomendasi
```

### Contoh SWRL Rules

**Klasifikasi Hipertensi Stage 2:**
```
Pasien(?p) ∧ memilikiTekananSistolik(?p, ?sbp) ∧ 
swrlb:greaterThanOrEqual(?sbp, 140) → memiliki(?p, HipertensiStage2_Instance)
```

**Kontraindikasi Beta-Blocker pada Asma:**
```
Pasien(?p) ∧ memiliki(?p, Asma_Instance) ∧ 
memerlukan(?p, ?bb) ∧ BetaBlocker(?bb) → kontraindikasiPada(?p, ?bb)
```

---

## 🧮 Kalkulator Klinis

### BMI (Body Mass Index)
```
BMI = Berat (kg) / Tinggi² (m²)

Kategori:
- Underweight: < 18.5
- Normal: 18.5 - 24.9
- Overweight: 25 - 29.9
- Obesitas: ≥ 30
```

### eGFR (CKD-EPI 2021)
```
eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(-1.200) × 0.9938^age × (1.012 jika female)

Dimana:
- κ = 0.7 (female) atau 0.9 (male)
- α = -0.241 (female) atau -0.302 (male)
```

### ASCVD Risk Score
```
Pooled Cohort Equations (ACC/AHA 2013)
- Variabel: Usia, Gender, Race, Total Cholesterol, HDL, SBP, 
  DM status, Smoking status, Hypertension treatment
```

---

## ☁️ Deployment Azure (Opsional)

Folder `azure/` berisi konfigurasi untuk deployment ke Azure Web App.

### Setup Azure

1. **Copy template konfigurasi:**
   ```bash
   cd azure
   cp local.settings.json.example local.settings.json
   ```

2. **Edit `local.settings.json`** dengan kredensial Azure Cosmos DB Anda

3. **Build Docker image:**
   ```bash
   docker build -t cvd-expert-system .
   ```

4. **Push ke Azure Container Registry:**
   ```bash
   az acr login --name <your-registry>
   docker tag cvd-expert-system <your-registry>.azurecr.io/cvd-expert-system:latest
   docker push <your-registry>.azurecr.io/cvd-expert-system:latest
   ```

5. **Deploy ke Azure Web App:**
   ```bash
   az webapp config container set \
     --name <your-webapp> \
     --resource-group <your-rg> \
     --docker-custom-image-name <your-registry>.azurecr.io/cvd-expert-system:latest
   ```

---

## 🛠 Teknologi

| Layer | Teknologi | Versi |
|-------|-----------|-------|
| **Frontend** | HTML5, CSS3, JavaScript | - |
| **Backend** | Flask | 3.0+ |
| **Ontology** | OWL 2 SROIQ(D) | W3C |
| **Reasoner** | Pellet | 2.4 |
| **OWL Library** | Owlready2 | 0.46+ |
| **SPARQL** | Apache Jena Fuseki | 5.x |
| **Container** | Docker | 20+ |
| **Cloud** | Azure Web App, Cosmos DB | - |

---

## 📚 Referensi Klinis

Sistem ini dibangun berdasarkan pedoman klinis terkini:

| Domain | Pedoman | Tahun |
|--------|---------|-------|
| **Hipertensi** | JNC 8, ACC/AHA 2017 | 2014, 2017 |
| **Diabetes** | ADA Standards of Care | 2024 |
| **Gagal Jantung** | ACC/AHA/HFSA, ESC | 2017, 2021 |
| **Dislipidemia** | ACC/AHA Cholesterol | 2018 |
| **CKD** | KDIGO | 2024 |
| **Atrial Fibrilasi** | AHA/ACC/HRS, ESC | 2019, 2020 |
| **ASCVD Risk** | Pooled Cohort Equations | 2013 |

---

## 👥 Kontributor

- **L0223019** - Irfan - Universitas Sebelas Maret

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

## ⚠️ Disclaimer

> **PENTING**: Sistem ini dikembangkan untuk tujuan **edukasi dan penelitian**. 
> Hasil diagnosis dan rekomendasi **TIDAK** menggantikan konsultasi dengan profesional medis.
> Selalu konsultasikan dengan dokter untuk keputusan klinis.

---

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:

1. Fork repository ini
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

---

<p align="center">
  Made with ❤️ for Healthcare AI
</p>
