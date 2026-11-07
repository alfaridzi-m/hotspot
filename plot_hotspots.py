#!/usr/bin/env python3
"""Plot KALIMANTAN hotspot detections on an OpenStreetMap basemap."""

import csv
from pathlib import Path

import contextily as cx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from pyproj import Transformer
from shapely import force_2d

CSV_FILE = Path(__file__).parent / "kalimantan_hotspots_20260715_20261106.csv"
KABKOTA_GDB = Path(__file__).parent / "BATASWILAYAH_KABKOTA_20260601.gdb"
KABKOTA_LAYER = "BATAS_KABKOTA_AR"
OUTPUT_WITH_RECT = Path(__file__).parent / "kalimantan_hotspots_map_with_rectangle.png"
OUTPUT_WITHOUT_RECT = Path(__file__).parent / "kalimantan_hotspots_map_without_rectangle.png"
DATA_SOURCE_URL = "https://cews.bmkg.go.id/tempatirk/HOTSPOT/"
FIG_SIZE_INCHES = 20
OUTPUT_DPI = 300
OSM_HEADERS = {
    "User-Agent": "HotspotPlot/1.0 (Kalimantan hotspot visualization; +https://openstreetmap.org)",
}
KABKOTA_EDGE_COLOR = "#222222"
KABKOTA_LINEWIDTH = 1.2

# Corners as (latitude, longitude)
AREA_CORNER_A = (0.773, 109.103)
AREA_CORNER_B = (-3.9014288933559493, 117.08655776431192)

# Rectangle corners as (latitude, longitude)
RECT_CORNER_A = (-2.6527138130618516, 112.8707315878356)
RECT_CORNER_B = (-2.4756300918918553, 113.03462273931843)
RECT2_CORNER_A = (-2.14606750909026, 113.77723868131911)
RECT2_CORNER_B = (-2.33370557508906, 114.10277025000045)

RECTANGLES = [
    (RECT_CORNER_A, RECT_CORNER_B, "Sampit", "#2ca02c"),
    (RECT2_CORNER_A, RECT2_CORNER_B, "Palangka Raya", "#1f77b4"),
]

WGS84_TO_WEB_MERCATOR = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
CONFIDENCE_COLORS = {
    7: "#2ca02c",
    8: "#ffd700",
    9: "#d62728",
}


def bounds_from_corners(corner_a: tuple[float, float], corner_b: tuple[float, float]) -> tuple[float, float, float, float]:
    lat_a, lon_a = corner_a
    lat_b, lon_b = corner_b
    return min(lat_a, lat_b), max(lat_a, lat_b), min(lon_a, lon_b), max(lon_a, lon_b)


def rectangle_latlon_vertices(
    corner_a: tuple[float, float], corner_b: tuple[float, float]
) -> list[tuple[float, float]]:
    lat_min, lat_max, lon_min, lon_max = bounds_from_corners(corner_a, corner_b)
    return [
        (lon_min, lat_min),
        (lon_max, lat_min),
        (lon_max, lat_max),
        (lon_min, lat_max),
    ]


def to_web_mercator(lons: list[float], lats: list[float]) -> tuple[list[float], list[float]]:
    xs, ys = WGS84_TO_WEB_MERCATOR.transform(lons, lats)
    return list(xs), list(ys)


def mercator_bounds_from_corners(
    corner_a: tuple[float, float], corner_b: tuple[float, float]
) -> tuple[float, float, float, float]:
    lons, lats = zip(*rectangle_latlon_vertices(corner_a, corner_b))
    xs, ys = to_web_mercator(list(lons), list(lats))
    return min(xs), max(xs), min(ys), max(ys)


def load_points_in_bbox(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> list[tuple[float, float, int]]:
    points: list[tuple[float, float, int]] = []
    with CSV_FILE.open(newline="", encoding="utf-8") as infile:
        for row in csv.DictReader(infile):
            lat = float(row["LINTANG"])
            lon = float(row["BUJUR"])
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                points.append((lon, lat, int(row["KEPERCAYAAN"])))
    return points


def load_kabkota_boundaries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(
        KABKOTA_GDB,
        layer=KABKOTA_LAYER,
        where="WADMPR LIKE 'Kalimantan%'",
    )
    gdf = gdf.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3857")
    gdf = gdf.set_geometry(gdf.geometry.map(force_2d))
    return gdf


def render_map(
    points: list[tuple[float, float, int]],
    kabkota: gpd.GeoDataFrame,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    output_file: Path,
    show_rectangle: bool,
) -> None:
    fig, ax = plt.subplots(figsize=(FIG_SIZE_INCHES, FIG_SIZE_INCHES))

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.margins(0)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    ax.set_title("Akumulasi Hotspots (Jul 15 - Nov 06, 2026)", fontsize=18, pad=14)

    cx.add_basemap(
        ax,
        crs="EPSG:3857",
        source=cx.providers.OpenStreetMap.Mapnik,
        zoom="auto",
        headers=OSM_HEADERS,
        attribution=False,
        reset_extent=False,
        zorder=0,
    )

    # add_basemap expands limits to tile bounds; restore geographic extent.
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.margins(0)

    if not kabkota.empty:
        kabkota.plot(
            ax=ax,
            facecolor="none",
            edgecolor=KABKOTA_EDGE_COLOR,
            linewidth=KABKOTA_LINEWIDTH,
            zorder=2,
        )

    if points:
        for confidence in (7, 8, 9):
            group = [(lon, lat) for lon, lat, level in points if level == confidence]
            if not group:
                continue
            lons, lats = zip(*group)
            xs, ys = to_web_mercator(list(lons), list(lats))
            ax.scatter(
                xs,
                ys,
                s=14,
                c=CONFIDENCE_COLORS[confidence],
                alpha=0.55,
                edgecolors="none",
                label=f"Kepercayaan {confidence} ({len(group)})",
                zorder=3 + confidence,
            )

    if show_rectangle:
        for corner_a, corner_b, label, color in RECTANGLES:
            rect_lons, rect_lats = zip(*rectangle_latlon_vertices(corner_a, corner_b))
            rect_xs, rect_ys = to_web_mercator(list(rect_lons), list(rect_lats))
            ax.add_patch(
                Polygon(
                    list(zip(rect_xs, rect_ys)),
                    closed=True,
                    fill=False,
                    edgecolor=color,
                    linewidth=3.5,
                    linestyle="--",
                    label=label,
                    zorder=20,
                )
            )

    handles, labels = ax.get_legend_handles_labels()
    if not kabkota.empty:
        handles.append(
            Line2D([0], [0], color=KABKOTA_EDGE_COLOR, linewidth=KABKOTA_LINEWIDTH, label="Batas Kabupaten/Kota")
        )
        labels.append("Batas Kabupaten/Kota")
    if handles:
        ax.legend(handles, labels, loc="upper left", framealpha=0.9, fontsize=12)

    ax.text(
        0.01,
        0.01,
        f"Source: {DATA_SOURCE_URL}\nSatelit: Terra, Aqua, Suomi NPP, NOAA-20",
        transform=ax.transAxes,
        fontsize=11,
        va="bottom",
        ha="left",
        color="black",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.85, "edgecolor": "none"},
        zorder=10,
    )

    fig.savefig(output_file, dpi=OUTPUT_DPI, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def main() -> None:
    lat_min, lat_max, lon_min, lon_max = bounds_from_corners(AREA_CORNER_A, AREA_CORNER_B)
    points = load_points_in_bbox(lat_min, lat_max, lon_min, lon_max)
    kabkota = load_kabkota_boundaries()
    x_min, x_max, y_min, y_max = mercator_bounds_from_corners(AREA_CORNER_A, AREA_CORNER_B)

    render_map(points, kabkota, x_min, x_max, y_min, y_max, OUTPUT_WITH_RECT, show_rectangle=True)
    render_map(points, kabkota, x_min, x_max, y_min, y_max, OUTPUT_WITHOUT_RECT, show_rectangle=False)

    print(f"Image size: {FIG_SIZE_INCHES * OUTPUT_DPI:.0f} x {FIG_SIZE_INCHES * OUTPUT_DPI:.0f} px at {OUTPUT_DPI} DPI")
    print(f"Hotspots plotted: {len(points)}")
    print(f"Kabupaten/kota boundaries: {len(kabkota)}")
    print(f"Bounding box: lat [{lat_min}, {lat_max}], lon [{lon_min}, {lon_max}]")
    print(f"Output with rectangle: {OUTPUT_WITH_RECT}")
    print(f"Output without rectangle: {OUTPUT_WITHOUT_RECT}")


if __name__ == "__main__":
    main()
