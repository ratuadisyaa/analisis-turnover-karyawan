"""
Langkah 1 - Memeriksa kualitas data dan menyiapkan data untuk analisis.

Sumber: IBM HR Analytics Employee Attrition (data fiktif buatan IBM),
https://github.com/IBM/employee-attrition-aif360 (lisensi Apache 2.0).

Keluaran:
  data/processed/karyawan_bersih.csv   data siap analisis (kolom berbahasa Indonesia)
  outputs/laporan_kualitas_data.md     hasil pemeriksaan kualitas data
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "ibm_hr_attrition.csv"
OUT = ROOT / "data" / "processed" / "karyawan_bersih.csv"
LAPORAN = ROOT / "outputs" / "laporan_kualitas_data.md"

df = pd.read_csv(RAW, encoding="utf-8-sig")

# ------------------------------------------------ pemeriksaan kualitas data --
cek = [
    ("Jumlah baris", len(df)),
    ("Jumlah kolom", df.shape[1]),
    ("Nilai kosong (semua kolom)", int(df.isna().sum().sum())),
    ("ID karyawan ganda", int(df["EmployeeNumber"].duplicated().sum())),
    ("Baris ganda", int(df.duplicated().sum())),
]
konstan = [c for c in df.columns if df[c].nunique() == 1]
cek.append(("Kolom bernilai tunggal (dibuang)", ", ".join(konstan)))

# ------------------------------------------------------- pilih & terjemahkan --
KOLOM = {
    "EmployeeNumber": "id_karyawan", "Age": "usia", "Attrition": "resign", "Department": "departemen",
    "JobRole": "jabatan", "JobLevel": "level_jabatan", "OverTime": "lembur",
    "MaritalStatus": "status_pernikahan", "BusinessTravel": "dinas_luar",
    "MonthlyIncome": "gaji_bulanan_usd", "YearsAtCompany": "masa_kerja_tahun",
    "YearsSinceLastPromotion": "tahun_sejak_promosi", "JobSatisfaction": "kepuasan_kerja",
    "WorkLifeBalance": "work_life_balance", "StockOptionLevel": "level_opsi_saham",
    "DistanceFromHome": "jarak_rumah_km",
}
d = df[list(KOLOM)].rename(columns=KOLOM)
d["resign"] = d["resign"].map({"Yes": "Ya", "No": "Tidak"})
d["lembur"] = d["lembur"].map({"Yes": "Ya", "No": "Tidak"})
d["departemen"] = d["departemen"].map({"Research & Development": "Riset & Pengembangan",
                                       "Sales": "Penjualan", "Human Resources": "SDM"})
d["status_pernikahan"] = d["status_pernikahan"].map({"Single": "Lajang", "Married": "Menikah", "Divorced": "Cerai"})
d["dinas_luar"] = d["dinas_luar"].map({"Non-Travel": "Tidak pernah", "Travel_Rarely": "Jarang",
                                       "Travel_Frequently": "Sering"})
assert d.notna().all().all(), "Ada nilai yang gagal diterjemahkan"

# ------------------------------------------------------------ kolom turunan --
d["keluar"] = (d["resign"] == "Ya").astype(int)
d["kelompok_masa_kerja"] = pd.cut(d["masa_kerja_tahun"], [-1, 0, 1, 2, 5, 10, 100],
                                  labels=["<1 tahun", "1 tahun", "2 tahun", "3-5 tahun", "6-10 tahun", ">10 tahun"])
batas = d["gaji_bulanan_usd"].quantile([0.25, 0.5, 0.75]).tolist()   # sama dengan PERCENTILE di Excel
d["kuartil_gaji"] = pd.cut(d["gaji_bulanan_usd"], [0, *batas, float("inf")],
                           labels=["Q1 (terendah)", "Q2", "Q3", "Q4 (tertinggi)"])

OUT.parent.mkdir(parents=True, exist_ok=True)
d.to_csv(OUT, index=False)

LAPORAN.parent.mkdir(parents=True, exist_ok=True)
LAPORAN.write_text(
    "# Laporan kualitas data\n\n| Pemeriksaan | Hasil |\n| --- | --- |\n"
    + "\n".join(f"| {a} | {b} |" for a, b in cek)
    + f"\n\nBatas kuartil gaji bulanan (USD): {', '.join(f'{b:,.0f}' for b in batas)}.\n"
    + f"Kolom yang dipakai untuk analisis: {len(KOLOM)} dari {df.shape[1]}.\n",
    encoding="utf-8")
print(LAPORAN.read_text(encoding="utf-8"))
print(f"Tersimpan -> {OUT.relative_to(ROOT)} ({len(d):,} baris)")
