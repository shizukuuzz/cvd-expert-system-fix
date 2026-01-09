# CVD Expert System

Sistem pakar berbasis ontologi untuk diagnosis dan rekomendasi pengobatan penyakit kardiovaskular. Sistem ini menggunakan OWL 2 SROIQ(D) dengan inferensi SWRL Rules dan Pellet Reasoner.

## Daftar Isi

- [Fitur](#fitur)
- [Arsitektur](#arsitektur)
- [Struktur Folder](#struktur-folder)
- [Instalasi](#instalasi)
- [Penggunaan](#penggunaan)
- [Ontologi](#ontologi)
- [Kalkulator Klinis](#kalkulator-klinis)
- [Deployment Azure](#deployment-azure)
- [Teknologi](#teknologi)
- [Referensi Klinis](#referensi-klinis)
- [Lisensi](#lisensi)

## Fitur

### Diagnosis Otomatis

Sistem dapat mendeteksi kondisi berikut berdasarkan data klinis pasien:

- Hipertensi (Stage 1, Stage 2, Krisis) - klasifikasi berdasarkan JNC 8
- Diabetes Mellitus (Prediabetes, Tipe 2) - berdasarkan kriteria ADA 2024
- Gagal Jantung (HFrEF, HFmrEF, HFpEF) - staging berdasarkan ACC/AHA
- Dislipidemia - evaluasi berdasarkan ACC/AHA 2018
- Chronic Kidney Disease (Stage 1-5) - staging berdasarkan KDIGO 2024

### Rekomendasi Obat

- Rekomendasi berbasis pedoman klinis terkini
- Deteksi kontraindikasi otomatis
- Mempertimbangkan komorbiditas pasien

### Kalkulator Klinis

| Kalkulator | Fungsi | Referensi |
|------------|--------|-----------|
| BMI | Indeks Massa Tubuh | WHO |
| eGFR | Estimasi GFR (CKD-EPI 2021) | KDIGO |
| ASCVD | Risiko Kardiovaskular 10 Tahun | ACC/AHA PCE |
| CHA2DS2-VASc | Risiko Stroke pada Atrial Fibrilasi | ESC |
| HAS-BLED | Risiko Perdarahan | ESC |

### Penalaran Semantik

- Pellet Reasoner untuk inferensi OWL
- 65 SWRL Rules untuk penalaran klinis
- Property Chains untuk inferensi risiko otomatis

## Arsitektur

```
+----------------------------------------------------------+
|                  Frontend (HTML/CSS/JS)                   |
|                  - Form Input Pasien                      |
|                  - Kalkulator Klinis                      |
|                  - Visualisasi Hasil                      |
+----------------------------------------------------------+
                            |
                            v
+----------------------------------------------------------+
|                  Flask Backend (app.py)                   |
|                  - REST API                               |
|                  - Request Handling                       |
+----------------------------------------------------------+
                            |
            +---------------+---------------+
            v                               v
+-------------------------+   +-------------------------+
|   Knowledge Service     |   |    SPARQL Service       |
|   (Owlready2 + Pellet)  |   |   (Apache Jena Fuseki)  |
|   - Load Ontology       |   |   - Triple Store        |
|   - Run SWRL Rules      |   |   - SPARQL Queries      |
|   - Inference Engine    |   |   - Data Persistence    |
+-------------------------+   +-------------------------+
            |                               |
            +---------------+---------------+
                            v
+----------------------------------------------------------+
|              Ontology (cvd_sroiq_complete.owl)            |
|              - 149 Classes                                |
|              - 23 Object Properties                       |
|              - 34 Data Properties                         |
|              - 95 Individuals                             |
|              - 65 SWRL Rules                              |
+----------------------------------------------------------+
```

## Struktur Folder

```
cvd-expert-system/
├── app.py                      # Flask backend utama
├── requirements.txt            # Dependencies Python
├── cvd_sroiq_complete.owl      # Ontologi OWL 2 SROIQ(D)
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── knowledge_service.py    # Ontology dan reasoning service
│   └── sparql_service.py       # SPARQL query service
│
├── static/                     # Frontend files
│   ├── index.html              # Main UI
│   ├── script.js               # JavaScript logic
│   └── style.css               # Styling
│
└── azure/                      # Azure deployment (opsional)
    ├── app_deploy.py           # Azure Web App version
    ├── Dockerfile              # Container definition
    ├── requirements.txt        # Azure dependencies
    ├── cvd_sroiq_complete.owl  # Salinan ontologi
    ├── local.settings.json.example  # Template konfigurasi
    ├── services/
    │   └── knowledge_service.py
    └── static/
        ├── index.html
        ├── script.js
        └── style.css
```

## Instalasi

### Prasyarat

- Python 3.9 atau lebih baru
- Java 11 atau lebih baru (diperlukan untuk Pellet Reasoner)
- Apache Jena Fuseki 5.x (opsional, untuk SPARQL)

### Langkah Instalasi

1. Clone repository ini:

```bash
git clone https://github.com/shizukuuzz/cvd-expert-system-fix.git
cd cvd-expert-system-fix
```

2. Buat virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Pastikan Java sudah terinstall:

```bash
java -version
```

5. Jalankan aplikasi:

```bash
python app.py
```

Aplikasi akan berjalan di http://localhost:5000

## Penggunaan

### Melalui Web Interface

1. Buka http://localhost:5000 di browser
2. Isi data pasien pada form yang tersedia:
   - Nama, Usia, Jenis Kelamin
   - Tekanan Darah (Sistolik/Diastolik)
   - Gula Darah Puasa, HbA1c
   - Profil Lipid (LDL, HDL, Trigliserida)
   - Ejection Fraction (jika ada)
   - Kondisi penyerta (Asma, Kehamilan, dll)
3. Klik tombol "Diagnosa"
4. Sistem akan menampilkan:
   - Diagnosis yang terdeteksi
   - Rekomendasi obat
   - Kontraindikasi (jika ada)
   - Rekomendasi gaya hidup

### Menggunakan Kalkulator

Tab kalkulator menyediakan perhitungan klinis:

- BMI: Masukkan berat badan (kg) dan tinggi badan (cm)
- eGFR: Masukkan kreatinin serum, usia, dan jenis kelamin
- ASCVD Risk: Masukkan profil risiko lengkap
- CHA2DS2-VASc: Pilih faktor risiko stroke yang ada
- HAS-BLED: Pilih faktor risiko perdarahan yang ada

## Ontologi

### Statistik

| Komponen | Jumlah | Keterangan |
|----------|--------|------------|
| Classes | 149 | Hirarki penyakit, obat, gejala |
| Object Properties | 23 | Relasi antar entitas |
| Data Properties | 34 | Atribut numerik pasien |
| Individuals | 95 | Instance obat, kondisi, rekomendasi |
| SWRL Rules | 65 | Aturan inferensi klinis |

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

Klasifikasi Hipertensi Stage 2:
```
Pasien(?p) ^ memilikiTekananSistolik(?p, ?sbp) ^ 
swrlb:greaterThanOrEqual(?sbp, 140) -> memiliki(?p, HipertensiStage2_Instance)
```

Kontraindikasi Beta-Blocker pada Asma:
```
Pasien(?p) ^ memiliki(?p, Asma_Instance) ^ 
memerlukan(?p, ?bb) ^ BetaBlocker(?bb) -> kontraindikasiPada(?p, ?bb)
```

## Kalkulator Klinis

### BMI (Body Mass Index)

```
BMI = Berat (kg) / Tinggi^2 (m^2)

Kategori:
- Underweight: < 18.5
- Normal: 18.5 - 24.9
- Overweight: 25 - 29.9
- Obesitas: >= 30
```

### eGFR (CKD-EPI 2021)

```
eGFR = 142 x min(Scr/k, 1)^a x max(Scr/k, 1)^(-1.200) x 0.9938^age x (1.012 jika female)

Dimana:
- k = 0.7 (female) atau 0.9 (male)
- a = -0.241 (female) atau -0.302 (male)
```

### ASCVD Risk Score

Menggunakan Pooled Cohort Equations (ACC/AHA 2013) dengan variabel:
- Usia, Jenis Kelamin, Ras
- Total Cholesterol, HDL
- Tekanan Darah Sistolik
- Status Diabetes, Merokok
- Pengobatan Hipertensi

## Deployment Azure

Folder `azure/` berisi konfigurasi untuk deployment ke Azure Web App.

### Langkah Deployment

1. Salin template konfigurasi:
```bash
cd azure
cp local.settings.json.example local.settings.json
```

2. Edit `local.settings.json` dengan kredensial Azure Cosmos DB

3. Build Docker image:
```bash
docker build -t cvd-expert-system .
```

4. Push ke Azure Container Registry:
```bash
az acr login --name <nama-registry>
docker tag cvd-expert-system <nama-registry>.azurecr.io/cvd-expert-system:latest
docker push <nama-registry>.azurecr.io/cvd-expert-system:latest
```

5. Deploy ke Azure Web App:
```bash
az webapp config container set \
  --name <nama-webapp> \
  --resource-group <nama-resource-group> \
  --docker-custom-image-name <nama-registry>.azurecr.io/cvd-expert-system:latest
```

## Teknologi

| Layer | Teknologi | Versi |
|-------|-----------|-------|
| Frontend | HTML5, CSS3, JavaScript | - |
| Backend | Flask | 3.0+ |
| Ontology | OWL 2 SROIQ(D) | W3C |
| Reasoner | Pellet | 2.4 |
| OWL Library | Owlready2 | 0.46+ |
| SPARQL | Apache Jena Fuseki | 5.x |
| Container | Docker | 20+ |
| Cloud | Azure Web App, Cosmos DB | - |

## Referensi Klinis

Sistem ini dibangun berdasarkan pedoman klinis berikut:

| Domain | Pedoman | Tahun |
|--------|---------|-------|
| Hipertensi | JNC 8, ACC/AHA | 2014, 2017 |
| Diabetes | ADA Standards of Care | 2024 |
| Gagal Jantung | ACC/AHA/HFSA, ESC | 2017, 2021 |
| Dislipidemia | ACC/AHA Cholesterol | 2018 |
| CKD | KDIGO | 2024 |
| Atrial Fibrilasi | AHA/ACC/HRS, ESC | 2019, 2020 |
| ASCVD Risk | Pooled Cohort Equations | 2013 |

## Kontributor

- L0223019 - Irfan Adi Nugroho - Universitas Sebelas Maret

## Lisensi

Proyek ini menggunakan lisensi MIT. Lihat file [LICENSE](LICENSE) untuk detail.

## Disclaimer

Sistem ini dikembangkan untuk tujuan edukasi dan penelitian. Hasil diagnosis dan rekomendasi yang dihasilkan tidak dapat menggantikan konsultasi dengan tenaga medis profesional. Selalu konsultasikan kondisi kesehatan Anda dengan dokter.

## Kontribusi

Kontribusi terhadap proyek ini sangat diterima. Untuk berkontribusi:

1. Fork repository ini
2. Buat branch untuk fitur baru
3. Commit perubahan
4. Push ke branch
5. Buat Pull Request
