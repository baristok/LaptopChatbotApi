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

import random
import socks


# Örnek proxy listesi yükleyici
import json
with open("Free_Proxy_List.json", "r", encoding="utf-8") as f:
    proxy_list = json.load(f)

def get_random_socks4_proxy():
    proxy = random.choice(proxy_list)
    return {
        'http': f'socks4://{proxy["ip"]}:{proxy["port"]}',
        'https': f'socks4://{proxy["ip"]}:{proxy["port"]}'
    }

def get_akakce_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        proxies = get_random_socks4_proxy()
        r = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        a_tag = soup.find('a', {'class': 'img_w'})
        if a_tag and a_tag.get('href'):
            img_url = a_tag['href']
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
    except Exception as e:
        print(f"Proxy ile görsel çekme hatası: {e}")
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
        command = f'chcp 65001 > NUL & py cli.py --prompt "{data.prompt}"'
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
