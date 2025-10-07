#include <SPI.h>       // SPI haberleşmesi için gerekli kütüphane
#include <MFRC522.h>   // RC522 RFID modülünü kontrol etmek için kütüphane

// RC522 modülünün Arduino UNO üzerindeki bağlantı pinleri
#define SS_PIN   10     // RC522 modülündeki SDA (Slave Select) pini Arduino D10'a bağlı
#define RST_PIN  9      // RC522 modülündeki RST (Reset) pini Arduino D9'a bağlı

// RC522 nesnesi oluşturulur - SS ve RST pinleri belirtilir
MFRC522 rfid(SS_PIN, RST_PIN);

// LED pinleri (görsel geri bildirim için)
#define LED_OK   2      // Yeşil LED - yetkili kartta yanacak
#define LED_ERR  7      // Kırmızı LED - yetkisiz kartta yanacak

// LED bağlantı tipi: SINK bağlantı (LOW = yanar, HIGH = söner)
#define LED_ON   LOW
#define LED_OFF  HIGH

// --------------------------------------------------------------
// Kartın UID'sini (benzersiz kimlik numarasını) HEX formatına çeviren fonksiyon
// RC522'den gelen UID verisi byte dizisidir; bunu okunabilir HEX stringe dönüştürür.
// --------------------------------------------------------------
String uidHex(const MFRC522::Uid* uid) {
  String s;
  for (byte i = 0; i < uid->size; i++) {       // UID kaç byte ise döngü o kadar çalışır
    if (uid->uidByte[i] < 0x10) s += "0";      // Tek haneli HEX değerlerin başına "0" eklenir (örnek: 0A)
    s += String(uid->uidByte[i], HEX);         // Byte değeri HEX stringe çevrilir ve stringe eklenir
  }
  s.toUpperCase();                             // Tüm harfleri büyük harfe çevirir (örnek: a54fbd02 → A54FBD02)
  return s;                                    // Dönüştürülmüş HEX string geri döndürülür
}

// --------------------------------------------------------------
// setup() fonksiyonu: Arduino açıldığında sadece 1 kez çalışır
// --------------------------------------------------------------
void setup() {
  Serial.begin(9600);     // Bilgisayarla seri haberleşme başlatılır (9600 baud hızında)
  SPI.begin();            // SPI protokolü başlatılır (MOSI, MISO, SCK pinleri etkinleşir)
  rfid.PCD_Init();        // RC522 modülü başlatılır

  // LED pinleri çıkış olarak ayarlanır
  pinMode(LED_OK, OUTPUT);
  pinMode(LED_ERR, OUTPUT);

  // LED'ler başlangıçta kapalı hale getirilir
  digitalWrite(LED_OK, LED_OFF);
  digitalWrite(LED_ERR, LED_OFF);

  // Kullanıcıya bilgi mesajı yazdırılır
  Serial.println(F("Lutfen kartinizi okutun..."));
}

// --------------------------------------------------------------
// loop() fonksiyonu: Arduino sürekli döngü halinde bu kısmı çalıştırır
// --------------------------------------------------------------
void loop() {
  // Yeni bir kart algılanmamışsa döngü başa döner
  if (!rfid.PICC_IsNewCardPresent())  return;

  // Kart algılandı ama okunamadıysa döngü başa döner
  if (!rfid.PICC_ReadCardSerial())    return;

  // Kartın UID'si alınır ve okunabilir stringe çevrilir
  String uid = uidHex(&rfid.uid);

  // Kartın UID'si Seri Monitör'e yazdırılır
  Serial.print(F("Kullanici UID: "));
  Serial.println(uid);

  // ---------------------------------------------------------
  // IF - ELSE yapısı ile kartın yetkili olup olmadığını kontrol et
  // ---------------------------------------------------------
  if (uid == "A54FBD02") {                  // 1. yetkili kart UID'si
    Serial.println(F("Erisim izni verildi! (Kart 1)")); // Ekrana mesaj yaz
    digitalWrite(LED_OK, LED_ON);           // Yeşil LED yanar
    digitalWrite(LED_ERR, LED_OFF);         // Kırmızı LED söner
  } 
  else if (uid == "0A9E4DC4") {             // 2. yetkili kart UID'si
    Serial.println(F("Erisim izni verildi! (Kart 2)"));
    digitalWrite(LED_OK, LED_ON);           // Yeşil LED yanar
    digitalWrite(LED_ERR, LED_OFF);
  } 
  else {                                    // Diğer tüm kartlar (yetkisiz)
    Serial.println(F("Erisim izni yok!"));  // Yetkisiz uyarısı
    digitalWrite(LED_OK, LED_OFF);          // Yeşil LED söner
    digitalWrite(LED_ERR, LED_ON);          // Kırmızı LED yanar
  }

  // LED'lerin 2 saniye açık kalmasını sağla
  delay(2000);

  // LED'leri kapat
  digitalWrite(LED_OK, LED_OFF);
  digitalWrite(LED_ERR, LED_OFF);

  // RFID modülünü kartla iletişimi kesmesi için bilgilendir
  rfid.PICC_HaltA();        // Kart okuma işlemini durdurur
  rfid.PCD_StopCrypto1();   // Şifreleme işlemini kapatır (modül güvenli kapanır)
}