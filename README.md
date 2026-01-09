# CVD Expert System

Sistem pakar berbasis ontologi untuk diagnosis penyakit kardiovaskular menggunakan OWL 2 dan SWRL Rules.

## Live Demo

Aplikasi dapat diakses secara online di:

https://kbr-cvd-webapp.azurewebsites.net/

Versi web ini di-host pada Microsoft Azure Web App dan menggunakan Azure Cosmos DB untuk menyimpan riwayat diagnosis.

## Tentang

Sistem ini dapat mendiagnosis kondisi kardiovaskular berdasarkan data klinis pasien:
- Hipertensi (Stage 1, 2, Krisis)
- Diabetes Mellitus (Prediabetes, Tipe 2)
- Gagal Jantung (HFrEF, HFmrEF, HFpEF)
- Dislipidemia
- Chronic Kidney Disease (Stage 1-5)

Selain diagnosis, sistem juga memberikan rekomendasi obat, mendeteksi kontraindikasi, dan menyediakan kalkulator klinis (BMI, eGFR, ASCVD Risk, CHA2DS2-VASc, HAS-BLED).

## Teknologi

- **Backend:** Flask + Owlready2
- **Reasoner:** Pellet (untuk inferensi SWRL)
- **Ontologi:** OWL 2 SROIQ(D) dengan 149 kelas dan 65 SWRL rules
- **Frontend:** HTML, CSS, JavaScript

## Instalasi

```bash
git clone https://github.com/shizukuuzz/cvd-expert-system-fix.git
cd cvd-expert-system-fix
pip install -r requirements.txt
python app.py
```

Buka http://localhost:5000

**Catatan:** Memerlukan Java 11+ untuk Pellet Reasoner.

## Struktur

```
├── app.py                  # Flask backend
├── cvd_sroiq_complete.owl  # Ontologi
├── services/
│   ├── knowledge_service.py
│   └── sparql_service.py
├── static/                 # Frontend
└── azure/                  # Konfigurasi deployment Azure
```

## Referensi

Sistem dibangun berdasarkan pedoman klinis: JNC 8, ADA 2024, ACC/AHA, ESC, dan KDIGO.

## Lisensi

MIT License

## Disclaimer

Sistem ini untuk tujuan edukasi. Hasil diagnosis tidak menggantikan konsultasi dengan dokter.
