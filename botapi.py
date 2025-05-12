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

def get_akakce_image(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Farklı görsel etiketlerini kontrol et
        # 1. Önce ana ürün görseli
        a_tag = soup.find('a', {'class': 'img_w'})
        if a_tag and a_tag.get('href'):
            img_url = a_tag['href']
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
            
        # 2. Alternatif görsel etiketleri
        img_tags = soup.find_all('img')
        for img in img_tags:
            # Ürün görseli olabilecek class'ları kontrol et
            if img.get('class') and any(c in ['p_v8', 'p_v9', 'p_v10', 'p_v11', 'p_v12'] for c in img.get('class')):
                img_url = img.get('src')
                if img_url:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    return img_url
                    
            # data-src özelliğini kontrol et
            if img.get('data-src'):
                img_url = img.get('data-src')
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
                
            # src özelliğini kontrol et
            if img.get('src') and 'akakcecdn.com' in img.get('src'):
                img_url = img.get('src')
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

@app.get("/get-image/")
async def get_image(url: str = Query(..., description="Ürün sayfası URL'si")):
    image_url = get_akakce_image(url)
    if image_url:
        return {"image_url": image_url}
    return {"error": "Görsel bulunamadı"}

@app.post("/ping")
async def keep_alive():
    # Basit bir yanıt döner, bu endpoint API'nin boşa düşmemesi için çağrılır.
    return {"message": "API is alive"}
