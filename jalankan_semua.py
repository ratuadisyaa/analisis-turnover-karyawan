"""
Menjalankan seluruh alur proyek secara berurutan:

    python jalankan_semua.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in sorted((ROOT / "scripts").glob("0*.py")):
    print(f"\n>>> {p.name}")
    subprocess.run([sys.executable, str(p)], check=True)
print("\nSelesai. Buka docs/index.html di browser untuk melihat dashboard.")
