import argparse
import pandas as pd
from nlp import prompt_to_filters
from filterMotor import filter_products
import sys
import io
import random

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="Laptop suggestion engine")
    parser.add_argument("--csv", type=str, default="latent_vektorlu_laptoplar.csv", help="CSV path")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt text")
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.csv)
    except Exception as e:
        print(f"CSV could not be loaded: {e}")
        return

    df = pd.read_csv("tamveriseti.csv")  # verisetin burada tanımlıysa
    filters = prompt_to_filters(args.prompt, df)
    
    if filters.get("greeting"):
        print(filters.get("greeting_response", "🤖 Selam dostum! Sana nasıl yardımcı olabilirim? Kullanım ihtiyacını yaz yeter 😎"))
        return

    # Filtrelemeyi bir kez yap
    result = filter_products(df, filters)

    if result.empty:
        print("No matching products found.")
        return

    # İlk 30 ürünü al (eğer 30'dan az ürün varsa hepsini al)
    top_products = result.head(30)
    
    # Sabit gösterilecek sütunlar
    base_cols = ["Urun_Ad", "Fiyat"]
    prompt_cols = filters.get("fields", [])
    show_cols = list(dict.fromkeys(base_cols + prompt_cols))  # Tekrarları temizle

    # Tablo başlığı
    header = " | ".join([col.ljust(20) for col in show_cols])
    print("\n" + header)
    print("-" * len(header))

    # İlk 30 ürün arasından rastgele 6 tanesini seç ve göster
    random_selection = top_products.sample(n=min(6, len(top_products)), random_state=random.randint(1, 9999))
    for _, row in random_selection.iterrows():
        row_data = [str(row.get(col, "N/A")).ljust(20) for col in show_cols]
        print(" | ".join(row_data))

    # URL'leri en altta yaz
    print("\nUrun Linkleri:")
    
    for _, row in random_selection.iterrows():
        ad = row.get("Urun_Ad", "Bilinmeyen Ürün")
        url = row.get("Urun_URL", "No URL")
        print(f"{ad}: {url}")



if __name__ == "__main__":
    main()
