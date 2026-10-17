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
python pipeline_gempa.py      # ambil data -> olah -> bangun docs/index.html
```

Buka `docs/index.html` di browser (perlu internet untuk peta dasar OpenStreetMap).

## Otomasi (GitHub Actions)

`.github/workflows/update.yml` menjalankan pipeline tiap 6 jam dan meng-commit hasilnya. Bisa juga dijalankan manual
dari tab **Actions → Perbarui peta gempa → Run workflow**. Aktifkan GitHub Pages dari **Settings → Pages → main, /docs**.

## Catatan penting

- Jika API tidak dapat diakses, skrip memakai **data contoh sintetis** dan dashboard menandainya dengan label merah.
  Data contoh bukan data gempa sebenarnya.
- Ini proyek pembelajaran, **bukan sumber informasi kebencanaan**. Untuk informasi resmi, rujuk BMKG.
- Lingkup data: sekitar Sumatera, 30 hari terakhir, magnitudo ≥ 2.5 (dapat diubah di bagian atas `pipeline_gempa.py`).
- GitHub menonaktifkan workflow terjadwal pada repo publik yang tidak aktif selama 60 hari.
- Karena Actions membuat commit sendiri, jalankan `git pull --rebase origin main` sebelum `git push` dari laptop.

## Pengembangan lanjutan

Menambah sumber BMKG, peta panas (*heatmap*), analisis kedekatan dengan sesar, atau menyimpan riwayat ke PostGIS.
