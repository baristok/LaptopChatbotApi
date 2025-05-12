import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from tensorflow.keras.models import Model  # type: ignore
from tensorflow.keras.layers import Input, Dense  # type: ignore
from tensorflow.keras.optimizers import Adam  # type: ignore
import matplotlib.pyplot as plt

# 📥 CSV'yi oku
DATA_PATH = "./tamveriseti.csv"
raw_df = pd.read_csv(DATA_PATH)

# 🧹 Gereksiz kolonları at
to_drop = ['Urun_Ad', 'Seri', 'Urun_URL']
df = raw_df.drop(columns=to_drop, errors='ignore')

# 🔧 Fiyat ve Ağırlık düzenle
if 'Fiyat' in df.columns:
    df['Fiyat'] = (
        df['Fiyat']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df['Fiyat'] = pd.to_numeric(df['Fiyat'], errors='coerce')

if 'Agirlik' in df.columns:
    df['Agirlik'] = pd.to_numeric(df['Agirlik'], errors='coerce')

# ✅ Sadece önemli sütunlara göre NaN sil
important_cols = ['Marka', 'SSD', 'Ekran_Karti_Hafizasi', 'RAM',
                  'Ekran_Boyutu', 'Isletim_Sistemi', 'Agirlik', 'Ekran_Karti_Modeli']
df = df.dropna(subset=important_cols, axis=0)

# 🔍 Sayısal ve kategorik kolonları ayır
categorical_cols = df.select_dtypes(include='object').columns.tolist()
numeric_cols = df.select_dtypes(include='number').columns.tolist()

# 🎯 One-hot encode + MinMax scale
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
encoded = encoder.fit_transform(df[categorical_cols])

scaler = MinMaxScaler()
scaled = scaler.fit_transform(df[numeric_cols])

# 🧬 Veriyi birleştir
X = np.concatenate([encoded, scaled], axis=1)

# 🧼 NaN / Inf temizliği
X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

# ✂️ Train/test böl
X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

# 🧠 AutoEncoder modelini kur
input_dim = X.shape[1]
input_layer = Input(shape=(input_dim,))
encoded = Dense(64, activation='relu')(input_layer)
encoded = Dense(32, activation='relu')(encoded)
decoded = Dense(64, activation='relu')(encoded)
output_layer = Dense(input_dim, activation='sigmoid')(decoded)

autoencoder = Model(inputs=input_layer, outputs=output_layer)
autoencoder.compile(optimizer=Adam(1e-3), loss='mse')

# 🚀 Modeli eğit ve geçmişi kaydet
history = autoencoder.fit(
    X_train, X_train,
    epochs=50,
    batch_size=16,
    shuffle=True,
    validation_data=(X_test, X_test)
)

# 📈 Loss ve val_loss grafiği çiz
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Autoencoder Eğitim Süreci')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("autoencoder_loss_plot.png")  # Opsiyonel: Kaydet
plt.show()

# 🔍 Encoder modelini çıkar
encoder_model = Model(inputs=input_layer, outputs=encoded)
latent_vectors = encoder_model.predict(X)

# 🧾 Latent vektörleri veriye ekle
latent_df = pd.DataFrame(latent_vectors, index=df.index)
final_df = pd.concat([raw_df.loc[df.index].reset_index(drop=True), latent_df.reset_index(drop=True)], axis=1)

# 💾 Sonuçları CSV olarak kaydet
final_df.to_csv("latent_vektorlu_laptoplar.csv", index=False)

print(f"✅ Eğitim tamamlandı. Sonuç dosyası: latent_vektorlu_laptoplar.csv")
print(f"📊 Eğitim grafiği: autoencoder_loss_plot.png")
