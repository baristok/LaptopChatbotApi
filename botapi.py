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
        api_key = "6bed84c4c638ccad16fac257595bf307513d45307e91eec3158ac195f83c1ee1"  # 🔑 BURAYA KENDİ API ANAHTARINI YAZ
        scraperbox_url = f"https://api.scraperbox.com/scrape?api_key={api_key}&url={url}&render=false"

        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(scraperbox_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        # Ana ürün görseli <a class="img_w"> içinde href'te
        a_tag = soup.find('a', {'class': 'img_w'})
        if a_tag and a_tag.get('href'):
            img_url = a_tag['href']
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
