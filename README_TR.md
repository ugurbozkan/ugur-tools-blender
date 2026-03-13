# Ugur Tools - Blender Eklentisi

Ugur Tools, Blender'da 3D baskı iş akışını basitleştirmek ve hızlandırmak için tasarlanmış kapsamlı bir eklentidir. Ölçüm araçları, hizalama işlemleri, boolean işlemler ve gelişmiş çizim özellikleri ile profesyonel 3D modelleme ve hazırlama sürecini kolaylaştırır.

## Temel Bilgiler

- **Eklenti Adı:** Ugur Tools
- **Yazar:** Ugur Bozkan
- **Sürüm:** 2.13.0
- **Blender Sürümü:** 5.0 ve üzeri
- **Lisans:** GPL-3.0
- **Konum:** View3D > Sidebar > Ugur Tools

## Özellikler

Ugur Tools beş ana sekme altında organize edilmiş geniş bir özellik seti sunar:

### 1. Araçlar (Tools) Sekmesi

Temel ölçüm ve dönüştürme araçlarını içerir.

#### Ölçüm Yönetimi
- **Ölçümleri Göster/Gizle:** Tüm ölçümlerin görünürlüğünü kontrol etmek için toggle
- **Ölçü Birimi Seçici:** Millimetre (mm), Santimetre (cm) veya Metre (m) arasında seçim yapın
- **Blender Birim Sistemi Desteği:** Metric ve Imperial birimler tam olarak desteklenir

#### Ölçüm Araçları
- **Tape Measure:** Noktalar arasındaki mesafeyi ölçmek için geleneksel şerit ölçüsü
- **Line Measure:** Çizgi üzerinde mesafe ölçümü yapma
- **Guide Line:** Referans çizgileri oluşturma ve görüntüleme
- **BBox Overlay:** Sınırlayıcı kutu üzerinde boyutları görüntüleme

#### Boyutlar (Dimensions)
- X, Y, Z eksenlerinde nesne boyutlarını görüntüleyin
- Seçili nesnelerin ölçülerini gerçek zamanlı olarak takip edin

#### Dönüştürme Kontrolü
- **Manuel Açı Girişi:** Tam doğrulukla özel dönüş açıları belirtin
- **Dönüş Yönü Toggle:** Saat yönünde (CW) ve saat yönünün tersine (CCW) dönüş seçenekleri
- **Hızlı Döndürme:** 45 derece ve 90 derece hızlı döndürme düğmeleri

### 2. Hizala (Align) Sekmesi

Nesneleri hassas bir şekilde konumlandırmak ve düzenlemek için kapsamlı hizalama araçları.

#### Aynalama (Mirror)
- X, Y, Z eksenlerinde nesne aynalama işlemleri
- Hızlı simetrik nesne oluşturma

#### Hizalama İşlemleri
- **Aktife Göre Hizala:** Seçili nesneleri aktif nesnenin X, Y, Z konumuna hizala
- **Boşluk Eşitle:** 3 veya daha fazla nesneyi eşit aralıklarla dağıt ve organize et
- **Yüzey Hizalama:** İki yüzeye sırasıyla tıklayarak nesneleri otomatik olarak hizala
- **Yüzeyi Eksene Hizala:** Seçilen yüzeyi X, Y veya Z eksenine hizala

#### Zemin İşlemleri
- **Zemine Düşür:** Nesneleri en alttaki yüzeyden zemine konumlandır
- **Zemine Yatır:** Nesneleri düz bir şekilde zemine yerleştir

#### Nokta Hizalama
- İki nokta arasında nesne hizalama ve konumlandırma
- Hassas nesne yerleştirme için ideal

### 3. Boolean Sekmesi

Karmaşık 3D geometri oluşturmak için boolean işlemleri ve delme araçları.

#### Boolean İşlemleri
- **Çıkart (Difference):** Seçilen nesneleri aktif nesneden çıkarma
- **Birleştir (Union):** Nesneleri birleştirme ve birleşik geometri oluşturma

#### Delik Delme Araçları
- **Yüzeye Tıklayarak Delik Del:** Yüzeyi seçip delik açma - Delik çapı ayarlanabilir - Delik derinliği kontrol edilebilir - Segment sayısı özelleştirilebilir
- **Cursor'a Delik:** 3D Cursor konumunda otomatik olarak delik oluştur
- **Seçili Nesneleri Del:** Birden fazla nesneyi aynı anda delme - Kurşun etkisi ile keskin delişler - Toplu delik işlemi desteği

#### Segment Ayarları
- 4 segment = kare delikler
- 6 segment = altıgen delikler
- 32 segment = dairesel delikler
- Özel segment sayıları desteklenir

### 4. Cursor (Cursor) Sekmesi

3D Cursor'u hassas bir şekilde konumlandırmak için araçlar.

#### Cursor Konumlandırma
- **Edit Mode:** Seçili yüzey merkezine cursor yerleştir
- **Seçili Noktalar:** Seçilen noktaların merkez noktasına cursor taşı
- **Yüzeye Tıkla:** Object modda herhangi bir yüzeye tıklayarak cursor konumlandır

#### Guide Kesişimi
- İki guide çizgisinin kesişim noktasına cursor otomatik olarak taşınır
- Referans çizgileri ile hassas konumlandırma

### 5. Çiz (Draw) Sekmesi

SketchUp tarzı edit mode çizim aracı ile hızlı modelleme.

#### Çizim Özellikleri
- **Edit Mode Çizimi:** Köşeleri, kenarları ve yüzeyleri hızlıca çizin
- **Snap Desteği:** Vertex snap - köşelere yapışma, Midpoint snap - kenar orta noktalarına yapışma, Edge snap - kenarlara yapışma, Face snap - yüzeylere yapışma

#### Gelişmiş Özellikler
- **Eksen Kilitleme:** X, Y, Z eksenine kilitlenmiş çizim
- **Sayısal Mesafe Girişi:** Kesin mesafeler belirleyin
- **Knife-Cut İşlemleri:** Kenar bölme, Yüzey bölme

## Teknik Özellikleri

### Ölçüm ve Hesaplama
- Alan hesaplama
- Uzunluk ölçümü
- Mesafe hesaplama
- Edit mode'da gerçek zamanlı bilgi gösterimi

### Kalıcı Ölçümler
- Ölçümler .blend dosyasıyla kaydedilir
- Dosya kapatıp açıldıktan sonra da ölçümler korunur

### Snap Sistemi
- Vertex snap
- Midpoint snap
- Edge snap
- Face snap

## Kurulum

### Adım 1: Eklentiyi İndir
Ugur Tools eklentisini Blender eklenti deposundan veya doğrudan kaynak dosyasından indirin.

### Adım 2: Blender'da Yükle
1. Blender'ı açın (sürüm 5.0 veya daha yeni)
2. **Edit > Preferences** menüsüne gidin
3. **Add-ons** sekmesine tıklayın
4. **Install...** düğmesine tıklayın
5. İndirdiğiniz eklenti dosyasını seçin
6. **Install Add-on** düğmesine tıklayın

### Adım 3: Etkinleştir
1. Arama kutusuna "Ugur Tools" yazın
2. Eklentiyi bulun ve etkinleştirmek için checkbox'ı işaretleyin

### Adım 4: Erişim
Eklenti yüklendiğinde 3D Viewport'un sağ tarafındaki Sidebar'da **Ugur Tools** paneli görünür. Not: Sidebar görmüyorsanız N tuşuna basarak açın.

## Kullanım Kılavuzu

### Ölçüm Araçlarını Kullanma
1. Toolbar sekmesine gidin
2. İstediğiniz ölçü birimini seçin (mm, cm veya m)
3. Ölçümleri Göster toggle'ını açın
4. Kullanmak istediğiniz ölçüm aracını seçin (Tape Measure, Line Measure vb.)
5. 3D görünümde ölçümleri gerçekleştirin

### Boolean İşlemleri İçin
1. Boolean sekmesine gidin
2. Esas nesneyi seçin
3. Özel nesneyi Shift+Click ile ekleyin (aktif hale gelmez)
4. İstenilen Boolean işlemini seçin (Çıkart veya Birleştir)
5. Sonucu inceleyin

### Delik Delme İçin
1. Boolean sekmesinde Delik Delme bölümüne gidin
2. Delik çapını ve derinliğini ayarlayın
3. Segment sayısını seçin (kare, altıgen, daire vb.)
4. "Yüzeye Tıklayarak Delik Del" seçeneğini etkinleştirin
5. 3D görünümde delik istediğiniz yüzeye tıklayın

### Nesneleri Hizalamak İçin
1. Hizala sekmesine gidin
2. Hizalanacak nesneleri seçin
3. Referans nesnesini aktif yapın (terakhir seçilen veya Shift+Click)
4. Uygun hizalama seçeneğini seçin
5. Sonuç otomatik olarak uygulanır

### Çizim Aracını Kullanmak
1. Çiz sekmesine gidin
2. Edit mode'a geçin (Tab tuşu)
3. Başlangıç noktasına tıklayın
4. Snap seçeneklerini etkinleştirin
5. Ek noktalara tıklayarak çizin
6. Mesafeleri sayısal olarak girin (isteğe bağlı)
7. Eksen kilitleme kullanarak doğru yönler oluşturun

## 3D Baskı İş Akışı

Ugur Tools özellikle 3D baskı için modelleri hazırlamak üzere tasarlanmıştır:

### Model Hazırlama
1. Ölçüm araçlarını kullanarak boyutları kontrol edin
2. Nesneleri zemine hizalayın (Zemine Düşür)
3. Gerekli deşikleri ve özellikleri ekleyin (Boolean > Delik Delme)
4. Hizalama araçlarını kullanarak baskı yönünü optimize edin

### Geometri Kontrol
1. BBox Overlay ile sınırlayıcı kutuyu görmek için araç kullanın
2. Boyut sekmesinde X, Y, Z boyutlarını doğrulayın
3. Guide çizgileri ile referans çizgiler oluşturun

### Son Kontrol
1. Tüm boolean işlemlerin doğru uygulandığından emin olun
2. Alan ve hacim bilgilerini kontrol edin
3. Nesne konumlandırmasını son kez doğrulayın

## Dosya Yapısı

blender_tools/ ├── __init__.py ├── snap_utils.py ├── tape_measure.py ├── line_measure.py ├── bbox_measure.py ├── bbox_scale.py ├── guide_measure.py └── draw_tool.py

## Kısayollar ve İpuçları

### Kullanışlı Klavye Kısayolları
- **N tuşu:** Sidebar'ı aç/kapat
- **Tab tuşu:** Object mode ve Edit mode arasında geçiş yap
- **Shift+Click:** Nesne seçimine ekle
- **X tuşu:** Seçili nesneyi sil

### İş Akışı İpuçları
1. Cursor konumlandırmasını sık kullanın - hassas modelleme için önemlidir
2. Guide çizgilerini referans olarak kullanın
3. Boolean işlemler yapmadan önce nesneleri dönüştürün
4. Ölçümleri kaydetmek için dosyayı .blend olarak kaydedin
5. Snap sistemi etkinken elde edilen doğruluk daha yüksek olur

## Sorun Giderme

### Sidebar Görünmüyor
- N tuşuna basarak Sidebar'ı açın
- View > Sidebar menüsünü kontrol edin

### Ölçümler Gösterilmiyor
- Toolbar sekmesine gidin
- "Ölçümleri Göster" toggle'ını işaretleyin
- Görüş açısını ayarlayın (ölçümler bazı açılarda gizli olabilir)

### Boolean İşlemi Başarısız
- Nesnelerin geometrisinin temiz olduğundan emin olun
- Nesneleri manifold olacak şekilde düzenleyin
- Dönüştürme işlemlerini uygulayın (Ctrl+A > All Transforms)

### Snap Çalışmıyor
- Boolean sekmesinde snap seçeneklerini kontrol edin
- Edit mode'da olduğunuzdan emin olun
- Görünür snap noktaları olduğundan emin olun

## Lisans

Ugur Tools GPL-3.0 lisansı altında dağıtılmaktadır. Kaynak kodunu kopyalayabilir, değiştirebilir ve dağıtabilirsiniz, ancak aynı lisansı kullanmanız gerekir.

## Geri Bildirim ve Destek

Hataları bildirmek, özellik isteklerinde bulunmak veya katkıda bulunmak için lütfen geliştirici ile iletişime geçin.

## Sürüm Geçmişi

### Sürüm 2.13.0
- Blender 5.0 uyumluluğu
- Tüm temel özellikler kararlı ve test edilmiş
- Geliştirilmiş snap sistemi
- Optimize edilmiş UI/UX

## Teşekkürler

Ugur Tools'u kullanan ve geri bildirim sağlayan tüm kullanıcılara teşekkürler.

---

**Son Güncelleme:** 2026
**Yazar:** Ugur Bozkan
**Lisans:** GPL-3.0
