import os
import subprocess
import json
import time
import hashlib
import hmac
import base64
import urllib.parse

def generate_oauth_signature(method, url, params, consumer_secret, token_secret):
    """OAuth 1.0a signature oluşturur"""
    # Parametreleri sırala
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params])
    
    # Signature base string oluştur
    signature_base = '&'.join([
        method.upper(),
        urllib.parse.quote(url, safe=''),
        urllib.parse.quote(param_string, safe='')
    ])
    
    # Signing key oluştur
    signing_key = '&'.join([
        urllib.parse.quote(consumer_secret, safe=''),
        urllib.parse.quote(token_secret, safe='')
    ])
    
    # HMAC-SHA1 signature oluştur
    signature = hmac.new(
        signing_key.encode('utf-8'),
        signature_base.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')

def test_twitter_api_curl():
    """cURL ile Twitter API'yi test eder"""
    print("Twitter API cURL Test:")
    
    # Environment değişkenlerini al
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    ACCESS_SECRET = os.getenv("ACCESS_SECRET")
    
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
        print("❌ Eksik API anahtarları!")
        return
    
    print(f"API_KEY: {API_KEY[:10]}...")
    print(f"API_SECRET: {API_SECRET[:10]}...")
    print(f"ACCESS_TOKEN: {ACCESS_TOKEN[:10]}...")
    print(f"ACCESS_SECRET: {ACCESS_SECRET[:10]}...")
    
    # OAuth parametreleri
    timestamp = str(int(time.time()))
    nonce = base64.b64encode(os.urandom(16)).decode('utf-8')
    
    oauth_params = {
        'oauth_consumer_key': API_KEY,
        'oauth_token': ACCESS_TOKEN,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_nonce': nonce,
        'oauth_version': '1.0'
    }
    
    # Tweet içeriği
    tweet_text = "Test tweet - Kayserispor FIFA Bot"
    
    # URL ve method
    url = "https://api.twitter.com/2/tweets"
    method = "POST"
    
    # Body parametrelerini OAuth'a ekle
    body_params = {'text': tweet_text}
    all_params = {**oauth_params, **body_params}
    
    # Signature oluştur
    signature = generate_oauth_signature(method, url, all_params, API_SECRET, ACCESS_SECRET)
    oauth_params['oauth_signature'] = signature
    
    # OAuth header oluştur
    oauth_header = 'OAuth ' + ', '.join([f'{k}="{urllib.parse.quote(v, safe="")}"' for k, v in oauth_params.items()])
    
    # cURL komutu oluştur
    curl_command = [
        'curl', '-X', 'POST',
        '-H', f'Authorization: {oauth_header}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(body_params),
        url
    ]
    
    print(f"\ncURL komutu:")
    print(' '.join(curl_command))
    
    try:
        # cURL komutunu çalıştır
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        
        print(f"\nStatus Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
            
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                if 'data' in response_data:
                    print("✅ Tweet başarıyla atıldı!")
                    print(f"Tweet ID: {response_data['data']['id']}")
                else:
                    print("❌ Tweet atılamadı:")
                    print(response_data)
            except json.JSONDecodeError:
                print("❌ JSON parse hatası")
                print(result.stdout)
        else:
            print("❌ cURL hatası")
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout hatası")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")

if __name__ == "__main__":
    test_twitter_api_curl() 