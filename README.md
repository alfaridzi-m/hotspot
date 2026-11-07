# Kalimantan Hotspot Map

Download BMKG hotspot data for Kalimantan and plot accumulations on an OpenStreetMap basemap, with kabupaten/kota boundaries and optional focus rectangles.

## Requirements

- Python 3.10+
- Internet access (to download hotspot CSV files and map tiles)

## Setup

```bash
cd /path/to/hotspot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Data

| Path | Purpose |
| --- | --- |
| `crawl_hotspots.py` output CSV | Hotspot points (lon, lat, confidence, admin fields) |
| `BATASWILAYAH_KABKOTA_20260601.gdb/` | Kabupaten/kota boundary polygons |

`plot_hotspots.py` reads the CSV path set in `CSV_FILE` (update that constant if your crawled filename differs).

### Batas wilayah kabupaten/kota (SHP / GDB)

Data batas administrasi kabupaten/kota dari **Badan Informasi Geospasial (BIG)** bisa diunduh di:

- [Drive BIG — Batas Wilayah](https://drive.big.go.id/s/9x9dJWSNfQ3wp7S?opendetails=)
- [Tanah Air Indonesia — Portal Unduh](https://tanahair.indonesia.go.id/portal-web/unduh)

Setelah diunduh, letakkan folder GDB (atau ekstrak SHP) di root proyek ini, lalu sesuaikan `KABKOTA_GDB` / `KABKOTA_LAYER` di `plot_hotspots.py` jika nama file atau layer berbeda.

## 1. Crawl hotspot data

Edit date range and output name in `crawl_hotspots.py` if needed (`START_DATE`, `END_DATE`, `OUTPUT_FILE`), then:

```bash
python3 crawl_hotspots.py
```

This downloads daily hotspot files from BMKG CEWS and writes Kalimantan rows into one CSV.

## 2. Plot the map

```bash
python3 plot_hotspots.py
```

Outputs:

- `kalimantan_hotspots_map_with_rectangle.png` — hotspots + kab/kota boundaries + focus rectangles
- `kalimantan_hotspots_map_without_rectangle.png` — hotspots + kab/kota boundaries only

Map extent, rectangle corners, and styling are configured near the top of `plot_hotspots.py`.

## Notes

- First plot run may take longer while map tiles are downloaded.
- The GDB folder is large; keep it next to `plot_hotspots.py` (or update `KABKOTA_GDB`).
