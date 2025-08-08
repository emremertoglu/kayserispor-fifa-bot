import requests
import json
import os
import tweepy
from time import sleep
import logging
from datetime import datetime
from bs4 import BeautifulSoup

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
TFF_STATE_FILE = "tff_kadro.json"

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

def get_tff_kadro():
    """TFF sitesinden Kayserispor faal kadrosunu alır"""
    try:
        # İlk olarak sayfayı ziyaret edip form verilerini al
        session = requests.Session()
        url = "https://www.tff.org/Default.aspx?pageId=28&kulupID=72"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # İlk sayfa ziyareti
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Form verilerini topla
        form_data = {}
        
        # ViewState ve diğer gizli alanları bul
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        if viewstate:
            form_data['__VIEWSTATE'] = viewstate.get('value', '')
        
        viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        if viewstategenerator:
            form_data['__VIEWSTATEGENERATOR'] = viewstategenerator.get('value', '')
        
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
        if eventvalidation:
            form_data['__EVENTVALIDATION'] = eventvalidation.get('value', '')
        
        # Kadro arama form verilerini ekle
        form_data.update({
            'ctl00$ContentPlaceHolder1$ddlSezon': '2025-2026',  # Sezon
            'ctl00$ContentPlaceHolder1$ddlStatus': 'Profesyonel',  # Statü
            'ctl00$ContentPlaceHolder1$ddlDurum': 'Faal',  # Durum
            'ctl00$ContentPlaceHolder1$btnAra': 'Ara'  # Ara butonu
        })
        
        logger.info("TFF form verileri hazırlandı, POST request gönderiliyor...")
        
        # POST request ile kadro verilerini çek
        response = session.post(url, data=form_data, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Faal kadro tablosunu bul
        kadro_data = []
        
        # Kadro tablosunu ara (GridView veya DataGrid)
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # En az 3 sütun varsa
                    try:
                        oyuncu_adi = cells[0].get_text(strip=True)
                        pozisyon = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        lisans_durumu = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        
                        if oyuncu_adi and len(oyuncu_adi) > 2:  # Geçerli oyuncu adı
                            kadro_data.append({
                                'ad': oyuncu_adi,
                                'pozisyon': pozisyon,
                                'lisans_durumu': lisans_durumu
                            })
                    except:
                        continue
        
        logger.info(f"TFF'den alınan oyuncu sayısı: {len(kadro_data)}")
        
        # İlk 5 oyuncuyu logda göster
        if kadro_data:
            logger.info("TFF'den alınan ilk 5 oyuncu:")
            for i, oyuncu in enumerate(kadro_data[:5]):
                logger.info(f"  {i+1}. {oyuncu['ad']} - {oyuncu['pozisyon']} - {oyuncu['lisans_durumu']}")
        else:
            logger.warning("TFF'den oyuncu verisi alınamadı. Form verilerini kontrol edin.")
        
        return kadro_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"TFF API isteği başarısız: {e}")
        return None
    except Exception as e:
        logger.error(f"TFF veri işleme hatası: {e}")
        return None

def load_last_count():
    """Son kayıtlı sayıyı yükler (önce environment variable, sonra dosya)"""
    try:
        # Önce environment variable'dan kontrol et
        env_count = os.getenv("LAST_COUNT")
        if env_count:
            count = int(env_count)
            logger.info(f"Environment variable'dan son sayı yüklendi: {count}")
            return count
        
        # Dosyadan kontrol et
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
    """Yeni sayıyı kaydeder (hem dosyaya hem environment variable'a)"""
    try:
        # Dosyaya kaydet
        with open(STATE_FILE, "w") as f:
            json.dump({"count": count}, f)
        logger.info(f"Yeni sayı dosyaya kaydedildi: {count}")
        
        # Environment variable'a kaydet (Railway'de kalıcı olması için)
        os.environ["LAST_COUNT"] = str(count)
        logger.info(f"Yeni sayı environment variable'a kaydedildi: {count}")
    except Exception as e:
        logger.error(f"Sayı kaydetme hatası: {e}")

def load_tff_kadro():
    """TFF kadro verilerini yükler"""
    try:
        if os.path.exists(TFF_STATE_FILE):
            with open(TFF_STATE_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"TFF kadro verisi yüklendi: {len(data)} oyuncu")
                return data
        logger.info("TFF kadro verisi bulunamadı, ilk çalıştırma")
        return None
    except Exception as e:
        logger.error(f"TFF kadro yükleme hatası: {e}")
        return None

def save_tff_kadro(kadro_data):
    """TFF kadro verilerini kaydeder"""
    try:
        with open(TFF_STATE_FILE, "w") as f:
            json.dump(kadro_data, f, ensure_ascii=False, indent=2)
        logger.info(f"TFF kadro verisi kaydedildi: {len(kadro_data)} oyuncu")
    except Exception as e:
        logger.error(f"TFF kadro kaydetme hatası: {e}")

def check_lisans_degisiklikleri(eski_kadro, yeni_kadro):
    """Lisans durumu değişikliklerini kontrol eder"""
    if not eski_kadro or not yeni_kadro:
        return []
    
    degisiklikler = []
    
    # Eski kadrodaki oyuncuları kontrol et
    for eski_oyuncu in eski_kadro:
        eski_ad = eski_oyuncu.get('ad', '')
        eski_lisans = eski_oyuncu.get('lisans_durumu', '')
        
        # Yeni kadroda aynı oyuncuyu bul
        for yeni_oyuncu in yeni_kadro:
            yeni_ad = yeni_oyuncu.get('ad', '')
            yeni_lisans = yeni_oyuncu.get('lisans_durumu', '')
            
            if eski_ad == yeni_ad and eski_lisans != yeni_lisans:
                degisiklikler.append({
                    'oyuncu': eski_ad,
                    'pozisyon': yeni_oyuncu.get('pozisyon', ''),
                    'eski_durum': eski_lisans,
                    'yeni_durum': yeni_lisans
                })
                break
    
    return degisiklikler

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
            # FIFA API kontrolü
            current_count = get_kayserispor_count()
            
            if current_count is None:
                logger.warning("FIFA API'den veri alınamadı")
            else:
                last_count = load_last_count()
                current_time = datetime.now().strftime("%H:%M")

                if last_count is None:
                    # İlk çalıştırma
                    tweet_text = f"Şu anda Kayserispor için {current_count} kayıt yasağı dosyası var. (Güncelleme: {current_time})"
                    if send_tweet(tweet_text):
                        save_last_count(current_count)

                elif current_count != last_count:
                    # Değişiklik var
                    tweet_text = f"Kayserispor dosya sayısında değişiklik var! Yeni sayı: {current_count} (Güncelleme: {current_time})"
                    if send_tweet(tweet_text):
                        save_last_count(current_count)
                else:
                    logger.info(f"FIFA: Değişiklik yok. Mevcut sayı: {current_count}")

            # TFF Kadro kontrolü
            current_kadro = get_tff_kadro()
            
            if current_kadro is None:
                logger.warning("TFF'den veri alınamadı")
            else:
                last_kadro = load_tff_kadro()
                
                if last_kadro is None:
                    # İlk çalıştırma
                    logger.info(f"TFF: İlk kadro verisi kaydedildi: {len(current_kadro)} oyuncu")
                    save_tff_kadro(current_kadro)
                else:
                    # Değişiklik kontrolü
                    degisiklikler = check_lisans_degisiklikleri(last_kadro, current_kadro)
                    
                    if degisiklikler:
                        logger.info(f"TFF: {len(degisiklikler)} lisans değişikliği bulundu:")
                        for degisiklik in degisiklikler:
                            logger.info(f"  {degisiklik['oyuncu']} ({degisiklik['pozisyon']}): {degisiklik['eski_durum']} → {degisiklik['yeni_durum']}")
                            # Tweet atmıyoruz, sadece logda gösteriyoruz
                        
                        # Yeni kadroyu kaydet
                        save_tff_kadro(current_kadro)
                    else:
                        logger.info(f"TFF: Lisans değişikliği yok. {len(current_kadro)} oyuncu")

        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")

        logger.info("10 dakika bekleniyor...")
        sleep(600)  # 10 dakika bekle

if __name__ == "__main__":
    main()
