"""
Langkah 3 - Menyiapkan data ringkas untuk dashboard web (docs/index.html).

Data per karyawan disimpan dalam bentuk angka/indeks agar file kecil.
Dashboard menghitung semua angka di browser saat filter diubah.

Keluaran: docs/data.js
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "data" / "processed" / "karyawan_bersih.csv")
OUT = ROOT / "docs" / "data.js"

kamus = {
    "departemen": sorted(d["departemen"].unique()),
    "jabatan": sorted(d["jabatan"].unique()),
    "status_pernikahan": ["Lajang", "Menikah", "Cerai"],
    "dinas_luar": ["Sering", "Jarang", "Tidak pernah"],
}
kolom = ["departemen", "jabatan", "level_jabatan", "lembur", "status_pernikahan", "dinas_luar",
         "gaji_bulanan_usd", "masa_kerja_tahun", "kepuasan_kerja", "work_life_balance",
         "level_opsi_saham", "keluar"]
baris = []
for r in d[kolom].itertuples(index=False):
    baris.append([kamus["departemen"].index(r.departemen), kamus["jabatan"].index(r.jabatan),
                  int(r.level_jabatan), 1 if r.lembur == "Ya" else 0,
                  kamus["status_pernikahan"].index(r.status_pernikahan), kamus["dinas_luar"].index(r.dinas_luar),
                  int(r.gaji_bulanan_usd), int(r.masa_kerja_tahun), int(r.kepuasan_kerja),
                  int(r.work_life_balance), int(r.level_opsi_saham), int(r.keluar)])
data = dict(kamus=kamus,
            kolom=["dep", "jab", "level", "lembur", "status", "dinas", "gaji", "masa", "puas", "wlb", "saham", "keluar"],
            batas_kuartil_gaji=d["gaji_bulanan_usd"].quantile([0.25, 0.5, 0.75]).tolist(),
            baris=baris)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("// Dibuat otomatis oleh scripts/03_siapkan_data_dashboard.py - jangan diedit manual.\n"
               "window.DATA_TURNOVER = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n",
               encoding="utf-8")
print(f"{len(baris):,} baris -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")
