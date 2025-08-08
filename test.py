import os
import requests
import json

def test_environment():
    """Environment değişkenlerini test eder"""
    required_vars = ["API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_SECRET"]
    
    print("Environment Değişkenleri Kontrolü:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}...")
        else:
            print(f"❌ {var}: Eksik!")
    
    print("\nFIFA API Test:")
    try:
        url = "https://knowledge.fifa.com/api/fkmpdatahub/fifadatahubtransfer/registrationBans"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            content = response.text
            print(f"Response Content (first 500 chars): {content[:500]}")
            
            try:
                data = response.json()
                if isinstance(data, list):
                    kayseri_count = sum(1 for item in data if isinstance(item, dict) and item.get("club_in") == "KAYSERISPOR FUTBOL A.S.")
                    print(f"✅ FIFA API çalışıyor. Kayserispor dosya sayısı: {kayseri_count}")
                else:
                    print(f"❌ Beklenmeyen veri formatı. Data type: {type(data)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing hatası: {e}")
                print(f"Response content: {content}")
        else:
            print(f"❌ FIFA API hatası: {response.status_code}")
    except Exception as e:
        print(f"❌ FIFA API bağlantı hatası: {e}")

if __name__ == "__main__":
    test_environment() 