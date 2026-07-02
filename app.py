import streamlit as st
import joblib
import pandas as pd

# 1. Sayfa Ayarları (Sekme adı, genişlik vb.)
st.set_page_config(
    page_title="Ev Fiyatı Tahmincisi",
    page_icon="🏠",
    layout="wide"  # Geniş ekran modu
)

# 2. Modeli Önbellekle Yükle (Hız için cache kullanıyoruz)
@st.cache_resource
def load_model():
    try:
        model = joblib.load('house_price_model.pkl')
        cols = joblib.load('model_columns.pkl')
        return model, cols
    except:
        return None, None

model, model_columns = load_model()

if model is None:
    st.error("Model dosyaları bulunamadı! Lütfen .pkl dosyalarını klasöre ekleyin.")
    st.stop()

# --- ARAYÜZ TASARIMI ---

# Başlık ve Görsel Bölümü
col_header1, col_header2 = st.columns([1, 2])

with col_header1:
    # Rastgele güzel bir ev görseli
    st.image("https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80", width=300)

with col_header2:
    st.title("AI Destekli Gayrimenkul Değerleme")
    st.markdown("""
    Bu sistem, makine öğrenmesi (XGBoost) kullanarak evin özelliklerine göre **anlık piyasa değeri** tahmini yapar.
    Soldaki menüden özellikleri değiştirin, fiyatın nasıl değiştiğini izleyin.
    """)

st.divider() # Yatay çizgi

# --- YAN MENÜ (SIDEBAR) ---
st.sidebar.header("⚙️ Ev Özellikleri")

# Kullanıcıdan verileri anlık alıyoruz
input_total_sf = st.sidebar.slider("Toplam Alan (ft² / sq ft)", 500, 5000, 1500, step=10)
input_quality = st.sidebar.select_slider("Malzeme Kalitesi", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], value=5)
input_year = st.sidebar.number_input("İnşa Yılı", 1900, 2024, 2005)
input_garage = st.sidebar.selectbox("Garaj Kapasitesi", [0, 1, 2, 3, 4], index=2)
input_bath = st.sidebar.radio("Banyo Sayısı", [1, 2, 3, 4], index=1, horizontal=True)
input_fireplaces = st.sidebar.slider("Şömine Sayısı", 0, 3, 1)

# --- TAHMİN MEKANİZMASI (Gelişmiş Mantık) ---

# GARAJ ALANI TAHMİNİ: Araç kapasitesine göre mantıklı bir alan atıyoruz (1 araç ~250 birim)
garage_area_estimate = input_garage * 250

# BODRUM ALANI TAHMİNİ: Toplam alanın %40'ı bodrumdur varsayımı
bsmt_estimate = input_total_sf * 0.4 

# GİRİŞ KATI TAHMİNİ: Toplam alanın %60'ı giriş kattır varsayımı
first_floor_estimate = input_total_sf * 0.6

# Veriyi hazırla
user_input = pd.DataFrame({
    # Kullanıcıdan gelen ana veriler
    "TotalSF": [input_total_sf],
    "OverallQual": [input_quality],
    "YearBuilt": [input_year],
    "GarageCars": [input_garage],
    "FullBath": [input_bath],
    "Fireplaces": [input_fireplaces],
    
    # --- MODELİ DESTEKLEMEK İÇİN TÜRETİLEN VERİLER ---
    # Modelin "0" görüp fiyatı düşürmesini engellemek için mantıklı değerler atıyoruz
    "GrLivArea": [input_total_sf],       # Oturulabilir alanı toplam alana eşitledik
    "GarageArea": [garage_area_estimate], # Garaj alanı kapasiteyle orantılı
    "TotalBsmtSF": [bsmt_estimate],      # Bodrum alanı dolu
    "1stFlrSF": [first_floor_estimate]   # Giriş katı dolu
})

# Eksik sütunları doldur (Reindex - Modelin beklediği 259 sütuna tamamla)
user_input = user_input.reindex(columns=model_columns, fill_value=0)

# Tahmin yap
prediction = model.predict(user_input)[0]

# --- SONUÇ EKRANI (DASHBOARD) ---

# Ortalama bir ev fiyatı referansı (Veri setimizdeki ortalama ~180.000$)
avg_price = 180921 
fark = prediction - avg_price

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.subheader("Tahmini Değer")
    
    # Büyük, renkli gösterge (Metric)
    st.metric(
        label="Güncel Piyasa Fiyatı",
        value=f"${int(prediction):,}",
        delta=f"{int(fark):,} vs Ortalama", # Ortalamaya göre fark
        delta_color="normal" # Yeşil/Kırmızı otomatik
    )

with col_res2:
    st.subheader("Piyasa Konumu")
    
    # İlerleme Çubuğu (Maksimum 800k$ varsayımı üzerinden)
    # HATA DÜZELTİLDİ: float() dönüşümü eklendi
    progress_val = float(min(prediction / 800000, 1.0)) 
    st.progress(progress_val)
    
    # GELİŞMİŞ SEGMENTASYON
    if prediction > 450000:
        st.success("💎 ULTRA LÜKS SEGMENT")
        st.write("Bu ev bölgenin en seçkin %1'lik diliminde.")
    elif prediction > 300000:
        st.warning("🏆 LÜKS SEGMENT")
        st.write("Yüksek yaşam standartları sunan prestijli mülk.")
    elif prediction > 200000:
        st.info("🏡 ORTA-ÜST SEGMENT")
        st.write("Ortalamanın üzerinde, konforlu aile evi.")
    elif prediction > 120000:
        st.write("✅ STANDART SEGMENT")
        st.write("Piyasa ortalamasında, ideal bir başlangıç evi.")
    else:
        st.error("📉 EKONOMİK SEGMENT")
        st.write("Yatırım fırsatı veya tadilat gerektirebilecek mülk.")

# Detaylı veri tablosu (İsteğe bağlı açılır kapanır)
with st.expander("Arka Planda Gönderilen Veriyi İncele"):
    st.dataframe(user_input)