import requests
import json
import os
import tweepy
from time import sleep
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re

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

# Dosya yolu
STATE_FILE = "kayseri_count.json"

def get_tff_kayserispor_roster():
    """TFF sitesinden Kayserispor kadro bilgilerini çeker"""
    try:
        # TFF Kayserispor sayfası URL'i
        url = "https://www.tff.org/Default.aspx?pageId=28&kulupID=72"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # İlk sayfa isteği - form verilerini almak için
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # BeautifulSoup ile sayfayı parse et
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ViewState ve diğer form verilerini al
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
        
        if not all([viewstate, viewstategenerator, eventvalidation]):
            logger.error("Form verileri bulunamadı")
            return None
        
        # Form verilerini hazırla
        form_data = {
            '__VIEWSTATE': viewstate.get('value', ''),
            '__VIEWSTATEGENERATOR': viewstategenerator.get('value', ''),
            '__EVENTVALIDATION': eventvalidation.get('value', ''),
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            'ctl00$ContentPlaceHolder1$ddlSezon': '2025-2026',  # Sezon
            'ctl00$ContentPlaceHolder1$ddlStatus': 'Profesyonel',  # Statü
            'ctl00$ContentPlaceHolder1$ddlDurum': 'Faal',  # Durum
            'ctl00$ContentPlaceHolder1$btnAra': 'Ara'  # Ara butonu
        }
        
        # POST isteği gönder - kadro bilgilerini al
        response = session.post(url, data=form_data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Kadro bilgilerini parse et
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kadro tablosunu bul
        roster_table = soup.find('table', {'class': 'table'})
        if not roster_table:
            logger.warning("Kadro tablosu bulunamadı")
            return None
        
        # Oyuncu bilgilerini çek
        players = []
        rows = roster_table.find_all('tr')[1:]  # İlk satır başlık
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:  # En az 4 sütun olmalı
                player_info = {
                    'name': cells[0].get_text(strip=True) if cells[0] else '',
                    'position': cells[1].get_text(strip=True) if len(cells) > 1 and cells[1] else '',
                    'birth_date': cells[2].get_text(strip=True) if len(cells) > 2 and cells[2] else '',
                    'nationality': cells[3].get_text(strip=True) if len(cells) > 3 and cells[3] else ''
                }
                players.append(player_info)
        
        logger.info(f"TFF'den {len(players)} oyuncu bilgisi çekildi")
        
        # Oyuncu bilgilerini logla
        for i, player in enumerate(players[:10], 1):  # İlk 10 oyuncuyu logla
            logger.info(f"Oyuncu {i}: {player['name']} - {player['position']} - {player['birth_date']} - {player['nationality']}")
        
        if len(players) > 10:
            logger.info(f"... ve {len(players) - 10} oyuncu daha")
        
        return players
        
    except requests.exceptions.RequestException as e:
        logger.error(f"TFF sitesi isteği başarısız: {e}")
        return None
    except Exception as e:
        logger.error(f"TFF kadro veri işleme hatası: {e}")
        return None

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
    """Son kayıtlı sayıyı yükler (sadece dosyadan)"""
    try:
        # Sadece dosyadan kontrol et
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"Dosyadan son sayı yüklendi: {data['count']}")
                return data["count"]
        
        logger.info("Önceki kayıt bulunamadı, ilk çalıştırma")
        return None
    except Exception as e:
        logger.error(f"Son sayı yükleme hatası: {e}")
        return None

def save_last_count(count):
    """Yeni sayıyı kaydeder (sadece dosyaya)"""
    try:
        # Dosyaya kaydet
        with open(STATE_FILE, "w") as f:
            json.dump({"count": count}, f)
        logger.info(f"Yeni sayı dosyaya kaydedildi: {count}")
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
    
    # Manuel tweet kontrolü
    manual_tweet = os.getenv("MANUAL_TWEET", "false").lower() == "true"
    
    while True:
        try:
            # FIFA API kontrolü
            current_count = get_kayserispor_count()
            
            if current_count is None:
                logger.warning("FIFA API'den veri alınamadı")
            else:
                last_count = load_last_count()
                current_time = datetime.now().strftime("%H:%M")

                if last_count is None:
                    # İlk çalıştırma
                    if manual_tweet:
                        # Manuel tweet at
                        tweet_text = f"Şu anda Kayserispor için {current_count} kayıt yasağı dosyası var. (Güncelleme: {current_time})"
                        if send_tweet(tweet_text):
                            logger.info("Manuel tweet atıldı")
                        # Manuel tweet flag'ini kaldır
                        os.environ["MANUAL_TWEET"] = "false"
                    
                    logger.info(f"İlk çalıştırma: Dosya sayısı {current_count} olarak kaydedildi")
                    save_last_count(current_count)

                elif current_count != last_count:
                    # Değişiklik var
                    tweet_text = f"Kayserispor dosya sayısında değişiklik var! Yeni sayı: {current_count} (Güncelleme: {current_time})"
                    if send_tweet(tweet_text):
                        save_last_count(current_count)
                else:
                    logger.info(f"FIFA: Değişiklik yok. Mevcut sayı: {current_count}")

            # TFF Kadro kontrolü
            logger.info("TFF'den Kayserispor kadro bilgileri çekiliyor...")
            roster_data = get_tff_kayserispor_roster()
            
            if roster_data:
                logger.info(f"TFF kadro kontrolü tamamlandı. Toplam {len(roster_data)} oyuncu bulundu.")
            else:
                logger.warning("TFF kadro bilgileri çekilemedi")

        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")

        logger.info("10 dakika bekleniyor...")
        sleep(600)  # 10 dakika bekle

if __name__ == "__main__":
    main()
