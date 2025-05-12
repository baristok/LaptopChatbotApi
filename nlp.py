import re
import unicodedata
from typing import List, Dict, Any
from difflib import SequenceMatcher

def string_similarity(a: str, b: str) -> float:
    """İki string arasındaki benzerliği hesaplar"""
    return SequenceMatcher(None, a, b).ratio()

# Kelime grupları ve eş anlamlıları
WORD_GROUPS = {
    'oyun': ['gaming', 'oyun', 'game', 'gpu', 'ekran kartı', 'render', 'grafik', 'oyun laptopları'],
    'hafif': ['hafif', 'taşınabilir', 'light', 'ağırlık', 'ultrabook', 'portable', 'hafif laptoplar'],
    'pil': ['pil', 'şarj', 'batarya', 'uzun süre', 'dayanıklı', 'battery', 'pil ömrü'],
    'depolama': ['ssd', 'depolama', 'disk', 'nvme', 'm2', 'storage', 'harddisk'],
    'ekran': ['ekran', 'büyük ekran', 'film', 'görüntü', 'küçük ekran', 'display', 'monitör'],
    'ucuz': ['ucuz', 'bütçe', 'ekonomik', 'uygun fiyat', 'affordable', 'uygun', 'makul'],
    'pahalı': ['pahalı', 'paraya kıyarım', 'premium', 'high-end', 'üst düzey'],
    'ofis': ['ofis', 'iş', 'çalışma', 'business', 'kurumsal'],
    'tasarım': ['tasarım', 'design', 'çizim', 'grafik', 'render'],
    'öğrenci': ['öğrenci', 'student', 'okul', 'üniversite', 'eğitim'],
    'yeni': ['yeni', 'son', 'latest', 'güncel', 'yeni çıkan'],
    'popüler': ['popüler', 'tercih', 'çok satan', 'popular', 'trend'],
    'performans': ['performans', 'güç', 'hız', 'power', 'hızlı']
}

def get_word_similarity(word1: str, word2: str) -> float:
    """İki kelime arasındaki benzerliği hesaplar"""
    return string_similarity(word1.lower(), word2.lower())

def find_similar_words(word: str, threshold: float = 0.6) -> List[str]:
    """Verilen kelimeye benzer kelimeleri bulur"""
    similar_words = []
    for group_name, group_words in WORD_GROUPS.items():
        for group_word in group_words:
            similarity = get_word_similarity(word, group_word)
            if similarity > threshold:
                similar_words.extend(group_words)
                break
    
    return list(set(similar_words))

def normalize(text):
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()

def extract_cpu_from_prompt(prompt: str):
    cpu_hierarchy = [
        'ryzen 9', 'i9', 'ryzen 7', 'i7',
        'ryzen 5', 'i5', 'ryzen 3', 'i3'
    ]
    for cpu in cpu_hierarchy:
        if cpu in prompt:
            return cpu.title() if 'ryzen' in cpu else cpu
    return None

def prompt_to_filters(prompt, df):
    prompt = normalize(prompt)
    filters = {}
    fields = ["Urun_Ad", "Marka", "Fiyat"]  # her zaman gösterilsin

    # Kelime benzerliği ile genişletilmiş sorgu analizi
    words = prompt.split()
    for word in words:
        similar_words = find_similar_words(word)
        prompt += " " + " ".join(similar_words)

    # 💰 Fiyat aralığı veya tekli
    range_match = re.search(r'(\d{4,6})\s*(?:-|ile|–)\s*(\d{4,6})', prompt)
    if range_match:
        min_val, max_val = float(range_match.group(1)), float(range_match.group(2))
        filters['min_price'] = min(min_val, max_val)
        filters['max_price'] = max(min_val, max_val)
    else:
        price_match = re.search(r'(\d{4,6})\s*(tl|₺)?', prompt)
        if price_match:
            try:
                price_val = float(price_match.group(1))
                if any(x in prompt for x in ['üst', 'uzeri', 'fazla', 'daha fazla', 'en az', 'daha yuksek']):
                    filters['min_price'] = price_val
                elif any(x in prompt for x in ['alt', 'az', 'daha az', 'en fazla']):
                    filters['max_price'] = price_val
                else:
                    filters['max_price'] = price_val
            except:
                pass

    # Selamlama kontrolü
    greetings = {
        'selam': 'Selam dostum! Sana nasıl yardımcı olabilirim? 😊',
        'merhaba': 'Merhaba! Bugün sana nasıl yardımcı olabilirim? 🤗',
        'naber': 'İyidir dostum, sen nasılsın? Sana nasıl yardımcı olabilirim? 😎',
        'ne haber': 'İyilik! Sen nasılsın? Sana nasıl bir laptop önerebilirim? 🤔',
        'hey': 'Hey! Nasıl gidiyor? Sana nasıl yardımcı olabilirim? 😊',
        'günaydın': 'Günaydın! Güzel bir gün olsun. Sana nasıl yardımcı olabilirim? 🌞',
        'iyi akşamlar': 'İyi akşamlar! Sana nasıl yardımcı olabilirim? 🌙',
        'selamun aleyküm': 'Aleyküm selam! Sana nasıl yardımcı olabilirim? 🤲',
        'nasılsın': 'İyiyim dostum, sen nasılsın? Sana nasıl bir laptop önerebilirim? 😊',
        'sen kimsin': 'Ben senin laptop öneri asistanınım! Sana en uygun laptopu bulmak için buradayım 🤖',
        'kimsin': 'Ben senin laptop öneri asistanınım! Sana en uygun laptopu bulmak için buradayım 🤖',
        'ne yapıyorsun': 'Sana en uygun laptopu bulmak için çalışıyorum! Nasıl bir laptop arıyorsun? 💻',
        'yardım': 'Tabii ki yardımcı olabilirim! Ne tür bir laptop arıyorsun? 🤔'
    }
    
    # Selamlaşma kontrolü - kelime benzerliği ile
    prompt_words = prompt.split()
    for word in prompt_words:
        for greet, response in greetings.items():
            if get_word_similarity(word, greet) > 0.8:  # Yüksek benzerlik eşiği
                filters['greeting'] = True
                filters['greeting_response'] = response
                return filters

    # 💾 SSD
    if any(w in prompt for w in ['ssd', 'depolama', 'disk', 'nvme', 'm2']):
        fields.append("SSD")
        filters["sort_by"] = filters.get("sort_by", "SSD")
        filters["ascending"] = filters.get("ascending", False)

    # 🔋 Pil
    if any(w in prompt for w in ['pil', 'sarj', 'batarya', 'uzun sure', 'dayanikli']):
        fields.append("Pil_Gucu")
        filters["sort_by"] = filters.get("sort_by", "Pil_Gucu")
        filters["ascending"] = False

    # Marka kontrolü
    marka_bulundu = False
    if 'Marka' in df.columns:
        unique_brands = df['Marka'].dropna().unique()
        for brand in unique_brands:
            if isinstance(brand, str) and brand.lower() in prompt:
                filters['brand'] = brand
                fields.append("Marka")
                marka_bulundu = True
                break

    # Eğer anahtar kelimelerden biri prompt'ta geçiyor ve marka belirtilmemişse uyarı ekle
    anahtar_kelimeler = set()
    for kelime_listesi in WORD_GROUPS.values():
        anahtar_kelimeler.update(kelime_listesi)
    if any(k in prompt for k in anahtar_kelimeler) and not marka_bulundu:
        filters["brand_warning"] = "Eğer farklı bir markadan ürün istiyorsan lütfen belirt."

    # 🧠 RAM
    ram_match = re.search(r'(\d{1,2})\s*(gb)?\s*ram', prompt)
    if ram_match:
        ram_val = int(ram_match.group(1))
        if any(word in prompt for word in ['en az', 'minimum', 'daha yüksek', 'üstü', 'fazla']):
            filters['min_ram'] = ram_val
        else:
            filters['exact_ram'] = ram_val
        fields.append("RAM")
    elif any(w in prompt for w in ['ram', 'bellek', 'hafiza']):
        fields.append("RAM")

    # ⚡ CPU
    cpu = extract_cpu_from_prompt(prompt)
    if cpu:
        filters['cpu'] = cpu
        filters['prefer_cpu'] = [cpu]
        fields.append("Islemci_Modeli")
    elif any(x in prompt for x in ['hizli islemci', 'iyi islemci', 'guc islemci']):
        filters['prefer_cpu'] = ['i9', 'Ryzen 9', 'i7', 'Ryzen 7']
        fields.append("Islemci_Modeli")

    # 🎮 GPU
    if any(x in prompt for x in ['oyun', 'gpu', 'guc ekran', 'render', 'ekran karti']):
        filters['gpu'] = True
        fields.extend(["Ekran_Kart", "Ekran_Karti_Modeli", "VRAM"])
        filters['sort_by'] = filters.get("sort_by", "VRAM")
        filters['ascending'] = filters.get("ascending", False)

    # 🪶 Hafiflik
    if any(w in prompt for w in ['hafif', 'tasinabilir', 'light', 'agirlik', 'ultrabook']):
        fields.append("Agirlik")
        filters['sort_by'] = filters.get("sort_by", "Agirlik")
        filters['ascending'] = True

    # 📺 Ekran
    if any(w in prompt for w in ['ekran', 'buyuk ekran', 'film', 'görüntü', 'kucuk ekran']):
        fields.append("Ekran_Boyutu")
        filters['sort_by'] = filters.get("sort_by", "Ekran_Boyutu")
        filters['ascending'] = False

    # 💸 Fiyat sıralama
    if any(w in prompt for w in ['ucuz', 'butce', 'bütçe', 'uygun', 'ekonomik']):
        filters['sort_by'] = filters.get("sort_by", "Fiyat")
        filters['ascending'] = True
    elif any(w in prompt for w in ['pahali', 'paraya kiyarim', 'premium']):
        filters['sort_by'] = filters.get("sort_by", "Fiyat")
        filters['ascending'] = False

    # 🎯 Kullanım amacı
    if any(w in prompt for w in ['ofis', 'is', 'calisma']):
        filters['sort_by'] = filters.get("sort_by", "Pil_Gucu")
        filters['ascending'] = False
    elif any(w in prompt for w in ['tasarim', 'cizim', 'grafik']):
        filters['gpu'] = True
        fields.extend(["Ekran_Kart", "Ekran_Karti_Modeli", "VRAM"])
    elif any(w in prompt for w in ['ogrenci', 'okul', 'universite']):
        filters['sort_by'] = filters.get("sort_by", "Fiyat")
        filters['ascending'] = True

    # ⭐ Popülerlik ve yenilik
    if any(w in prompt for w in ['populer', 'tercih', 'cok satan']):
        filters['sort_by'] = filters.get("sort_by", "Fiyat")
        filters['ascending'] = False
    elif any(w in prompt for w in ['yeni', 'son', 'guncel']):
        filters['sort_by'] = filters.get("sort_by", "Fiyat")
        filters['ascending'] = False

    filters["fields"] = list(dict.fromkeys(fields))  # tekrarları sil
    return filters