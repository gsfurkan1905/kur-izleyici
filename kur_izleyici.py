# -*- coding: utf-8 -*-
# DOSYA ADI: kur_izleyici.py
# SÜRÜM: Hisse Senedi Takipçisi (Alpha Vantage)

"""
Bu betik, bir sunucu tarafından "Zamanlanmış Görev" olarak
çalıştırılmak üzere tasarlanmıştır.

SADECE BİR KEZ çalışır, Alpha Vantage API'sini kullanarak 
belirtilen hisse senedinin (KOCHL) fiyatını kontrol eder,
hedef fiyata ulaşılmışsa Telegram üzerinden bildirim gönderir
ve ardından kapanır.

'while True' veya 'time.sleep' içermez.
"""

import requests
import json
import time
import os  # Gizli bilgileri (Secrets) işletim sistemi ortamından okumak için

# --- 1. Adım: GİZLİ BİLGİLERİ GITHUB'DAN OKUMA ---
# Bu betik, 'check.yaml' dosyasının 'env:' bloğu aracılığıyla
# sağladığı 'Secrets' (Gizli Bilgiler) değişkenlerine güvenir.
try:
    # Telegram için gerekli bilgiler
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    
    # Hisse senedi API'si için gerekli anahtar
    API_KEY = os.environ['ALPHA_VANTAGE_API_KEY']
    
except KeyError as e:
    # Eğer 'check.yaml' veya 'Secrets' ayarlarında bir eksiklik varsa,
    # hangi anahtarın eksik olduğunu belirten net bir hata ver ve programdan çık.
    # Aldığınız hata tam olarak buradan kaynaklanıyor.
    print(f"HATA: Gizli bilgi (Secret) bulunamadı: {e}")
    print("Lütfen GitHub Depo Ayarları (Settings) -> Secrets -> Actions bölümünü kontrol edin.")
    print("Gerekenler: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALPHA_VANTAGE_API_KEY")
    exit(1) # Hata kodu 1 ile programı sonlandır


# --- 2. Adım: HİSSE SENEDİ VE HEDEF YAPILANDIRMASI ---

# Takip edilecek hisse senedinin BIST sembolü
# Alpha Vantage, BIST hisseleri için ".IS" son ekini kullanır.
HISSE_SEMBOLU = "KOCHL.IS"

# !!! ÖNEMLİ !!!
# Alarmın çalmasını istediğiniz fiyatı buraya yazın
HEDEF_FIYAT = 300.0  # ÖRNEK: Hisse fiyatı 300.0 TL'ye eşit veya büyükse

# Sadece mesajda gösterilecek para birimi metni
PARA_BIRIMI = "TRY"
# ---------------------------------------------------


def gonder_telegram_bildirimi(token, chat_id, mesaj):
    """
    Belirtilen token ve chat_id kullanarak Telegram API'sine
    'requests' kütüphanesi ile bir mesaj gönderir.
    """
    telegram_api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Gönderilecek veriyi (parametreleri) bir sözlük olarak hazırlıyoruz
    params = {
        'chat_id': chat_id,
        'text': mesaj
    }
    
    print("Telegram'a bildirim gönderiliyor...")
    try:
        # API'lere bağlanırken zaman aşımı (timeout) eklemek iyi bir pratiktir.
        # 30 saniye içinde yanıt gelmezse hata verir.
        response = requests.get(telegram_api_url, params=params, timeout=30)
        
        # Eğer Telegram API'si 4xx (örn: 401 Yetkisiz) veya 5xx (Sunucu hatası)
        # gibi bir hata kodu dönerse, programın çökmesini sağlar.
        response.raise_for_status() 
        
        print("Bildirim başarıyla gönderildi.")
        
    except requests.exceptions.RequestException as e:
        # Bağlantı hatası, timeout hatası, HTTP hatası vb. tüm
        # 'requests' kaynaklı hataları yakalar.
        print(f"Telegram'a bağlanırken HATA oluştu: {e}")

def fiyati_kontrol_et():
    """
    Ana program mantığı. Alpha Vantage API'sine bağlanır,
    hisse fiyatını BİR KEZ kontrol eder ve gerekirse bildirir.
    """
    
    print("--- Hisse Senedi Fiyat Kontrolü Başlatıldı ---")
    
    # Alpha Vantage API'sinden anlık fiyatı çekmek için
    # "GLOBAL_QUOTE" fonksiyonunu kullanıyoruz.
    api_url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE"
        f"&symbol={HISSE_SEMBOLU}"
        f"&apikey={API_KEY}"
    )
    
    print(f"Veri çekiliyor: {HISSE_SEMBOLU}")
    print(f"Hedef Fiyat: {HEDEF_FIYAT} {PARA_BIRIMI}")

    try:
        # 1. API İsteği
        response = requests.get(api_url, timeout=30)
        response.raise_for_status() # HTTP hatası varsa dur
        
        # Gelen JSON metnini otomatik olarak Python sözlüğüne çevir
        veri_sozluk = response.json() 

        # 2. API Hata Kontrolü (Örn: API limitine ulaşıldıysa)
        # Alpha Vantage, limiti aşınca "Note" içeren bir JSON döner.
        if "Note" in veri_sozluk:
            print(f"HATA: Alpha Vantage API Limiti Aşıldı: {veri_sozluk['Note']}")
            print("API ücretsiz katmanı günde ~25 istekle sınırlıdır.")
            print("Lütfen 'check.yaml' dosyasındaki cron zamanlamasını yavaşlatın (örn: '0 * * * *' - saatte bir
