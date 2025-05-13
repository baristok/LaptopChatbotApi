from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import subprocess
import os
import json
import requests
from bs4 import BeautifulSoup
from fastapi import Query
from nlp import WORD_GROUPS
import pandas as pd

def get_akakce_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Ana ürün görseli <a class="img_w"> içinde href'te
        a_tag = soup.find('a', {'class': 'img_w'})
        if a_tag and a_tag.get('href'):
            img_url = a_tag['href']
            # Eğer link // ile başlıyorsa başına https: ekle
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
    except Exception as e:
        print(f"Görsel çekme hatası: {e}")
    return None


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptInput(BaseModel):
    prompt: str

@app.post("/get-suggestions/")
async def get_suggestions(data: PromptInput):
    try:
        command = f'python3 cli.py --prompt "{data.prompt}"'
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            error_json = json.dumps({"hata": stderr or "Komut hatası"}, ensure_ascii=False)
            return Response(content=error_json, media_type="application/json")

        # Kelime gruplarından herhangi biri geçiyor mu kontrol et
        should_ask_brand = False
        for words in WORD_GROUPS.values():
            if any(word in data.prompt.lower() for word in words):
                should_ask_brand = True
                break

        # 🎯 Türkçe karakterleri kaçırmadan encode et
        json_data = json.dumps({
            "cevap": stdout or "Bot bir yanıt üretemedi.",
            "recommendations": [],
            "brand_warning": None,
            "ask_brand": should_ask_brand
        }, ensure_ascii=False)
        return Response(content=json_data, media_type="application/json")

    except Exception as e:
        error_json = json.dumps({"hata": str(e)}, ensure_ascii=False)
        return Response(content=error_json, media_type="application/json")

# CSV dosyalarını bir kere yükle
laptop_df = pd.read_csv("latent_vektorlu_laptoplar.csv")
tam_veri_df = pd.read_csv("tamveriseti.csv")

def normalize_url(url):
    """URL'yi normalize eder, http:// veya https:// farkını giderir ve önemli kısmı korur"""
    # URL'den http/https protokolünü çıkar
    if "://" in url:
        url = url.split("://")[1]
    elif "//" in url and not url.startswith("//"):
        url = url.split("//")[1]
    
    # Ürün ID kısmını al (genellikle son kısım)
    if "fiyati," in url:
        product_id = url.split("fiyati,")[-1].split(".html")[0]
        return product_id
    
    return url

@app.get("/get-image/")
async def get_image(url: str = Query(..., description="Ürün sayfası URL'si")):
    try:
        # URL'yi normalize et
        normalized_url = normalize_url(url)
        image_url = None
        
        # İlk olarak latent_vektorlu_laptoplar.csv'de ara
        found_in_latent = find_image_in_csv(laptop_df, url, normalized_url)
        if found_in_latent:
            print(f"Görsel latent_vektorlu_laptoplar.csv'den bulundu: {url}")
            return {"image_url": found_in_latent, "source": "latent_csv"}
            
        # Bulunamazsa tamveriseti.csv'de ara
        found_in_tam = find_image_in_csv(tam_veri_df, url, normalized_url)
        if found_in_tam:
            print(f"Görsel tamveriseti.csv'den bulundu: {url}")
            return {"image_url": found_in_tam, "source": "tam_csv"}
        
        # CSV'lerde bulunamazsa web'den al
        print(f"Görsel CSV'lerde bulunamadı, web'den alınıyor: {url}")
        fallback_image_url = get_akakce_image(url)
        if fallback_image_url:
            print(f"Görsel web'den alındı: {url}")
            return {"image_url": fallback_image_url, "source": "web"}
            
        print(f"Görsel hiçbir yerden bulunamadı: {url}")
        return {"error": "Görsel bulunamadı", "source": "none"}
    except Exception as e:
        print(f"Görsel çekme hatası: {e}")
        return {"error": f"Görsel çekilirken hata oluştu: {str(e)}", "source": "error"}

def find_image_in_csv(df, original_url, normalized_url):
    """Verilen DataFrame'de görsel URL'sini bulmak için kullanılır"""
    # Tam URL eşleşmesi dene
    laptop_row = df[df['Urun_URL'] == original_url]
    
    # Eğer bulunamazsa, normalize edilmiş URL'yi içeren satırları ara
    if laptop_row.empty:
        # CSV'deki her URL'yi normalize et ve karşılaştır
        df['normalized_url'] = df['Urun_URL'].apply(normalize_url)
        laptop_row = df[df['normalized_url'] == normalized_url]
        # Geçici sütunu temizle
        if 'normalized_url' in df.columns:
            df.drop('normalized_url', axis=1, inplace=True)
    
    if not laptop_row.empty and 'Gorsel_URL' in df.columns:
        image_url = laptop_row.iloc[0]['Gorsel_URL']
        if image_url and str(image_url) != 'nan':
            return image_url
    
    return None

@app.post("/ping")
async def keep_alive():
    # Basit bir yanıt döner, bu endpoint API'nin boşa düşmemesi için çağrılır.
    return {"message": "API is alive"}
