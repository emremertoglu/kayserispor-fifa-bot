# Kayserispor Botu

Bu bot, FIFA'nın public API'sinden "KAYSERISPOR FUTBOL A.S." kayıt yasağı sayısını takip eder. Sayı değişirse Twitter'da paylaşır.

## Kurulum
1. Twitter Developer hesabı aç ve API anahtarlarını al (Read/Write yetkili).
2. Railway hesabı oluştur.
3. Bu projeyi GitHub'a yükle.
4. Railway'e GitHub'dan bağla.
5. Environment Variables ekle:
   - API_KEY
   - API_SECRET
   - ACCESS_TOKEN
   - ACCESS_SECRET
6. Deploy et.

Bot her 10 dakikada bir kontrol yapar.
