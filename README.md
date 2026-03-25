# MapBiomas Land Transition Explorer — Brazil (2008–2024)

Pixel-by-pixel rasterized land transition analysis across **133 intermediate 
geographic regions** (IBGE RG2017), derived from MapBiomas Collection 9/10.

🌐 **Live Dashboard →** https://aikiesan.github.io/MapBiomas_Data/

## Data Overview

| Item | Value |
|------|-------|
| Records | 25,474 rows |
| Regions | 133 IBGE Intermediate Regions |
| Year pairs | 2008–2024 (16 pairs) |
| Transition types | 17 |
| Pixel resolution | 30m (900 m²/pixel) |

## Project Structure

```
ABIOVE_SOJA_2026/
├── data/
│   ├── raw/                  # IBGE source XLS
│   └── processed/            # Main CSV + per-year CSVs
├── notebooks/                # Analysis notebooks (00–05)
├── scripts/                  # ArcPy raster extraction script
├── figures/                  # PNG + HTML chart outputs
└── web/                      # GitHub Pages dashboard
    └── data/                 # CSV copy for the web app
```

## Key Findings

- **Peak deforestation:** 2021–2022 (~20,500 km² Floresta → Pastagem)
- **Top region:** Sinop (MT) with 22,807 km² cumulative (2008–2024)
- **Soy expansion** operates primarily through the pasture intermediary
- Sharp deforestation reduction after 2022 (Amazon Fund reactivation)

## Funding & Attribution

- **Researcher:** Lucas Nakamura Cerejo
- **Institution:** NIPE/UNICAMP · CP2B
- **Grant:** FAPESP Process 2025/08745-2
- **Data source:** MapBiomas Collection 9 · IBGE RG2017

---
*Generated: 2026-03-25*
