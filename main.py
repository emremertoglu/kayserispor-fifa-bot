import requests
import json
import os
import tweepy
from time import sleep
import logging

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Twitter API anahtarlarını environment değişkenlerinden al
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

# API anahtarlarının varlığını kontrol et
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    logger.error("Twitter API anahtarları eksik! Lütfen environment değişkenlerini kontrol edin.")
    exit(1)

try:
    # Twitter API v2 için client oluştur
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )
    logger.info("Twitter API v2 bağlantısı başarılı")
except Exception as e:
    logger.error(f"Twitter API v2 bağlantısı başarısız: {e}")
    exit(1)

STATE_FILE = "kayseri_count.json"

def get_kayserispor_count():
    """FIFA API'den Kayserispor dosya sayısını alır"""
    try:
        url = "https://knowledge.fifa.com/api/fkmpdatahub/fifadatahubtransfer/registrationBans"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        count = sum(1 for item in data if isinstance(item, dict) and item.get("club_in") == "KAYSERISPOR FUTBOL A.S.")
        logger.info(f"FIFA API'den alınan Kayserispor dosya sayısı: {count}")
        return count
        
    except requests.exceptions.RequestException as e:
        logger.error(f"FIFA API isteği başarısız: {e}")
        return None
    except Exception as e:
        logger.error(f"FIFA API veri işleme hatası: {e}")
        return None

def load_last_count():
    """Son kayıtlı sayıyı yükler"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"Son kayıtlı sayı yüklendi: {data['count']}")
                return data["count"]
        logger.info("Önceki kayıt bulunamadı, ilk çalıştırma")
        return None
    except Exception as e:
        logger.error(f"Son sayı yükleme hatası: {e}")
        return None

def save_last_count(count):
    """Yeni sayıyı kaydeder"""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"count": count}, f)
        logger.info(f"Yeni sayı kaydedildi: {count}")
    except Exception as e:
        logger.error(f"Sayı kaydetme hatası: {e}")

def send_tweet(message):
    """Tweet atar"""
    try:
        response = client.create_tweet(text=message)
        if response.data:
            logger.info(f"Tweet atıldı: {message}")
            logger.info(f"Tweet ID: {response.data['id']}")
            return True
        else:
            logger.error("Tweet atılamadı")
            return False
    except tweepy.errors.Forbidden as e:
        logger.error(f"Twitter API erişim hatası (403): {e}")
        return False
    except tweepy.errors.Unauthorized as e:
        logger.error(f"Twitter API yetkilendirme hatası (401): {e}")
        return False
    except Exception as e:
        logger.error(f"Twitter API beklenmeyen hata: {e}")
        return False

def main():
    """Ana bot fonksiyonu"""
    logger.info("Kayserispor FIFA Bot başlatıldı")
    
    while True:
        try:
            current_count = get_kayserispor_count()
            
            if current_count is None:
                logger.warning("FIFA API'den veri alınamadı, 10 dakika sonra tekrar denenecek")
                sleep(600)
                continue
                
            last_count = load_last_count()

            if last_count is None:
                # İlk çalıştırma
                tweet_text = f"Şu anda Kayserispor için {current_count} kayıt yasağı dosyası var."
                if send_tweet(tweet_text):
                    save_last_count(current_count)

            elif current_count != last_count:
                # Değişiklik var
                tweet_text = f"Kayserispor dosya sayısında değişiklik var! Yeni sayı: {current_count}"
                if send_tweet(tweet_text):
                    save_last_count(current_count)
            else:
                logger.info(f"Değişiklik yok. Mevcut sayı: {current_count}")

        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")

        logger.info("10 dakika bekleniyor...")
        sleep(600)  # 10 dakika bekle

if __name__ == "__main__":
    main()
