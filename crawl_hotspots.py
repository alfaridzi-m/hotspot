#!/usr/bin/env python3
"""Download BMKG hotspot data and export KALIMANTAN rows to a single CSV."""

import csv
import subprocess
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

BASE_URL = "https://cews.bmkg.go.id/tempatirk/HOTSPOT/{date}/hotspot_{date}.txt"
START_DATE = datetime(2026, 7, 15)
END_DATE = datetime(2026, 11, 6)
TARGET_REGION = "KALIMANTAN"
OUTPUT_FILE = Path(__file__).parent / "kalimantan_hotspots_20260715_20261106.csv"

FIELDNAMES = [
    "BUJUR",
    "LINTANG",
    "KEPERCAYAAN",
    "REGION",
    "PROVINSI",
    "KABUPATEN",
    "KECAMATAN",
    "SATELIT",
    "TANGGAL(WIB)",
    "WAKTU(WIB)",
    "RADIUS KEMUNGKINAN",
    "TIPE",
]


def date_range(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def download(url: str) -> str:
    result = subprocess.run(
        ["curl", "-sS", "-f", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"curl failed with code {result.returncode}")
    return result.stdout


def parse_and_filter(text: str) -> tuple[list[dict[str, str]], int]:
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if reader.fieldnames != FIELDNAMES:
        raise ValueError(f"Unexpected header: {reader.fieldnames}")

    total_rows = 0
    filtered_rows: list[dict[str, str]] = []
    for row in reader:
        total_rows += 1
        if row.get("REGION") == TARGET_REGION:
            filtered_rows.append(row)
    return filtered_rows, total_rows


def main() -> int:
    total_written = 0
    total_source_rows = 0
    failed_dates: list[str] = []

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        for day in date_range(START_DATE, END_DATE):
            date_str = day.strftime("%Y%m%d")
            url = BASE_URL.format(date=date_str)
            try:
                text = download(url)
                rows, source_count = parse_and_filter(text)
                writer.writerows(rows)
                total_written += len(rows)
                total_source_rows += source_count
                print(f"{date_str}: {source_count} rows, {len(rows)} KALIMANTAN")
            except Exception as exc:
                failed_dates.append(date_str)
                print(f"{date_str}: FAILED - {exc}", file=sys.stderr)

    print()
    print(f"Output: {OUTPUT_FILE}")
    print(f"Dates processed: {(END_DATE - START_DATE).days + 1 - len(failed_dates)}")
    print(f"Dates failed: {len(failed_dates)}")
    print(f"Total source rows: {total_source_rows}")
    print(f"Total KALIMANTAN rows written: {total_written}")
    if failed_dates:
        print(f"Failed dates: {', '.join(failed_dates)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
