# Bilgisayar Ağları Dersi - Dönem Projesi (UDP Üzerinde Güvenilir Dosya Aktarımı)

Bu proje, UDP protokolü üzerinde çalışarak dosya aktarımını güvenilir hale getiren, Go-Back-N (Kayan Pencere) mimarisi kullanan özel bir uygulama katmanı protokolünün Python ile gerçeklenmesidir.

## Özellikler
* **Go-Back-N (Sliding Window):** Paket kayıplarına karşı pencere tabanlı yeniden iletim mekanizması.
* **Maksimum 5 Yeniden Deneme (Retry):** Paketlerin sonsuz bir döngüde yeniden gönderilmesini engeller.
* **Duplicate Paket Kontrolü:** Alıcı, çift paketleri başarıyla tanır, dosyaya mükerrer yazım yapmaz ve uygun ACK'yi döndürür.
* **MD5 Checksum:** Paket başlıklarına eklenen checksum ile veri bütünlüğü sağlanır.
* **Ağ Simülasyonu:** İstemci içerisinde istenen oranda yapay paket kaybı simülasyonu çalıştırılabilir.
* **Detaylı Loglama ve Analiz:** Her olay (Gönderim, Timeout, Yeniden İletim vb.) milisaniye hassasiyetinde kaydedilir ve `analyzer.py` aracılığıyla otomatik analiz edilir.

## Gereksinimler
Projenin doğru şekilde çalıştırılıp grafiklerin çizdirilebilmesi için aşağıdaki kütüphanelerin yüklü olması gerekmektedir:
```bash
python -m pip install pandas matplotlib
```

## Çalıştırma Adımları

Proje dosyaları üç temel modülden oluşmaktadır. Manuel olarak test etmek isterseniz şu adımları izleyebilirsiniz:

1. **Sunucuyu Başlatın:**
```bash
python server.py
```
Sunucu `127.0.0.1:8080` adresinde dinlemeye başlayacaktır.

2. **İstemciyi Başlatın:**
```bash
python client.py --file gonderilecek_dosya.txt --chunk 1024 --window 4 --timeout 0.5 --retries 5 --drop 0.1
```
*Parametreler:*
* `--file`: Gönderilecek dosyanın adı.
* `--chunk`: Paket boyutu (byte).
* `--window`: Go-Back-N pencere boyutu.
* `--timeout`: Zaman aşımı süresi (saniye).
* `--retries`: Maksimum yeniden gönderim denemesi.
* `--drop`: Yapay paket kayıp ihtimali (Örn: 0.1 = %10).

3. **Logların Analizi (İsteğe Bağlı):**
Aktarım bittikten sonra metrikleri görmek için:
```bash
python analyzer.py
```

### Otomatik Deney Senaryoları
Dönem projesinde istenen tüm deney senaryolarını (Paket boyutu, Timeout ve Kayıp oranı) otomatik çalıştırıp grafikleri çizdirmek için tek yapmanız gereken:
```bash
python run_experiments.py
```
Bu komut, rastgele dosyalar oluşturup sunucu ve istemciyi gerekli parametrelerle ardışık olarak başlatır, analizlerini gerçekleştirir ve `.png` formatında performans grafiklerini klasöre kaydeder.

## Dosya Yapısı
* `protocol.py`: Paket yapısının tanımlandığı ortak modül.
* `client.py`: Dosya aktarımı, Go-Back-N mantığı ve hata/kayıp simülasyonu sağlayan istemci.
* `server.py`: Dosyaları alan, parçaları birleştiren ve duplicate/checksum kontrolü yapan sunucu.
* `analyzer.py`: Çıkan `.csv` loglarını okuyan ve Goodput, Throughput, Retransmission Rate gibi performans verilerini hesaplayan modül.
* `run_experiments.py`: Tüm sistemi otomatik çalıştırarak grafikleri çıkaran ana test betiği.

## GitHub Deposu
Projenin kaynak kodlarına ve tüm detaylarına aşağıdaki bağlantıdan ulaşabilirsiniz:
[https://github.com/asrinaydin/NetProbe-UDP-Reliable-Transfer](https://github.com/asrinaydin/NetProbe-UDP-Reliable-Transfer)


