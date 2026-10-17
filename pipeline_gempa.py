"""
Studi Kasus: Pipeline Otomatis Peta Gempa Sumatera (GIS + API + Otomasi)
Berdasarkan kuliah praktisi "Career and Competition in Industrial Era with GIS" (Widi Primadepa, GIS Analyst).

Alur (sesuai pesan materi: lulusan IT membangun alat, integrasi API, dan otomasi alur kerja):
  1. Ambil data gempa dari API USGS (GeoJSON)          -> integrasi API
  2. Olah secara spasial (jarak ke kota, kelas, dsb.)   -> analisis data spasial
  3. Bangun peta web interaktif (docs/index.html)       -> aplikasi web
  4. Dijadwalkan GitHub Actions agar diperbarui sendiri -> otomasi & cloud
Jika API tidak dapat diakses, dipakai DATA CONTOH sintetis (ditandai jelas di dashboard).
"""
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HARI, MIN_MAG = 30, 2.5
BBOX = dict(minlatitude=-7, maxlatitude=7, minlongitude=93, maxlongitude=109)  # Sumatera & sekitarnya
KOTA = {"Banda Aceh": (5.55, 95.32), "Medan": (3.59, 98.67), "Pekanbaru": (0.51, 101.45),
        "Padang": (-0.95, 100.35), "Jambi": (-1.61, 103.61), "Bengkulu": (-3.80, 102.26),
        "Palembang": (-2.98, 104.76), "Bandar Lampung": (-5.43, 105.26)}
WIB = timezone(timedelta(hours=7))
DOCS = Path("docs")


def ambil_api():
    """Ambil gempa 30 hari terakhir dari USGS. Mengembalikan DataFrame mentah."""
    end = datetime.now(timezone.utc)
    q = "&".join(f"{k}={v}" for k, v in BBOX.items())
    url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&orderby=time&limit=1000"
           f"&minmagnitude={MIN_MAG}&starttime={(end - timedelta(days=HARI)):%Y-%m-%dT%H:%M:%S}&{q}")
    req = urllib.request.Request(url, headers={"User-Agent": "studi-kasus-gis-gempa"})
    with urllib.request.urlopen(req, timeout=25) as r:
        feats = json.load(r)["features"]
    rows = [{"waktu": datetime.fromtimestamp(f["properties"]["time"] / 1000, timezone.utc),
             "mag": f["properties"]["mag"], "tempat": f["properties"]["place"] or "-",
             "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1],
             "depth": f["geometry"]["coordinates"][2]} for f in feats if f["properties"]["mag"] is not None]
    if not rows:
        raise ValueError("API tidak mengembalikan data")
    return pd.DataFrame(rows)


def data_contoh(n=180):
    """Data sintetis di sepanjang zona subduksi Sumatera (hanya untuk cadangan/uji offline)."""
    rng = np.random.default_rng(42)
    lat = rng.uniform(-6, 5, n)
    lon = 93.8 + (5 - lat) * 0.82 + rng.normal(0, 1.1, n)
    now = datetime.now(timezone.utc)
    return pd.DataFrame({
        "waktu": [now - timedelta(minutes=int(m)) for m in np.sort(rng.uniform(0, HARI * 1440, n))],
        "mag": np.round(MIN_MAG + rng.exponential(0.5, n), 1),
        "tempat": "Zona contoh (data sintetis)", "lat": lat, "lon": lon,
        "depth": np.round(rng.lognormal(3.3, 0.8, n), 1)})


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def olah(df):
    """Pengolahan spasial: kelas magnitudo/kedalaman, kota terdekat, jarak ke Bengkulu."""
    df = df.sort_values("waktu", ascending=False).reset_index(drop=True)
    jarak = pd.DataFrame({k: haversine(df.lat, df.lon, la, lo) for k, (la, lo) in KOTA.items()})
    df["kota"], df["jarak_km"] = jarak.idxmin(axis=1), jarak.min(axis=1).round(0).astype(int)
    df["jarak_bkl"] = jarak["Bengkulu"].round(0).astype(int)
    df["kelas"] = pd.cut(df.mag, [0, 4, 5, 6, 10], right=False, labels=["Minor", "Ringan", "Sedang", "Kuat"]).astype(str)
    df["waktu"] = df["waktu"].dt.tz_convert(WIB).dt.strftime("%d %b %H:%M")
    df["mag"], df["depth"] = df.mag.round(1), df.depth.round(1)
    df["lat"], df["lon"] = df.lat.round(3), df.lon.round(3)
    return df[["waktu", "mag", "depth", "lat", "lon", "tempat", "kelas", "kota", "jarak_km", "jarak_bkl"]]


def main():
    try:
        raw, sumber = ambil_api(), "USGS (data nyata)"
    except Exception as e:  # jaringan/API bermasalah -> cadangan
        print(f"[!] API gagal ({e}); memakai DATA CONTOH sintetis.")
        raw, sumber = data_contoh(), "DATA CONTOH (sintetis)"
    df = olah(raw)
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").touch()
    df.to_csv(DOCS / "gempa_olahan.csv", index=False)
    meta = {"sumber": sumber, "diperbarui": datetime.now(WIB).strftime("%d %b %Y %H:%M WIB"), "hari": HARI, "minmag": MIN_MAG}
    html = TEMPLATE.replace("__DATA__", df.to_json(orient="records")).replace("__META__", json.dumps(meta))
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"Selesai: {len(df)} gempa dari {sumber} -> docs/index.html")


TEMPLATE = r'''<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Peta Gempa Sumatera</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
:root{--ink:#111;--bg:#fffbee;--y:#ffd23f;--p:#ff9ecd;--g:#7ee8a2;--b:#7cc4ff;--r:#ff6b6b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Space Grotesk","Helvetica Neue",Arial,sans-serif;line-height:1.45}
.wrap{max-width:1280px;margin:auto;padding:28px 22px 40px}
h1{margin:0;font-size:clamp(2rem,6vw,3.6rem);font-weight:800;letter-spacing:-.03em;line-height:1}
h1 mark{background:var(--y);padding:0 .15em;border:3px solid var(--ink);box-shadow:5px 5px 0 var(--ink);display:inline-block;transform:rotate(-1.5deg)}
.sub{margin:14px 0 20px;font-weight:600;max-width:760px}
.bar{display:flex;flex-wrap:wrap;gap:12px;align-items:center;background:#fff;border:3px solid var(--ink);box-shadow:8px 8px 0 var(--ink);padding:12px 14px;margin-bottom:26px}
.bar b{font-size:.8rem;text-transform:uppercase}.bar button{font:inherit;font-weight:800;border:3px solid var(--ink);background:#fff;padding:7px 16px;cursor:pointer;box-shadow:3px 3px 0 var(--ink);transition:.1s}
.bar button:hover{transform:translate(-2px,-2px)}.bar button.on{background:var(--y);transform:translate(2px,2px);box-shadow:1px 1px 0 var(--ink)}
.tag{margin-left:auto;border:3px solid var(--ink);padding:5px 12px;font-weight:700;font-size:.82rem;background:var(--g)}.tag.warn{background:var(--r)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:22px}.s3{grid-column:span 3}.s4{grid-column:span 4}.s8{grid-column:span 8}.s6{grid-column:span 6}.s12{grid-column:span 12}
.card{background:#fff;border:3px solid var(--ink);box-shadow:7px 7px 0 var(--ink);padding:16px 18px}.card h2{margin:0 0 10px;font-size:1rem;text-transform:uppercase}
.kpi{border:3px solid var(--ink);box-shadow:6px 6px 0 var(--ink);padding:14px 16px}.kpi span{font-size:.76rem;font-weight:700;text-transform:uppercase;display:block}.kpi b{font-size:2.1rem}
#map{height:520px;border:3px solid var(--ink)}.list{max-height:520px;overflow-y:auto;border:3px solid var(--ink)}
.row{display:flex;gap:10px;align-items:center;padding:8px 10px;border-bottom:2px solid var(--ink);font-size:.82rem}.row:last-child{border:0}
.m{min-width:46px;text-align:center;font-weight:800;border:2px solid var(--ink);padding:3px 0}.row small{color:#444;display:block}
.br{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:.85rem;font-weight:600}.br i{display:block;height:20px;border:2px solid var(--ink);min-width:3px}.br span{min-width:96px}
.bkl{font-size:24px;line-height:24px;text-shadow:-1px -1px #fff,1px 1px #fff,1px -1px #fff,-1px 1px #fff;text-align:center}
.leg{display:flex;flex-wrap:wrap;gap:8px 14px;margin-bottom:12px;font-size:.8rem;font-weight:700;align-items:center}
.leg i{display:inline-block;width:16px;height:16px;border:2px solid var(--ink);border-radius:50%;vertical-align:-3px;margin-right:5px}
.how{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.how div{border:3px solid var(--ink);padding:10px 12px;font-size:.88rem;font-weight:500}
.how b{display:block;text-transform:uppercase;font-size:.78rem;margin-bottom:3px}.note{margin:14px 0 0;border:3px solid var(--ink);background:var(--r);padding:8px 12px;font-weight:700;font-size:.85rem}
ol{margin:0;padding-left:20px;font-weight:500;font-size:.9rem}ol li{margin-bottom:5px}code{background:var(--y);padding:0 4px;border:1px solid var(--ink)}
@media(max-width:860px){.s3{grid-column:span 6}.s4,.s8,.s6{grid-column:span 12}#map,.list{height:380px}}
</style></head><body><div class="wrap">
<h1>Peta <mark>Gempa</mark> Sumatera</h1>
<p class="sub">Pipeline GIS otomatis: data gempa diambil dari API, diolah secara spasial, dan diperbarui terjadwal. Studi kasus kuliah praktisi GIS (Widi Primadepa).</p>
<div class="bar"><b>Magnitudo minimum</b><button data-m="2.5" class="on">≥ 2.5</button><button data-m="3.5">≥ 3.5</button><button data-m="4.5">≥ 4.5</button><button data-m="5.5">≥ 5.5</button>
<span class="tag" id="tag"></span></div>
<div class="grid">
<div class="kpi s3" style="background:var(--b)"><span>Jumlah gempa</span><b id="k1"></b></div>
<div class="kpi s3" style="background:var(--p)"><span>Magnitudo terbesar</span><b id="k2"></b></div>
<div class="kpi s3" style="background:var(--g)"><span>≤ 300 km dari Bengkulu</span><b id="k3"></b></div>
<div class="kpi s3" style="background:var(--y)"><span>Gempa dangkal (&lt;70 km)</span><b id="k4"></b></div>
<div class="card s8"><h2>Peta interaktif</h2>
<div class="leg"><span><i style="background:#7cc4ff"></i>Minor (&lt;4)</span><span><i style="background:#7ee8a2"></i>Ringan (4–5)</span><span><i style="background:#ffd23f"></i>Sedang (5–6)</span><span><i style="background:#ff6b6b"></i>Kuat (≥6)</span><span>★ Kota Bengkulu</span><span>Ukuran lingkaran = magnitudo</span></div>
<div id="map"></div>
<p class="note" id="fnote" style="display:none;background:var(--y)">Peta dasar tidak akan tampil jika halaman dibuka langsung dari file. Buka lewat Live Server (VS Code) atau lewat link GitHub Pages.</p></div>
<div class="card s4"><h2>Gempa terbaru (WIB)</h2><div class="list" id="list"></div></div>
<div class="card s6"><h2>Sebaran kelas magnitudo</h2><div id="b1"></div></div>
<div class="card s6"><h2>Kota terdekat dari episentrum</h2><div id="b2"></div></div>
<div class="card s12"><h2>Cara membaca peta ini</h2><div class="how">
<div style="background:var(--b)"><b>1 · Apa ini?</b>Peta gempa yang sudah terjadi di sekitar Sumatera dalam 30 hari terakhir, bersumber dari USGS.</div>
<div style="background:var(--g)"><b>2 · Filter</b>Tombol magnitudo di atas menyaring gempa. Pilih ≥ 4.5 untuk hanya melihat gempa yang lebih kuat.</div>
<div style="background:var(--p)"><b>3 · Peta</b>Tiap lingkaran adalah satu gempa. Klik lingkarannya untuk melihat waktu, kedalaman, dan kota terdekat.</div>
<div style="background:var(--y)"><b>4 · Kedalaman</b>Gempa dangkal (&lt;70 km) cenderung lebih terasa di permukaan dibanding gempa yang dalam.</div></div>
<p class="note">Halaman ini hanya memetakan gempa yang sudah terjadi, bukan prakiraan (gempa tidak dapat diprediksi). Untuk informasi resmi dan peringatan dini, rujuk BMKG.</p></div>
<div class="card s12"><h2>Alur otomatis</h2><ol><li><code>pipeline_gempa.py</code> memanggil API USGS (integrasi API)</li><li>Jarak ke kota dan kelas dihitung (analisis spasial)</li><li>GitHub Actions menjalankannya terjadwal dan memperbarui halaman ini (otomasi &amp; cloud)</li></ol></div>
</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
const D=__DATA__,M=__META__,COL={Minor:'#7cc4ff',Ringan:'#7ee8a2',Sedang:'#ffd23f',Kuat:'#ff6b6b'};
const $=i=>document.getElementById(i);
const map=L.map('map').setView([-1.5,101],6);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:12,attribution:'© OpenStreetMap contributors'}).addTo(map);
if(location.protocol==='file:')$('fnote').style.display='block';
L.marker([-3.80,102.26],{icon:L.divIcon({html:'★',className:'bkl',iconSize:[24,24]})}).addTo(map).bindPopup('Kota Bengkulu');
const layer=L.layerGroup().addTo(map);let minMag=M.minmag;
$('tag').textContent=M.sumber+' · diperbarui '+M.diperbarui;$('tag').className='tag'+(M.sumber.startsWith('USGS')?'':' warn');
function bars(el,obj,colf){const mx=Math.max(1,...Object.values(obj));$(el).innerHTML=Object.entries(obj).map(([k,v])=>
`<div class="br"><span>${k}</span><i style="width:${v/mx*60}%;background:${colf(k)}"></i>${v}</div>`).join('')||'-'}
function render(){
 const f=D.filter(d=>d.mag>=minMag);layer.clearLayers();
 f.forEach(d=>L.circleMarker([d.lat,d.lon],{radius:3+d.mag*1.8,color:'#111',weight:1.5,fillColor:COL[d.kelas],fillOpacity:.8}).addTo(layer)
  .bindPopup(`<b>M ${d.mag.toFixed(1)}</b> · ${d.kelas}<br>${d.tempat}<br>${d.waktu} WIB<br>Kedalaman ${d.depth} km<br>${d.jarak_km} km dari ${d.kota}`));
 $('k1').textContent=f.length;$('k2').textContent=f.length?Math.max(...f.map(d=>d.mag)).toFixed(1):'-';
 $('k3').textContent=f.filter(d=>d.jarak_bkl<=300).length;
 $('k4').textContent=f.length?Math.round(f.filter(d=>d.depth<70).length/f.length*100)+'%':'-';
 $('list').innerHTML=f.slice(0,25).map(d=>`<div class="row"><div class="m" style="background:${COL[d.kelas]}">${d.mag.toFixed(1)}</div><div>${d.kota} · ${d.jarak_km} km<small>${d.waktu} · ${d.depth} km dalam</small></div></div>`).join('')||'<div class="row">Tidak ada data</div>';
 const kc={};['Minor','Ringan','Sedang','Kuat'].forEach(k=>kc[k]=f.filter(d=>d.kelas===k).length);bars('b1',kc,k=>COL[k]);
 const cc={};f.forEach(d=>cc[d.kota]=(cc[d.kota]||0)+1);
 bars('b2',Object.fromEntries(Object.entries(cc).sort((a,b)=>b[1]-a[1])),()=>'#ff9ecd');
}
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{minMag=+b.dataset.m;document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('on',x===b));render()});
render();
</script></body></html>'''

if __name__ == "__main__":
    main()