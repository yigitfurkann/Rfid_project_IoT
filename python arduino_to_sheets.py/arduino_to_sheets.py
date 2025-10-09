import re, json, time, requests, serial
from requests.exceptions import ReadTimeout, RequestException
from serial.tools import list_ports

# ======= AYARLAR =======
BAUD       = 9600  # Arduino'nun seri haberleşme hızı (Arduino kodundaki Serial.begin(9600) ile aynı olmalı)
SCRIPT_URL = "Google Sheets'e Bağlantı URL'si"
# Google Apps Script'e POST gönderilecek URL (Google Sheets ile bağlantı için)

# Arduino yanıtlarını yakalamak için kalıplar # Arduino’dan gelen metinleri ayıklamak için desenler (regex kalıpları)
LINE = re.compile(r"Kullanici UID:\s*([0-9A-F]+)", re.I)  # UID'yi bulur 
OK   = "Erisim izni verildi"  # Arduino seri çıktısında bu metin varsa "yetkili" 
NO   = "Erisim izni yok"      # Bu metin varsa "yetkisiz"   

# Aynı UID için kaç saniye içinde tekrar POST yapmayalım?
DEBOUNCE_SEC = 2  

# ======= YARDIMCI FONKSİYONLAR =======
def find_arduino_port():
    """Vid/Pid ile bilinen kartları önceliklendir, yoksa ilk seri portu dene."""
    """Arduino'nun bağlı olduğu COM portu bulur."""
    cands = []
    for p in list_ports.comports():  # Bilgisayardaki tüm seri portları listele 
        vid = f"{p.vid:04X}" if p.vid else ""  # Vendor ID (Üretici Kimliği)
        pid = f"{p.pid:04X}" if p.pid else ""  # Product ID# Product ID (Ürün Kimliği)
        # Aşağıdaki VID/PID'ler Arduino Uno ve klonları içindir
        if (vid, pid) in [("1A86","7523"), ("2341","0043"), ("2A03","0043")]:
            return p.device   # Eşleşen varsa direk dön (örnek: 'COM3') 
        cands.append(p.device)
        # Hiçbiri eşleşmediyse, ilk bulduğu portu dene
    return cands[0] if cands else None

def open_serial():
    """Seri porta bağlan, port kilitliyse artan beklemeyle tekrar dene."""
    backoff = 1
    last_port_msg = None
    while True:
        port = find_arduino_port()
        if not port:
            # Arduino bulunamadıysa kullanıcıyı uyar ve bekle
            msg = "Seri cihaz bulunamadı. Kartı takın / sürücüyü kontrol edin."
            if msg != last_port_msg:
                print(msg)
                last_port_msg = msg
            time.sleep(min(backoff, 8))
            backoff = min(backoff * 2, 8)
            continue
        try:
            if port != last_port_msg:
                print("Port açılıyor:", port)
                last_port_msg = port
            ser = serial.Serial(port, BAUD, timeout=1) # Portu aç 
            print("Port bağlantısı OK:", port)
            return ser
        except PermissionError as e:
            # Eğer port başka program tarafından kullanılıyorsa 
            print(f"Port açılamadı (kilitli): {e} — Serial Monitor/Plotter vb. kapatın.")
        except Exception as e:
            print("Port açılamadı:", e)
        time.sleep(min(backoff, 8))
        backoff = min(backoff * 2, 8)
# Tek bir HTTP oturumu (performans için)
sess = requests.Session()

def warmup():
    """Google Sheets bağlantısını test eder (ilk isteği gönderir)."""
    try:
        r = sess.get(SCRIPT_URL, timeout=10)
        print("Sheets warmup:", r.status_code, r.text[:80])
    except Exception as e:
        print("Warmup hata:", e)

def post(uid, status):
    """UID ve durum bilgisini Google Sheets'e gönderir."""
    payload = {"uid": uid, "status": status, "device": "UNO-RC522"}
    for attempt in range(1, 4): # 3 defaya kadar dene 
        try:
            r = sess.post(
                SCRIPT_URL,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            print(f"{time.strftime('%H:%M:%S')} → {uid} {status} | Sheets {r.status_code} {r.text}")
            return True
        except ReadTimeout:
            print(f"POST timeout (deneme {attempt}/3) — tekrar denenecek...")
            time.sleep(1.5 * attempt)
        except RequestException as e:
            print("POST hata:", e)
            break
    return False

def pretty_status(uid, status):
    """Konsolda net bir durum satırı göster."""
    bar = "=" * 48
    if status == "AUTHORIZED":
        print(f"\n{bar}\n✅ AUTHORIZED | UID: {uid}\n{bar}\n")
    else:
        print(f"\n{bar}\n⛔ UNAUTHORIZED | UID: {uid}\n{bar}\n")

def read_lines_forever(ser):
    """Seri hattından satır oku; koparsa yeniden bağlan."""
    buffer = b""
    while True:
        try:
            chunk = ser.readline()  # Seri porttan bir satır oku 
            if not chunk:
                # bağlı ama veri yok; devam
                continue
            yield chunk.decode(errors="ignore").strip()  # Satırı dışarıya gönder 
        except (serial.SerialException, OSError):
            print("Seri bağlantı koptu, yeniden bağlanılıyor...")
            try:
                ser.close()
            except Exception:
                pass
            ser = open_serial()  # yeniden bağlan
        except Exception as e:
            print("Okuma hatası:", e)
            time.sleep(0.5)

# ======= ANA AKIŞ =======
def main():
    ser = open_serial() # Seri porta bağlan 
    warmup()             # Google Sheets bağlantısını test et 

    uid = None     # Geçici UID saklama değişkeni 
    last_sent = {}  # uid -> timestamp(son gönderim zamanı) 
    
    # Sürekli Arduino'dan veri oku
    for raw in read_lines_forever(ser):
        # Arduino’dan gelen satırı istersen ekrana basabilirsin
        # print("[SER]", raw)

        # 1️ UID satırını yakala
        m = LINE.search(raw)
        if m:
            uid = m.group(1).upper()  # UID'yi yakala ve büyük harfe çevir 
            print("UID algılandı:", uid)
            continue

        # 2️ Erişim durumu satırını yakala
        if uid and OK in raw:
            now = time.time()
            # Debounce kontrolü (aynı UID kısa sürede tekrar post edilmesin) !!!!!
            if uid not in last_sent or (now - last_sent[uid]) >= DEBOUNCE_SEC:
                pretty_status(uid, "AUTHORIZED")
                post(uid, "AUTHORIZED")  # Google Sheets'e gönder 
                last_sent[uid] = now
            else:
                # Debounce: çok hızlı tekrarı görmezden gel
                pass
            uid = None # UID sıfırla (yeni kart bekleniyor) 
        elif uid and NO in raw:
            now = time.time()
            if uid not in last_sent or (now - last_sent[uid]) >= DEBOUNCE_SEC:
                pretty_status(uid, "UNAUTHORIZED")
                post(uid, "UNAUTHORIZED")
                last_sent[uid] = now
            uid = None

# Program doğrudan çalıştırıldığında main() fonksiyonunu başlat
if __name__ == "__main__":
    main()
