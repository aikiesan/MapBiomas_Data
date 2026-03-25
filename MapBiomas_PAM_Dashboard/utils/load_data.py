"""
Data loading and transformation layer for the MapBiomas × PAM dashboard.

All public functions are cached with @st.cache_data so they run only once
per Streamlit session.

Data paths are resolved relative to the repository root (ABIOVE_SOJA_2026/),
which is two levels above this file (utils/ → MapBiomas_PAM_Dashboard/ → repo root).
"""

from __future__ import annotations

import csv
import pathlib
from functools import lru_cache
from typing import Any

import pandas as pd
import streamlit as st

from utils.constants import (
    PAM_CROP_MAP,
    TRANSITION_TO_GROUP,
    UF_DICT,
)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parents[2]  # ABIOVE_SOJA_2026/
_DATA_ROOT = _REPO_ROOT / "data"

_MB_CSV = _DATA_ROOT / "processed" / "transicoes_regioes_int.csv"
_PAM_DIR = _DATA_ROOT / "raw" / "pam" / "DADOS_PAM_POR_MUNICIPIO_5_CULTURAS"
_XLS_LOOKUP = (
    _DATA_ROOT
    / "raw"
    / "regioes_geograficas_composicao_por_municipios_2017_20180911.xls"
)


# ---------------------------------------------------------------------------
# PAM CSV parsing helpers (module-level, not cached individually)
# ---------------------------------------------------------------------------

def _parse_pam_csv(filepath: pathlib.Path) -> pd.DataFrame:
    """
    Parse one IBGE-style wide-format PAM CSV file.

    Structure:
        Line 0: Title (skip)
        Line 1: Variable name (skip)
        Line 2: Column group header (skip)
        Line 3: Year row — e.g. "Nível";"Cód.";"Município";"2022";"";"";...
        Line 4: Crop row  — e.g. "Nível";"Cód.";"Município";"Soja";...
        Line 5+: Data rows — "MU";"1100015";"Alta Floresta...";value;...

    The year row has merged cells (blanks between year changes); we forward-fill
    the year value to align one year per crop column.

    Returns a long-format DataFrame with columns:
        cd_geocodigo (str), municipio (str), ano (int), cultura (str), area_ha (float)
    """
    # Files are UTF-8 with BOM; utf-8-sig strips the BOM automatically.
    enc = "utf-8-sig"

    with open(filepath, encoding=enc, errors="replace") as fh:
        raw_lines = fh.readlines()

    def _parse_row(line: str) -> list[str]:
        return next(csv.reader([line.strip()], delimiter=";"))

    year_row = _parse_row(raw_lines[3])
    crop_row = _parse_row(raw_lines[4])

    # Forward-fill year values (numeric only) and pad to crop_row length
    ffilled_years: list[str] = []
    current_year: str | None = None
    for val in year_row:
        s = val.strip()
        if s.isdigit():
            current_year = s
        ffilled_years.append(current_year or val)

    while len(ffilled_years) < len(crop_row):
        ffilled_years.append(current_year)

    # Build (year, crop) tuples for data columns (skip first 3 meta columns)
    col_tuples: list[tuple[str, str]] = list(
        zip(ffilled_years[3:], crop_row[3:])
    )

    # Read the data block (skip 5 header rows)
    data = pd.read_csv(
        filepath,
        sep=";",
        header=None,
        skiprows=5,
        encoding="utf-8-sig",
        encoding_errors="replace",
        on_bad_lines="skip",
        dtype=str,
    )

    # Drop rows that don't look like municipality data
    # (some files have trailing notes)
    data = data[data.iloc[:, 0].str.strip().isin(["MU", '"MU"'])]
    # Strip quotes from all string columns
    data = data.apply(lambda col: col.str.strip('"') if col.dtype == object else col)

    # Assign column names
    n_data_cols = len(col_tuples)
    n_actual = len(data.columns) - 3
    if n_actual < n_data_cols:
        col_tuples = col_tuples[:n_actual]
    elif n_actual > n_data_cols:
        # Extra trailing columns — pad with last year/unknown
        extra = n_actual - n_data_cols
        for _ in range(extra):
            col_tuples.append((current_year or "?", "unknown"))

    _SEP = "__YR__"
    data.columns = ["nivel", "cd_geocodigo", "municipio"] + [
        f"{yr}{_SEP}{crop}" for yr, crop in col_tuples
    ]
    data = data[["cd_geocodigo", "municipio"] + [c for c in data.columns if _SEP in c]]

    # Melt wide → long
    long = data.melt(
        id_vars=["cd_geocodigo", "municipio"],
        var_name="yr_crop",
        value_name="area_ha_raw",
    )
    split = long["yr_crop"].str.split(_SEP, n=1, expand=True)
    long["ano_str"] = split[0]
    long["cultura_raw"] = split[1]

    # Map raw crop names to internal keys; drop unmapped / unknown
    long["cultura"] = long["cultura_raw"].map(PAM_CROP_MAP)
    long = long.dropna(subset=["cultura"])

    # Convert area: "-" or blank → NaN → 0
    long["area_ha"] = (
        pd.to_numeric(long["area_ha_raw"].str.replace(".", "", regex=False)
                        .str.replace(",", ".", regex=False)
                        .str.strip()
                        .replace("-", None),
                      errors="coerce")
        .fillna(0.0)
    )

    long["ano"] = pd.to_numeric(long["ano_str"], errors="coerce").astype("Int64")
    long = long.dropna(subset=["ano"])

    return long[["cd_geocodigo", "municipio", "ano", "cultura", "area_ha"]].copy()


@lru_cache(maxsize=1)
def _load_region_lookup() -> pd.DataFrame:
    """
    Load the municipality → intermediate region XLS lookup.
    Returns DataFrame with columns: cd_geocodi (str, 7-digit), cod_rgint (int), nome_rgint (str).
    """
    df = pd.read_excel(_XLS_LOOKUP, engine="xlrd", dtype=str)
    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={"cd_geocodi": "cd_geocodi", "cod_rgint": "cod_rgint", "nome_rgint": "nome_rgint"})
    df["cd_geocodi"] = df["cd_geocodi"].str.strip().str.zfill(7)
    df["cod_rgint"] = pd.to_numeric(df["cod_rgint"], errors="coerce").dropna().astype(int)
    return df[["cd_geocodi", "cod_rgint", "nome_rgint"]].drop_duplicates("cd_geocodi")


# ---------------------------------------------------------------------------
# Public cached loaders
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando transições MapBiomas…")
def load_transitions() -> pd.DataFrame:
    """
    Load and enrich the main transitions CSV.

    Added columns:
        uf        (str)  — state code from first 2 digits of zona_id
        uf_name   (str)  — state code repeated (full name in UF_NAMES constant)
        transition_group (str) — group label from TRANSITION_GROUPS
    """
    df = pd.read_csv(_MB_CSV, dtype={"zona_id": int, "n_pixels": int})

    # UF derivation
    uf_codes = (df["zona_id"] // 100).astype(int)
    df["uf"] = uf_codes.map(UF_DICT).fillna("??")

    # Transition group
    df["transition_group"] = df["transicao"].map(TRANSITION_TO_GROUP).fillna("other")

    # Ensure numeric area
    df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce")

    return df


@st.cache_data(show_spinner="Processando dados PAM por região…")
def load_pam_by_region() -> pd.DataFrame:
    """
    Parse all 6 PAM wide-format CSVs, aggregate to intermediate region level.

    Output columns:
        cod_rgint (int), nome_rgint (str), ano (int),
        cultura (str), area_ha (float)
    """
    lookup = _load_region_lookup()

    frames: list[pd.DataFrame] = []
    for csv_path in sorted(_PAM_DIR.glob("*.csv")):
        chunk = _parse_pam_csv(csv_path)
        frames.append(chunk)

    if not frames:
        return pd.DataFrame(columns=["cod_rgint", "nome_rgint", "ano", "cultura", "area_ha"])

    pam = pd.concat(frames, ignore_index=True)

    # Normalise cd_geocodigo to 7-digit string
    pam["cd_geocodigo"] = pam["cd_geocodigo"].str.strip().str.zfill(7)

    # Join with region lookup
    merged = pam.merge(lookup, left_on="cd_geocodigo", right_on="cd_geocodi", how="left")
    merged = merged.dropna(subset=["cod_rgint"])
    merged["cod_rgint"] = merged["cod_rgint"].astype(int)
    merged["ano"] = merged["ano"].astype(int)

    # Aggregate to (region, year, crop)
    agg = (
        merged.groupby(["cod_rgint", "nome_rgint", "ano", "cultura"], as_index=False)["area_ha"]
        .sum()
    )

    return agg.sort_values(["cod_rgint", "ano", "cultura"]).reset_index(drop=True)


@st.cache_data(show_spinner="Agregando PAM por estado…")
def load_pam_national() -> pd.DataFrame:
    """
    Aggregate PAM data to UF (state) level.

    Output columns:
        uf (str), ano (int), cultura (str), area_ha (float)
    """
    pam_region = load_pam_by_region()

    # Derive UF from cod_rgint first 2 digits
    pam_region = pam_region.copy()
    pam_region["uf_code"] = (pam_region["cod_rgint"] // 100).astype(int)
    pam_region["uf"] = pam_region["uf_code"].map(UF_DICT).fillna("??")

    agg = (
        pam_region.groupby(["uf", "ano", "cultura"], as_index=False)["area_ha"]
        .sum()
    )
    return agg.sort_values(["uf", "ano", "cultura"]).reset_index(drop=True)


@st.cache_data(show_spinner="Construindo série nacional…")
def load_national_series() -> pd.DataFrame:
    """
    Aggregate transitions to national level by (ano_fim, transicao).

    Output columns:
        ano_fim (int), transicao (str), transition_group (str), area_km2 (float)
    """
    df = load_transitions()
    agg = (
        df.groupby(["ano_fim", "transicao", "transition_group"], as_index=False)["area_km2"]
        .sum()
    )
    return agg.sort_values(["ano_fim", "transicao"]).reset_index(drop=True)


@st.cache_data(show_spinner="Agregando por estado…")
def load_uf_series() -> pd.DataFrame:
    """
    Aggregate transitions to (uf, ano_fim, transicao) level.
    """
    df = load_transitions()
    agg = (
        df.groupby(["uf", "ano_fim", "transicao", "transition_group"], as_index=False)["area_km2"]
        .sum()
    )
    return agg.sort_values(["uf", "ano_fim", "transicao"]).reset_index(drop=True)


def apply_filters(
    df_mb: pd.DataFrame,
    df_pam: pd.DataFrame,
    *,
    ufs: list[str] | None = None,
    transitions: list[str] | None = None,
    year_range: tuple[int, int] = (2008, 2024),
    crops: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply sidebar filters to both DataFrames and return filtered copies.
    """
    mb = df_mb.copy()
    pam = df_pam.copy()

    # Year filter (MapBiomas uses ano_fim as the "year" to align with PAM)
    mb = mb[(mb["ano_fim"] >= year_range[0]) & (mb["ano_fim"] <= year_range[1])]
    pam = pam[(pam["ano"] >= year_range[0]) & (pam["ano"] <= year_range[1])]

    if ufs:
        mb = mb[mb["uf"].isin(ufs)]
        uf_codes_sel = {code for code, name in UF_DICT.items() if name in ufs}
        pam_uf_codes = (pam["cod_rgint"] // 100).astype(int)
        pam = pam[pam_uf_codes.isin(uf_codes_sel)]

    if transitions:
        mb = mb[mb["transicao"].isin(transitions)]

    if crops:
        pam = pam[pam["cultura"].isin(crops)]

    return mb, pam
