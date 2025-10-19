# -*- coding: utf-8 -*-
# dosya adı: kur_izleyici.py (Hisse Senedi Sürümü)

"""
Bu betik, bir sunucu tarafından "Zamanlanmış Görev" olarak
çalıştırılmak üzere tasarlanmıştır.

Alpha Vantage API'sini kullanarak bir hisse senedinin (KOCHL)
fiyatını BİR KEZ kontrol eder ve hedef fiyata ulaşılmışsa
Telegram üzerinden bildirim gönderir.
"""

import requests
import json
import time
import os  # Secrets (gizli bilgiler) okumak için

# --- YAPIŞTIRILACAK ALAN: GİZLİ BİLGİLERİ OKUMA ---
try:
    # Telegram bilgileri
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    
    # Yeni Finans API Anahtarı
    API_KEY = os.environ['ALPHA_VANTAGE_API_KEY']
    
except KeyError as e:
    print(f"HATA: Gizli bilgi (Secret) bulunamadı: {e}")
    print("Lütfen GitHub Repository Secrets ayarlarını kontrol edin.")
    print("Gerekenler: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALPHA_VANTAGE_API_KEY")
    exit(1) # Hata varsa programdan çık


# --- YAPIlandırma: HİSSE SENEDİ VE HEDEF ---

# Takip edilecek hisse senedinin BIST sembolü
# Alpha Vantage, BIST hisseleri için ".IS" son ekini kullanır.
HISSE_SEMBOLU = "KOCHL.IS"

# Alarmın çalacağı fiyat (Bu satırı kendi hedefinizle değiştirin)
HEDEF_FIYAT = 152.0  # ÖRNEK: 152.0 TL

# Fiyatın para birimi (Sadece mesajlaşma için)
PARA_BIRIMI = "TRY"
# -----------------------------------------------


def gonder_telegram_bildirimi(token, chat_id, mesaj):
    """
    Telegram API'sine 'requests' ile bildirim gönderir.
    (Bu fonksiyon kur izleyici ile aynı)
    """
    telegram_api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {'chat_id': chat_id, 'text': mesaj}
    
    print("Telegram'a bildirim gönderiliyor...")
    try:
        # Timeout süresini 30 saniyeye çıkardım
        response = requests.get(telegram_api_url, params=params, timeout=30)
        response.raise_for_status() 
        print("Bildirim başarıyla gönderildi.")
    except requests.exceptions.RequestException as e:
        print(f"Telegram'a bağlanırken HATA oluştu: {e}")

def fiyati_kontrol_et():
    """
    Ana program mantığı. Hisse fiyatını BİR KEZ kontrol eder.
    """
    print("--- Hisse Senedi Fiyat Kontrolü Başlatıldı ---")
    
    # Alpha Vantage API'sinden anlık fiyatı çek ("GLOBAL_QUOTE" fonksiyonu)
    api_url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE"
        f"&symbol={HISSE_SEMBOLU}"
        f"&apikey={API_KEY}"
    )
    
    print(f"Veri çekiliyor: {HISSE_SEMBOLU}")

    try:
        # Timeout süresini 30 saniyeye çıkardım
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        veri_sozluk = response.json() 

        # API Hata Kontrolü (Örn: API limitine ulaşıldıysa)
        if "Note" in veri_sozluk:
            print(f"HATA: Alpha Vantage API Limiti: {veri_sozluk['Note']}")
            print("API ücretsiz katmanı 25 istek/gün limitine sahip olabilir, YAML'daki cron süresini artırın.")
            return

        # Gelen JSON verisini işle
        # Yanıt formatı: {"Global Quote": {"05. price": "215.50", ...}}
        global_quote = veri_sozluk.get("Global Quote")
        if not global_quote:
            print(f"HATA: API yanıtında 'Global Quote' bulunamadı.")
            print(f"Yanıt: {veri_sozluk}")
            return

        mevcut_fiyat_str = global_quote.get("05. price")
        if mevcut_fiyat_str is None:
            print(f"HATA: Yanıtta '05. price' (fiyat bilgisi) bulunamadı.")
            return

        # Fiyat bilgisi metin ("215.50") olarak gelir, sayıya (float) çevir
        mevcut_fiyat = float(mevcut_fiyat_str)

        zaman_damgasi = time.ctime() 
        print(f"[{zaman_damgasi}] Kontrol: {HISSE_SEMBOLU} = {mevcut_fiyat:.2f} {PARA_BIRIMI}")

        # HEDEF KONTROLÜ
        if mevcut_fiyat >= HEDEF_FIYAT:
            print("!!! HEDEF YAKALANDI !!!")
            alarm_mesaji = (
                f"🚨 HİSSE ALARMI! 🚨\n\n"
                f"Hedef Yakalandı: {HISSE_SEMBOLU} >= {HEDEF_FIYAT} {PARA_BIRIMI}\n\n"
                f"🔥 MEVCUT FİYAT: {mevcut_fiyat:.2f} {PARA_BIRIMI}"
            )
            gonder_telegram_bildirimi(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, alarm_mesaji)
        else:
            print(f"Hedef henüz yakalanmadı (Hedef: {HEDEF_FIYAT} {PARA_BIRIMI})")
            
    except requests.exceptions.RequestException as e:
        print(f"Hisse verisi çekilirken HATA OLUŞTU: {e}")
    except ValueError:
        print(f"HATA: Gelen fiyat ('{mevcut_fiyat_str}') sayıya dönüştürülemedi.")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
    
    print("--- Kontrol Tamamlandı ---")

# --- Programın Başlangıç Noktası ---
if __name__ == "__main__":
    fiyati_kontrol_et()
