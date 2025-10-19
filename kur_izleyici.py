# -*- coding: utf-8 -*-
# dosya adı: kur_izleyici.py

"""
Bu betik, bir sunucu tarafından "Zamanlanmış Görev" olarak
çalıştırılmak üzere tasarlanmıştır.

SADECE BİR KEZ çalışır, kuru kontrol eder ve kapanır.
'while True' veya 'time.sleep' içermez.
"""

import requests
import json
import time
import os  # Secrets (gizli bilgiler) okumak için eklendi

# --- Alarm Yapılandırması ---
# (Hedefleri buradan veya GitHub Secrets'tan ayarlayabilirsiniz)
HEDEF_KUR = 49.0
KAYNAK_BIRIM = "EUR"
HEDEF_BIRIM = "TRY"
API_URL = f"https://api.frankfurter.app/latest?from={KAYNAK_BIRIM}&to={HEDEF_BIRIM}"

# --- GİZLİ BİLGİLERİ GITHUB'DAN OKUMA ---
# Kodumuzu güvende tutmak için Token ve ID'yi doğrudan koda yazmıyoruz.
# Bunları GitHub Secrets'tan (Çevre Değişkeni) okuyoruz.
try:
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    print("HATA: TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID bulunamadı.")
    print("Lütfen GitHub Repository Secrets ayarlarını kontrol edin.")
    exit(1) # Hata varsa programdan çık


def gonder_telegram_bildirimi(token, chat_id, mesaj):
    """
    Telegram API'sine 'requests' ile bildirim gönderir.
    """
    telegram_api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {'chat_id': chat_id, 'text': mesaj}
    
    print("Telegram'a bildirim gönderiliyor...")
    try:
        response = requests.get(telegram_api_url, params=params, timeout=10)
        response.raise_for_status() 
        print("Bildirim başarıyla gönderildi.")
    except requests.exceptions.RequestException as e:
        print(f"Telegram'a bağlanırken HATA oluştu: {e}")

def kuru_kontrol_et():
    """
    Ana program mantığı. Kuru BİR KEZ kontrol eder.
    """
    print("--- Döviz Kuru Kontrolü Başlatıldı ---")
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        veri_sozluk = response.json() 
        
        mevcut_kur = veri_sozluk.get("rates", {}).get(HEDEF_BIRIM)

        if mevcut_kur is None:
            print(f"HATA: API yanıtında '{HEDEF_BIRIM}' kuru bulunamadı.")
            return # Fonksiyondan çık

        zaman_damgasi = time.ctime() 
        print(f"[{zaman_damgasi}] Kontrol: 1 {KAYNAK_BIRIM} = {mevcut_kur:.4f} {HEDEF_BIRIM}")

        if mevcut_kur >= HEDEF_KUR:
            print("!!! HEDEF YAKALANDI !!!")
            alarm_mesaji = (
                f"🚨 DÖVİZ ALARMI! 🚨\n\n"
                f"Hedef Yakalandı: 1 {KAYNAK_BIRIM} >= {HEDEF_KUR} {HEDEF_BIRIM}\n\n"
                f"🔥 MEVCUT KUR: {mevcut_kur:.4f} {HEDEF_BIRIM}"
            )
            gonder_telegram_bildirimi(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, alarm_mesaji)
        else:
            print("Hedef henüz yakalanmadı.")
            
    except requests.exceptions.RequestException as e:
        print(f"Kur verisi çekilirken HATA OLUŞTU: {e}")
    
    print("--- Kontrol Tamamlandı ---")

# --- Programın Başlangıç Noktası ---
# Bu betik çalıştırıldığında, sadece bu fonksiyonu çağırır ve biter.
if __name__ == "__main__":
    kuru_kontrol_et()
