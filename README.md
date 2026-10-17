# Studi Kasus: Pipeline Otomatis Peta Gempa Sumatera

Berdasarkan kuliah praktisi **"Career and Competition in Industrial Era with GIS"** oleh **Widi Primadepa**
(GIS Analyst, City Care Property, Christchurch). Pesan utamanya: lulusan Informatika unggul di GIS karena mampu
**membangun alat, mengintegrasikan sistem lewat API, dan mengotomasi alur kerja**, bukan sekadar memakai aplikasi GIS.

## Hubungan dengan materi

| Poin materi | Implementasi |
|---|---|
| Integrasi sistem lewat API | Data gempa diambil dari API USGS (GeoJSON) |
| Analisis data spasial | Jarak ke kota (haversine), kota terdekat, jarak ke Bengkulu, kelas magnitudo/kedalaman |
| Python & analisis data | `pandas` + `numpy` |
| Aplikasi web GIS | Peta interaktif Leaflet + filter magnitudo (`docs/index.html`) |
| Cloud & otomasi | GitHub Actions memperbarui data tiap 6 jam tanpa server sendiri |
| Tantangan data tersebar/tidak seragam | Data dinormalisasi ke satu skema; ada cadangan bila API gagal |

## Menjalankan

```bash
pip install -r requirements.txt
python pipeline_gempa.py      
```
link index.html  https://krbara.github.io/studi-kasus-gis-gempa/

## Pengembangan lanjutan

Menambah sumber BMKG, peta panas (*heatmap*), analisis kedekatan dengan sesar, atau menyimpan riwayat ke PostGIS.
