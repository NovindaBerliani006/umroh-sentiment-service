# Umrah & Hajj Aspect-Based Sentiment Analysis (ABSA)

Sistem evaluasi reputasi biro perjalanan Umroh & Haji berbasis Aspect-Based Sentiment Analysis (ABSA) menggunakan arsitektur hybrid **IndoBERT-BiLSTM** dengan skema penanganan ketidakseimbangan kelas (*Inverse Class Weighting*), backend **FastAPI**, dan antarmuka **Flutter**.

## 6 Aspek Evaluasi
1. Hotel & Akomodasi
2. Makanan & Konsumsi
3. Pembimbing & Mutawwif
4. Transportasi & Pesawat
5. Jadwal & Itinerary
6. Layanan & Administrasi

## Struktur Direktori
- `app/`: Layanan backend REST API menggunakan FastAPI.
- `models/`: Penyimpanan konfigurasi tokenizer dan arsitektur model.
- `utils/`: Modul pra-pemrosesan teks ulasan dan normalisasi slang.
- `mobile/`: Aplikasi mobile berbasis Flutter.

## Menjalankan Backend (FastAPI)
```bash
# Aktifkan virtual environment
.\venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt

# Jalankan server API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000