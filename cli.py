import argparse
import pandas as pd
from nlp import prompt_to_filters
from filterMotor import filter_products
import sys
import io

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

    filtered_df = filter_products(df, filters)
    result = filter_products(df, filters)

    if result.empty:
        print("No matching products found.")
        return

    # Sabit gösterilecek sütunlar
    base_cols = ["Urun_Ad", "Fiyat"]
    prompt_cols = filters.get("fields", [])
    show_cols = list(dict.fromkeys(base_cols + prompt_cols))  # Tekrarları temizle

    # Tablo başlığı
    header = " | ".join([col.ljust(20) for col in show_cols])
    print("\n" + header)
    print("-" * len(header))

    # Her ürünü yaz
    for _, row in result.head(6).iterrows():
        row_data = [str(row.get(col, "N/A")).ljust(20) for col in show_cols]
        print(" | ".join(row_data))

    # URL'leri en altta yaz
    print("\nUrun Linkleri:")
    
    for _, row in result.head(6).iterrows():
        ad = row.get("Urun_Ad", "Bilinmeyen Ürün")
        url = row.get("Urun_URL", "No URL")
        print(f"{ad}: {url}")



if __name__ == "__main__":
    main()
