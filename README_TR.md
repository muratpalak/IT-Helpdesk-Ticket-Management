# NexaDesk Glass — IT Helpdesk & Ticket Management (v2.0)

**Gerçekten çalışan, yerel veritabanlı bir IT yardım masası portföy projesi.** Yeni arayüz; açık, kırık beyaz bir zemin; cam etkili paneller; şeffaf kenarlar; iç/dış yumuşak gölgeler; şeftali renkli aydınlatma ve üç boyutlu oval kontroller kullanır. Tasarım, kullanıcının sağladığı minimal fiziksel anahtar/Glass UI referanslarından ilham alır.

## Mac'te tek komutla başlat

1. ZIP'i indirip açın. `IT-Helpdesk-Ticket-Management-Glass-v2` klasörünü **Masaüstü**ne taşıyın.
2. Terminal'i açıp aşağıdaki komutları çalıştırın:

```bash
cd "$HOME/Desktop/IT-Helpdesk-Ticket-Management-Glass-v2"
chmod +x START_MAC.command
./START_MAC.command
```

3. Uygulama bağımlılıkları ilk çalışmada kurar ve tarayıcınızda `http://127.0.0.1:8000` açılır (bu port doluysa 8001–8009 arasından uygun bir port seçilir).
4. Durdurmak için Terminal'de **Control + C** tuşlarına basın.

> Klasörü **İndirilenler** klasörüne çıkardıysanız birinci `cd` satırında `Desktop` yerine `Downloads` yazın. `requirements.txt` hatası alıyorsanız Terminal yanlış klasördedir. `pwd` ve `ls` ile doğrulayabilirsiniz.

## Yapabilecekleriniz

- `New request` ovaline tıklayarak destek kaydı oluşturun.
- Etki ve aciliyete göre P1–P4 önceliği ve örnek SLA hedefi otomatik hesaplanır.
- Teknik personele atayın, `Start work` ile işlem başlatın.
- `Resolution note` yazarak çözün, ardından kaydı kapatın ve gerektiğinde tekrar açın.
- Her işlem veritabanındaki **activity history**'ye kaydedilir; iç not eklenebilir.
- `In progress` ve `Completed` cam ovalleri, ilgili ticket listesi filtrelerini açar.
- Liste içinde arama, durum/öncelik/kategori filtreleri, CSV rapor ve SLA görünümü bulunur.

Veriler proje içinde otomatik oluşan `helpdesk.db` dosyasında tutulur. İlk çalıştırmada **10 kurgusal örnek kayıt** yüklenir. Tüm değişiklikleri sıfırlamak için uygulamayı kapatıp `helpdesk.db` dosyasını silin ve tekrar açın.

## Teknik yapı

| Katman | Teknoloji |
|---|---|
| Backend | Python 3, FastAPI |
| Sunucu | Uvicorn |
| Veritabanı | SQLite |
| Arayüz | HTML5, CSS3, Vanilla JavaScript |
| Testler | pytest, FastAPI TestClient |

Test için:

```bash
python3 -m pip install -r requirements.txt pytest httpx
python3 -m pytest -q
```

**Önemli:** Bu proje yalnızca demo/portföy kullanımı içindir. Kimlik doğrulama, yetkilendirme, canlı bildirim veya kurumsal entegrasyon içermez. Gerçek çalışan veya müşteri verileriyle internette yayınlamayın. SLA hedefleri örnektir, sözleşmesel garanti değildir.

### CV için Almanca açıklama

**IT Helpdesk & Ticket Management (GitHub-Portfolio-Projekt)** — Konzeption und Entwicklung einer interaktiven Service-Desk-Demo mit Ticketanlage, automatischer Priorisierung nach Auswirkung und Dringlichkeit, Technikerzuweisung, Statusübergängen, Lösungsdokumentation, SLA-Übersicht und CSV-Reporting. Technologien: Python, FastAPI, SQLite und JavaScript.
