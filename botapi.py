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

import requests

def get_akakce_image(url):
    try:
        api_url = "https://km9jvxo3il.execute-api.eu-central-1.amazonaws.com/get-image/"
        params = {"url": url}
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if "image_url" in data:
            return data["image_url"]
        else:
            print(f"API hata cevabı: {data.get('error')}")
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
