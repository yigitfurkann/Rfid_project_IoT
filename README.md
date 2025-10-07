## 🎥 Proje Tanıtım Videosu
👉 [YouTube’da İzle](https://youtube.com/shorts/GTKkeDu2JjI?feature=share)

🔐 RFID Tabanlı Erişim Kontrol Sistemi (Arduino RC522)

Bu proje, Arduino UNO ve MFRC522 RFID modülü kullanarak yetkili kartlara erişim izni veren, yetkisiz kartlarda ise uyarı LED’i yakan bir güvenlik sistemidir. Sistem, kartın benzersiz UID numarasını okuyarak kontrol yapar.

🧩 Donanım Gereksinimleri

| Bileşen                       | Açıklama                                 |
| ----------------------------- | ---------------------------------------- |
| **Arduino UNO**               | Mikrodenetleyici kart                    |
| **RC522 RFID Modülü**         | Kart okuyucu                             |
| **RFID Kart veya Anahtarlık** | Benzersiz UID’ye sahip tanımlama nesnesi |
| **LED (Yeşil & Kırmızı)**     | Erişim izni durumunu gösterir            |
| **Direnç (220Ω)**             | LED’ler için akım sınırlama              |
| **Jumper Kablolar**           | Bağlantılar için                         |

⚙️ Donanım Bağlantıları 

| RC522 Pin | Arduino UNO Pin | Açıklama            |
| --------- | --------------- | ------------------- |
| SDA (SS)  | 10              | Slave Select pini   |
| SCK       | 13              | Seri Clock          |
| MOSI      | 11              | Master Out Slave In |
| MISO      | 12              | Master In Slave Out |
| RST       | 9               | Reset pini          |
| VCC       | 3.3V            | Güç kaynağı         |
| GND       | GND             | Toprak hattı        |

💡 Yazılımın Özeti

Kodun temel çalışma prensibi:

1.Kart Algılama: RC522 modülü, yeni bir RFID kart algılandığında UID’sini okur.

2.UID Dönüşümü: UID, okunabilir HEX formatına çevrilir.

3.Erişim Kontrolü:

4.Eğer kartın UID’si önceden tanımlanmışsa → Erişim izni verilir (yeşil LED yanar)

5.Tanımlı değilse → Erişim reddedilir (kırmızı LED yanar)

6.Görsel Geri Bildirim: LED’ler 2 saniye açık kalır ve ardından söner.

7.Seri Monitör Çıkışı: Kart UID’si ve erişim durumu ekrana yazdırılır.

🧠 Önemli Fonksiyonlar

🔹 uidHex(const MFRC522::Uid* uid)

- Kart UID’sini byte dizisinden okunabilir HEX string’e dönüştürür.

- Tüm harfleri büyük harfe çevirir (örnek: a54fbd02 → A54FBD02).

🔹 loop()

- Yeni kart algılandığında UID okunur.

- UID, önceden tanımlı listede aranır ve LED’ler duruma göre yanar.


🖥️ Seri Monitör Çıktısı Örneği
  
Lutfen kartinizi okutun...
Kullanici UID: A54FBD02
Erisim izni verildi! (Kart 1)

Veya yetkisiz kartta:
Kullanici UID: 83F2C1A7
Erisim izni yok!

🛠️ Geliştirme Ortamı

Arduino IDE (v2.x veya üstü)

MFRC522 Kütüphanesi:
Arduino IDE → Araçlar > Kütüphane Yöneticisi > “MFRC522” arat > Kur
