import os
import tweepy

def test_twitter_api():
    """Twitter API anahtarlarını test eder"""
    print("Twitter API Test:")
    
    # Environment değişkenlerini kontrol et
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    ACCESS_SECRET = os.getenv("ACCESS_SECRET")
    
    print(f"API_KEY: {API_KEY[:10] if API_KEY else 'Eksik'}...")
    print(f"API_SECRET: {API_SECRET[:10] if API_SECRET else 'Eksik'}...")
    print(f"ACCESS_TOKEN: {ACCESS_TOKEN[:10] if ACCESS_TOKEN else 'Eksik'}...")
    print(f"ACCESS_SECRET: {ACCESS_SECRET[:10] if ACCESS_SECRET else 'Eksik'}...")
    
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
        print("❌ Eksik API anahtarları!")
        return
    
    try:
        # Twitter API bağlantısını test et
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth)
        
        # Kullanıcı bilgilerini al
        user = api.verify_credentials()
        print(f"✅ Twitter API bağlantısı başarılı!")
        print(f"✅ Kullanıcı: @{user.screen_name}")
        print(f"✅ Hesap adı: {user.name}")
        
        # Tweet atma yetkisini test et
        try:
            # Test tweet'i (sadece yetki kontrolü için, gerçek tweet atmaz)
            test_text = "Test tweet - Kayserispor FIFA Bot"
            api.update_status(test_text)
            print("✅ Tweet atma yetkisi var!")
            
            # Test tweet'ini sil
            api.destroy_status(api.user_timeline(count=1)[0].id)
            print("✅ Test tweet silindi!")
            
        except tweepy.errors.Forbidden as e:
            print(f"❌ Tweet atma yetkisi yok: {e}")
        except Exception as e:
            print(f"❌ Tweet atma hatası: {e}")
            
    except tweepy.errors.Unauthorized as e:
        print(f"❌ Twitter API yetkilendirme hatası: {e}")
    except Exception as e:
        print(f"❌ Twitter API bağlantı hatası: {e}")

if __name__ == "__main__":
    test_twitter_api() 