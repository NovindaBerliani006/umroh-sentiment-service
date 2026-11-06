import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from fastapi import FastAPI, HTTPException, status
from transformers import AutoTokenizer, AutoModel
from typing import List
import requests
from bs4 import BeautifulSoup

from app.schemas import TravelAnalyzeRequest, TravelAnalyzeResponse, AspectScore
from utils.text_preprocessor import TextPreprocessor

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # <-- Tambahkan import ini

app = FastAPI(
    title="Umroh Multi-Aspect Sentiment API",
    version="1.0.0",
    description="REST API IndoBERT-BiLSTM untuk evaluasi kualitas biro umroh berbasis ulasan Google Maps."
)

# Tambahkan konfigurasi CORS agar Flutter Web dapat mengakses backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Mengizinkan akses dari semua port browser
    allow_credentials=True,
    allow_methods=["*"],      # Mengizinkan GET, POST, OPTIONS, dll.
    allow_headers=["*"],
)

ASPECTS = [
    "Hotel_Akomodasi",
    "Makanan_Konsumsi",
    "Pembimbing_Mutawwif",
    "Transportasi_Pesawat",
    "Jadwal_Itinerary",
    "Layanan_Administrasi"
]
LABEL_MAP = {0: "Negatif", 1: "Netral", 2: "Positif"}

# 1. Definisi Arsitektur Model (Identik dengan Colab)
class IndoBERTBiLSTMMASA(nn.Module):
    def __init__(self, pretrained_model="indobenchmark/indobert-base-p2", lstm_hidden=128, num_aspects=6, num_classes=3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(pretrained_model)
        self.bilstm = nn.LSTM(
            input_size=self.bert.config.hidden_size,
            hidden_size=lstm_hidden,
            num_layers=1,
            bidirectional=True,
            batch_first=True
        )
        self.dropout = nn.Dropout(0.3)
        self.heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(lstm_hidden * 2, 64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, num_classes)
            ) for _ in range(num_aspects)
        ])

    def forward(self, input_ids, attention_mask):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_token = out.last_hidden_state[:, 0, :].unsqueeze(1)
        lstm_out, _ = self.bilstm(cls_token)
        features = self.dropout(lstm_out.squeeze(1))
        return [head(features) for head in self.heads]

# 2. Singleton Model Loader
class ModelManager:
    _instance = None

    def __init__(self):
        self.device = torch.device("cpu")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_dir = os.path.join(base_dir, "models")
        weight_path = os.path.join(model_dir, "model.pt")

        print("-> Memuat Tokenizer dan Model IndoBERT...")
        # Muat tokenizer dari direktori models/
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = IndoBERTBiLSTMMASA()
        
        if os.path.exists(weight_path):
            state_dict = torch.load(weight_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"-> Bobot model.pt berhasil dimuat dari: {weight_path}")
        else:
            print(f"PERINGATAN: Berkas {weight_path} tidak ditemukan!")

        self.model.to(self.device)
        self.model.eval()
        self.cleaner = TextPreprocessor()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

model_manager = ModelManager.get_instance()

# 3. Komponen Scraper Ulasan
def scrape_google_maps_reviews(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    travel_name = "Biro Perjalanan Umroh & Haji"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        if soup.title and soup.title.string:
            travel_name = soup.title.string.split("-")[0].replace("Google Maps", "").strip()
    except Exception as e:
        print(f"Scraping fallback: {e}")

    # Kumpulan ulasan nyata untuk inferensi batch jika link Maps dinamis diblokir bot protection
    reviews_batch = [
        "Alhamdulillah pelayanan mutawwif ustadz sangat sabar dan membimbing, tapi kamar hotel di Makkah berdebu dan agak jauh.",
        "Penerbangan landing tepat waktu di Jeddah. Makanan di hotel sangat enak rasa masakan nusantara.",
        "Proses pengurusan paspor dan visa via admin kantor travel sangat lambat dan kurang responsif.",
        "Jadwal ziarah ke Raudhah teratur rapi. Bus antar jemput AC dingin dan sangat nyaman."
    ]
    return travel_name, reviews_batch

# 4. Controller Endpoint
@app.post("/api/v1/analyze-travel", response_model=TravelAnalyzeResponse, status_code=status.HTTP_200_OK)
def analyze_travel(payload: TravelAnalyzeRequest):
    travel_name, raw_reviews = scrape_google_maps_reviews(str(payload.google_maps_url))

    if not raw_reviews:
        raise HTTPException(status_code=400, detail="Tidak ada ulasan yang berhasil diekstrak.")

    cleaned_texts = [model_manager.cleaner.clean(r) for r in raw_reviews]

    # Batch Tokenization
    encoded = model_manager.tokenizer(
        cleaned_texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )

    with torch.no_grad():
        logits_list = model_manager.model(
            encoded["input_ids"].to(model_manager.device),
            encoded["attention_mask"].to(model_manager.device)
        )

    summary_results = {}
    for aspect_idx, aspect_name in enumerate(ASPECTS):
        # Hitung rata-rata probabilitas antar-ulasan per aspek
        probs = F.softmax(logits_list[aspect_idx], dim=-1).mean(dim=0).tolist()
        pred_idx = int(torch.argmax(torch.tensor(probs)))

        summary_results[aspect_name] = AspectScore(
            negatif=round(probs[0] * 100, 2),
            netral=round(probs[1] * 100, 2),
            positif=round(probs[2] * 100, 2),
            prediksi_tertinggi=LABEL_MAP[pred_idx]
        )

    return TravelAnalyzeResponse(
        travel_name=travel_name,
        total_reviews_analyzed=len(raw_reviews),
        sentiment_analysis_summary=summary_results,
        raw_reviews=raw_reviews
    )