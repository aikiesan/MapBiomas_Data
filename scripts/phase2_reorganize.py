"""
ABIOVE_SOJA_2026 — Phase 2 Folder Cleanup
Run in Jupyter after Phase 1 completed successfully.
"""
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\Lucas\Documents\ABIOVE_SOJA_2026")

def move(src_rel, dst_rel):
    src, dst = ROOT / src_rel, ROOT / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists() and not dst.exists():
        shutil.move(str(src), str(dst))
        print(f"  📦 {src_rel}  →  {dst_rel}")
    elif dst.exists():
        print(f"  ⏭️  EXISTS: {dst_rel}")
    else:
        print(f"  ⚠️  NOT FOUND: {src_rel}")

def move_dir(src_rel, dst_rel):
    src, dst = ROOT / src_rel, ROOT / dst_rel
    if src.exists() and not dst.exists():
        shutil.move(str(src), str(dst))
        print(f"  📁 {src_rel}/  →  {dst_rel}/")
    elif dst.exists():
        print(f"  ⏭️  EXISTS: {dst_rel}/")
    else:
        print(f"  ⚠️  NOT FOUND: {src_rel}/")

print("\n══════════════════════════════════════════════════════")
print("  PHASE 2 — Reorganizing ABIOVE_SOJA_2026")
print("══════════════════════════════════════════════════════")

# ── SHAPEFILES → data/shapefiles/ ──────────────────────────────────────────
print("\n[1/7] Shapefiles...")
for folder in ["RG2017_rgint", "RG2017_rgint_20180911 (1)",
               "Biomas_250mil", "BR_Municipios_2024", "BR_UF_2024"]:
    move_dir(folder, f"data/shapefiles/{folder}")

# ── RASTER TIFs → data/rasters/coverage/ ──────────────────────────────────
print("\n[2/7] Coverage rasters (brazil_coverage_*.tif)...")
for f in sorted(ROOT.glob("brazil_coverage_*.tif")):
    move(f.name, f"data/rasters/coverage/{f.name}")

# ── TRANSITION TIFs → data/rasters/transicoes/ ────────────────────────────
print("\n[3/7] Transition rasters (Transicoes/ folder)...")
move_dir("Transicoes", "data/rasters/transicoes")

# ── GIF ANIMATIONS → figures/animations/ ─────────────────────────────────
print("\n[4/7] GIF animations...")
for f in sorted(ROOT.glob("ANIM_*.gif")):
    move(f.name, f"figures/animations/{f.name}")

# ── GIF FRAMES → figures/gif_frames/ ─────────────────────────────────────
print("\n[5/7] GIF frame folders...")
for folder in ["gif_frames", "gif_frames_Floresta_Florestal",
               "gif_frames_Mineracao", "gif_frames_Pastagem",
               "gif_frames_Savana_Cerrado"]:
    move_dir(folder, f"figures/gif_frames/{folder}")

# ── LOOSE FIGURES → figures/ ─────────────────────────────────────────────
print("\n[6/7] Loose figures at root...")
for f in ROOT.glob("*.png"):
    move(f.name, f"figures/{f.name}")
for f in ROOT.glob("HEATMAP_*.png"):
    move(f.name, f"figures/{f.name}")
for f in ROOT.glob("SANKEY_*.png"):
    move(f.name, f"figures/{f.name}")
for f in ROOT.glob("MAP_*.png"):
    move(f.name, f"figures/{f.name}")

# ── DATA FILES → data/ ────────────────────────────────────────────────────
print("\n[7/7] CSV, XLSX, data files...")

# MapBiomas statistics XLSXs → data/raw/mapbiomas/
for f in ROOT.glob("MAPBIOMAS_*.xlsx"):
    move(f.name, f"data/raw/mapbiomas/{f.name}")
move("TABELA-AGRICULTURA-MAPBIOMAS-COL9.0.xlsx",
     "data/raw/mapbiomas/TABELA-AGRICULTURA-MAPBIOMAS-COL9.0.xlsx")

# PAM data
move_dir("Dados_PAM_2024-20260323T190755Z-3-001", "data/raw/pam/Dados_PAM_2024")
move_dir("DADOS_PAM_POR_MUNICIPIO_5_CULTURAS", "data/raw/pam/DADOS_PAM_POR_MUNICIPIO_5_CULTURAS")
move("PAM_MUNICIPIOS.xlsx",      "data/raw/pam/PAM_MUNICIPIOS.xlsx")
move("TABELA_PAM.xlsx",          "data/raw/pam/TABELA_PAM.xlsx")
move("pam_rgint_foco.csv",       "data/raw/pam/pam_rgint_foco.csv")
move("pam_rgint_foco_v2.csv",    "data/raw/pam/pam_rgint_foco_v2.csv")

# MapBiomas processed CSVs → data/processed/
move("MB_col10_municipios.csv",              "data/processed/MB_col10_municipios.csv")
move("MB_nacional_cobertura_2008_2024.csv",  "data/processed/MB_nacional_cobertura_2008_2024.csv")
move("biomas_5000.csv",                      "data/processed/biomas_5000.csv")
move("MB_PAM_comparativo_RGINT.csv",         "data/processed/MB_PAM_comparativo_RGINT.csv")
move("COMPARATIVO_MB_PAM_BIOMA.csv",         "data/processed/COMPARATIVO_MB_PAM_BIOMA.csv")
move("COMPARATIVO_MB_PAM_FINAL.csv",         "data/processed/COMPARATIVO_MB_PAM_FINAL.csv")
move("DIAGNOSTICO_PRECISAO_MB_PAM.csv",      "data/processed/DIAGNOSTICO_PRECISAO_MB_PAM.csv")
move("RELATORIO_MB_PAM_ABIOVE2026.xlsx",     "data/processed/RELATORIO_MB_PAM_ABIOVE2026.xlsx")

# CSV subfolder
move_dir("CSV", "data/processed/CSV")

# Outputs folder (logs, comparativos)
move_dir("Outputs", "data/processed/Outputs")

# Duplicate/extra XLS files → data/raw/
for f in ROOT.glob("regioes_geograficas_composicao_por_municipios_2017_20180911*"):
    move(f.name, f"data/raw/{f.name}")

# MapBiomas transition ZIPs → data/raw/mapbiomas_zips/
for f in ROOT.glob("MAPBIOMAS_TRANSICOES_COL10-*.zip"):
    move(f.name, f"data/raw/mapbiomas_zips/{f.name}")

# Shapefile ZIPs
for f in ROOT.glob("*.zip"):
    move(f.name, f"data/raw/zips/{f.name}")

# Dashboard HTML
move("MapBiomas_Transition_Explorer.html", "web/index.html")

# ── UPDATE .gitignore ─────────────────────────────────────────────────────
print("\n  📝 Updating .gitignore...")
gitignore = """# ArcGIS — never commit
*.gdb/
ABIOVE2026.gdb/
Abiove_MapBiomas_Soja_2026/
*.aprx
*.atbx
*.lock
*.sr.lock
*.pyHistory

# Rasters & large raw data (local only)
data/rasters/
data/raw/mapbiomas_zips/
data/raw/zips/
data/raw/pam/Dados_PAM_2024/
data/shapefiles/BR_Municipios_2024/

# GIF frames (regenerable)
figures/gif_frames/

# Large processed CSVs
data/processed/MB_col10_municipios.csv

# Python
__pycache__/
.ipynb_checkpoints/
*.pyc
.env

# OS
.DS_Store
Thumbs.db
"""
(ROOT / ".gitignore").write_text(gitignore, encoding="utf-8")

# ── FINAL TREE ────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════════════════")
print("✅ PHASE 2 COMPLETE — Git-tracked structure:")
print("══════════════════════════════════════════════════════")
SKIP = {"ABIOVE2026.gdb", "Abiove_MapBiomas_Soja_2026",
        "data/rasters", "data/raw/mapbiomas_zips",
        "data/raw/zips", "figures/gif_frames",
        "__pycache__", ".ipynb_checkpoints"}

for p in sorted(ROOT.rglob("*")):
    if p.is_file() and not any(s in str(p) for s in SKIP):
        size = p.stat().st_size
        unit = "KB" if size < 1e6 else "MB"
        val  = size/1024 if size < 1e6 else size/1e6
        print(f"  {str(p.relative_to(ROOT)):<65} {val:>7.1f} {unit}")
