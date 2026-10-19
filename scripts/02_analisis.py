"""
Langkah 2 - Menghitung tingkat turnover per kelompok dan risiko relatifnya.

Risiko relatif (RR) = tingkat turnover kelompok A / tingkat turnover kelompok B.
Rentang kepercayaan 95% dihitung dengan metode logaritma. Jika rentangnya tidak
memuat angka 1, perbedaan kedua kelompok kecil kemungkinannya terjadi karena
kebetulan. Ini menunjukkan hubungan, BUKAN sebab-akibat.

Keluaran: outputs/hasil_analisis/*.csv dan outputs/ringkasan_angka.md
"""
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "data" / "processed" / "karyawan_bersih.csv")
OUT = ROOT / "outputs" / "hasil_analisis"
OUT.mkdir(parents=True, exist_ok=True)

URUTAN = {
    "kelompok_masa_kerja": ["<1 tahun", "1 tahun", "2 tahun", "3-5 tahun", "6-10 tahun", ">10 tahun"],
    "kuartil_gaji": ["Q1 (terendah)", "Q2", "Q3", "Q4 (tertinggi)"],
    "dinas_luar": ["Sering", "Jarang", "Tidak pernah"],
}


def per_kelompok(kolom):
    t = (d.groupby(kolom)["keluar"].agg(karyawan="size", resign="sum").reset_index())
    t["tingkat_turnover_persen"] = (100 * t["resign"] / t["karyawan"]).round(1)
    if kolom in URUTAN:
        t = t.set_index(kolom).loc[URUTAN[kolom]].reset_index()
    else:
        t = t.sort_values("tingkat_turnover_persen", ascending=False)
    return t


DIMENSI = ["kelompok_masa_kerja", "lembur", "departemen", "level_jabatan", "kuartil_gaji",
           "status_pernikahan", "dinas_luar", "jabatan", "kepuasan_kerja", "work_life_balance",
           "level_opsi_saham"]
for kol in DIMENSI:
    per_kelompok(kol).to_csv(OUT / f"turnover_per_{kol}.csv", index=False)

# Lembur x level jabatan
silang = d.pivot_table(index="lembur", columns="level_jabatan", values="keluar", aggfunc="mean")
(100 * silang).round(1).to_csv(OUT / "turnover_lembur_x_level.csv")


def risiko_relatif(nama, mask_a, label_a, label_b):
    a, n1 = d.loc[mask_a, "keluar"].sum(), mask_a.sum()
    c, n2 = d.loc[~mask_a, "keluar"].sum(), (~mask_a).sum()
    rr = (a / n1) / (c / n2)
    se = math.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n2)
    lo, hi = math.exp(math.log(rr) - 1.96 * se), math.exp(math.log(rr) + 1.96 * se)
    return dict(faktor=nama, kelompok_a=label_a, kelompok_b=label_b,
                turnover_a_persen=round(100 * a / n1, 1), turnover_b_persen=round(100 * c / n2, 1),
                risiko_relatif=round(rr, 2), ci95_bawah=round(lo, 2), ci95_atas=round(hi, 2))


rr = pd.DataFrame([
    risiko_relatif("Lembur", d["lembur"] == "Ya", "Lembur", "Tidak lembur"),
    risiko_relatif("Masa kerja", d["masa_kerja_tahun"] < 2, "< 2 tahun", ">= 2 tahun"),
    risiko_relatif("Gaji", d["kuartil_gaji"] == "Q1 (terendah)", "Kuartil terendah", "Kuartil lain"),
    risiko_relatif("Level jabatan", d["level_jabatan"] == 1, "Level 1", "Level 2-5"),
    risiko_relatif("Status pernikahan", d["status_pernikahan"] == "Lajang", "Lajang", "Menikah/cerai"),
    risiko_relatif("Dinas luar", d["dinas_luar"] == "Sering", "Sering", "Jarang/tidak pernah"),
    risiko_relatif("Opsi saham", d["level_opsi_saham"] == 0, "Tanpa opsi saham", "Punya opsi saham"),
]).sort_values("risiko_relatif", ascending=False)
rr.to_csv(OUT / "risiko_relatif.csv", index=False)

# Ringkasan angka utama
keluar = d[d["keluar"] == 1]
gaji_tahunan = keluar["gaji_bulanan_usd"].sum() * 12
ring = {
    "Jumlah karyawan": f"{len(d):,}",
    "Karyawan resign": f"{len(keluar):,}",
    "Tingkat turnover": f"{100 * d['keluar'].mean():.1f}%",
    "Porsi resign dengan masa kerja < 2 tahun": f"{100 * (keluar['masa_kerja_tahun'] < 2).mean():.1f}%",
    "Median gaji bulanan, resign (USD)": f"{keluar['gaji_bulanan_usd'].median():,.0f}",
    "Median gaji bulanan, bertahan (USD)": f"{d.loc[d['keluar'] == 0, 'gaji_bulanan_usd'].median():,.0f}",
    "Total gaji tahunan karyawan yang resign (USD)": f"{gaji_tahunan:,.0f}",
    "Estimasi biaya penggantian 0,5x-2x (USD)": f"{0.5 * gaji_tahunan:,.0f} - {2 * gaji_tahunan:,.0f}",
}
(ROOT / "outputs" / "ringkasan_angka.md").write_text(
    "# Ringkasan angka\n\n| Ukuran | Nilai |\n| --- | --- |\n"
    + "\n".join(f"| {k} | {v} |" for k, v in ring.items()) + "\n", encoding="utf-8")

print(pd.Series(ring).to_string())
print("\nRisiko relatif:\n" + rr.to_string(index=False))
print("\nLembur x level (%):\n" + (100 * silang).round(1).to_string())
