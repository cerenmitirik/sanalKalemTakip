OpenCV ve MediaPipe kütüphanelerini kullanarak web kamerası üzerinden el hareketleriyle kontrol edilen interaktif bir Sanal Yazı Tahtası (Virtual Whiteboard) ve Donanım Kontrol Sistemi uygular.

Temel Özellikler ve Çalışma Mantığı
Elin ve Parmakların Tespiti: MediaPipe ile görüntüdeki el eklemleri (landmarks) ve parmakların açık/kapalı olma durumları gerçek zamanlı analiz edilir.

Çizim ve Renk Seçimi:

İşaret Parmağı: Üstteki renk butonlarına (Kırmızı, Yeşil, Mavi, Silgi) dokunarak seçim yapar; tuval üzerinde ise çizim/silme işlemi gerçekleştirir.

Kalınlık ve Ekran Parlaklığı Ayarı: İki farklı yöntemle kontrol edilir:

Cımbız Hareketi (Başparmak + İşaret Parmağı Arası Mesafe): Ekranın solunda kalem kalınlığını, sağında ise sistem parlaklığını (screen_brightness_control ile) ayarlar.

Arayüz Kaydırma Çubukları (Slider): İşaret parmağı ile sağdaki parlaklık veya soldaki kalınlık çubukları yukarı/aşağı kaydırılabilir.

Özel El Hareketleri (Jestler):

2 Parmak (1 sn basılı tutma): Siyah ekran modunu açar.

3 Parmak: Siyah ekran modundan çıkar.

5 Parmak Açık (1.8 sn basılı tutma): O anki tuval ve kamera görüntüsünü birleştirip ekran görüntüsü (.png) olarak kaydeder.

Çoklu El Desteği: İki el aynı anda bağımsız olarak takip edilir ve koordinat/durum çakışmaları engellenir.
