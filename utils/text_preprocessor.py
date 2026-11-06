import re
import unicodedata

class TextPreprocessor:
    def __init__(self):
        self.slang_map = {
            "bgt": "banget", "dgn": "dengan", "yg": "yang", "sy": "saya",
            "tdk": "tidak", "gak": "tidak", "nggak": "tidak", "pesewat": "pesawat",
            "mutawif": "mutawwif", "itinarary": "itinerary", "itinerari": "itinerary",
            "rekomen": "rekomendasi", "delay": "terlambat", "fast respon": "respons cepat",
            "tp": "tapi", "sdh": "sudah", "bintang": "bintang", "kamar": "kamar"
        }

    def clean(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        # 1. Normalisasi unicode dan case folding
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = text.lower()
        # 2. Hapus tautan URL
        text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
        # 3. Hapus karakter non-alfanumerik/emoji
        text = re.sub(r'[^\w\s]', ' ', text)
        # 4. Hapus angka
        text = re.sub(r'\d+', ' ', text)
        # 5. Normalisasi kata tidak baku
        tokens = [self.slang_map.get(w, w) for w in text.split()]
        # 6. Rapikan spasi ganda
        return " ".join(tokens).strip()