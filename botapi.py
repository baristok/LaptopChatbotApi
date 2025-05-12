from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from bs4 import BeautifulSoup
import subprocess
import json
import os
import requests
import random
import socks

# NLP word kontrolü için dış dosyan varmış
from nlp import WORD_GROUPS

# Proxy listesi dosyadan yükleniyor
with open('Free_Proxy_List.json', 'r') as f:
    PROXIES = json.load(f)


def get_akakce_image(url):
    for attempt in range(5):  # En fazla 5 farklı proxy dene
        proxy = random.choice(PROXIES)
        proxy_ip = proxy["ip"]
        proxy_port = proxy["port"]
        proxy_protocol = proxy["protocols"][0]

        # SOCKS protokolüne göre formatla
        proxy_url = f"socks{proxy_protocol[-1]}://{proxy_ip}:{proxy_port}"

        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            a_tag = soup.find('a', {'class': 'img_w'})
            if a_tag and a_tag.get('href'):
                img_url = a_tag['href']
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
        except Exception as e:
            print(f"[{attempt + 1}. deneme] Proxy {proxy_ip}:{proxy_port} hatası: {e}")
            continue  # Başarısız olursa bir sonraki proxy ile dene

    return None  # Tüm denemeler başarısız olursa


app = FastAPI()

# CORS middleware
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

        # Kelime grupları kontrolü
        should_ask_brand = any(
            any(word in data.prompt.lower() for word in group)
            for group in WORD_GROUPS.values()
        )

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
