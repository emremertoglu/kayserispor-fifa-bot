import requests
import json
import os
import tweepy
from time import sleep

# Twitter API anahtarlarını environment değişkenlerinden al
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

STATE_FILE = "kayseri_count.json"

def get_kayserispor_count():
    url = "https://knowledge.fifa.com/api/fkmpdatahub/fifadatahubtransfer/registrationBans"
    response = requests.get(url)
    data = response.json()
    return sum(1 for item in data if item["club_in"] == "KAYSERISPOR FUTBOL A.S.")

def load_last_count():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)["count"]
    return None

def save_last_count(count):
    with open(STATE_FILE, "w") as f:
        json.dump({"count": count}, f)

while True:
    try:
        current_count = get_kayserispor_count()
        last_count = load_last_count()

        if last_count is None:
            tweet_text = f"Şu anda Kayserispor için {current_count} kayıt yasağı dosyası var."
            api.update_status(tweet_text)
            save_last_count(current_count)
            print("İlk tweet atıldı:", tweet_text)

        elif current_count != last_count:
            tweet_text = f"Kayserispor dosya sayısında değişiklik var! Yeni sayı: {current_count}"
            api.update_status(tweet_text)
            save_last_count(current_count)
            print("Değişiklik tweet atıldı:", tweet_text)
        else:
            print("Değişiklik yok.")

    except Exception as e:
        print("Hata:", e)

    sleep(600)  # 10 dakika bekle
