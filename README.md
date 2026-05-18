# Tanda Inspector v2

Bu paket, tango DJ'liği için kural bazlı bir MVP engine içerir.

## İçerik

- `tango_tracks_dj_enriched_v2.csv`: temizlenmiş ve DJ kolonları eklenmiş track datası
- `tanda_engine.py`: tanda skoru, uyarı motoru, sıralama ve milonga flow analizi
- `app.py`: Streamlit arayüzü
- `seed_tanda_examples_review_required.csv`: iyi/kötü/riskli örnek tanda seed datası
- `tanda_labeling_template.csv`: gerçek DJ label toplamak için boş şablon
- `track_annotation_template_first_500.csv`: ilk manuel review datası

## Çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Önemli not

Seed iyi/kötü tanda etiketleri gerçek crowd-labeled veri değildir. Bunlar tango DJ pratiğindeki genel kurallardan türetilmiş **heuristic başlangıç örnekleridir**. Gerçek ürün değerini, deneyimli DJ review'larıyla dolduracağınız `tanda_labeling_template.csv` oluşturacaktır.

## Önerilen kullanım

1. `app.py` ile Tanda Inspector'ı aç.
2. 3-4 parçalık tanda dene.
3. Warnings bölümüne bak.
4. Annotation ekranından düşük confidence kayıtları gözden geçir.
5. Gerçek DJ'lerden iyi/kötü tanda label'ı topla.
