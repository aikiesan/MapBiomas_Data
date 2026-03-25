"""
Geospatial data loaders for the MapBiomas × PAM dashboard.

All loaders use @st.cache_data so heavy file I/O and geometry processing
happen only once per Streamlit session.

Shapefile join keys:
  - RGINT:         gdf['rgint']    (int)  ↔  transitions CSV zona_id (int)
  - Municipalities: gdf['CD_MUN']  (str, 7-digit) ↔ PAM cd_geocodigo (str)
  - Biomes:        gdf['CD_Bioma'] (int)  ↔  biome transitions CD_Bioma (int)
"""

from __future__ import annotations

import json
import pathlib

import geopandas as gpd
import pandas as pd
import streamlit as st

from utils.load_data import _parse_pam_csv

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_SHP_ROOT = _REPO_ROOT / "data" / "shapefiles"
_DATA_ROOT = _REPO_ROOT / "data"

_RGINT_SHP = _SHP_ROOT / "RG2017_rgint" / "RG2017_rgint.shp"
_MUN_SHP = _SHP_ROOT / "BR_Municipios_2024" / "BR_Municipios_2024.shp"
_BIOME_SHP = _SHP_ROOT / "Biomas_250mil" / "lm_bioma_250.shp"

_PAM_DIR = _DATA_ROOT / "raw" / "pam" / "DADOS_PAM_POR_MUNICIPIO_5_CULTURAS"
_MB_COL10_CSV = _DATA_ROOT / "processed" / "MB_col10_municipios.csv"
_BIOME_TRANS_CSV = _DATA_ROOT / "processed" / "CSV" / "MB_transicoes_bioma_2008_2024.csv"

# Land-cover class mappings from MB_col10_municipios class_level_2
COVERAGE_CLASS_MAP: dict[str, str] = {
    "1.1. Forest Formation": "floresta",
    "1.2. Savanna Formation": "savana",
    "1.3. Mangrove": "manguezal",
    "1.4 Floodable Forest": "floresta_alagavel",
    "2.1. Wetland": "campo_alagado",
    "2.2. Grassland": "campo_nativo",
    "3.1. Pasture": "pastagem",
    "3.2. Sugar Cane": "cana",
    "3.3. Mosaic Agriculture and Pasture": "agric_mosaico",
    "3.4. Agriculture or Pasture": "agric_ou_past",
    "3.5. Other Annual and Perennial Crops": "outras_temp",
    "3.6. Coffee": "cafe",
    "3.7. Citrus": "citrus",
    "3.8. Other Perennial Crops": "outras_perenes",
    "3.9. Soybean": "soja",
    "3.10. Rice": "arroz",
    "4.1. Beach, Dune and Sand Spot": "praia_duna",
    "4.2. Urban Area": "area_urbana",
    "4.5. Other non Vegetated Areas": "outras_nao_veg",
    "5.1. River, Lake and Ocean": "agua",
    "5.2. Aquaculture": "aquicultura",
    "6. Not Observed": "nao_observado",
    "Farming/Agriculture": "agric_geral",
}

COVERAGE_DISPLAY: dict[str, str] = {
    "floresta": "Floresta Nativa",
    "savana": "Savana / Cerrado",
    "pastagem": "Pastagem",
    "soja": "Soja",
    "agric_mosaico": "Mosaico Agric./Past.",
    "outras_temp": "Outras Culturas Temp.",
    "cana": "Cana-de-açúcar",
    "area_urbana": "Área Urbana",
    "agua": "Água",
}


# ---------------------------------------------------------------------------
# Intermediate Regions
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando shapefile Regiões Intermediárias…")
def load_rgint_geo() -> tuple[str, pd.DataFrame]:
    """
    Returns (geojson_str, metadata_df).
    metadata_df columns: zona_id (int), nome_rgint (str), uf_code (int)
    GeoJSON featureidkey: 'properties.zona_id'
    """
    gdf = gpd.read_file(_RGINT_SHP)
    gdf = gdf.to_crs(epsg=4326)
    gdf = gdf.rename(columns={"rgint": "zona_id"})
    gdf["zona_id"] = gdf["zona_id"].astype(int)
    gdf["uf_code"] = (gdf["zona_id"] // 100).astype(int)

    geojson = json.loads(gdf[["zona_id", "nome_rgint", "geometry"]].to_json())

    meta = gdf[["zona_id", "nome_rgint", "uf_code"]].copy()
    return json.dumps(geojson), meta


# ---------------------------------------------------------------------------
# Municipalities
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando shapefile Municípios…")
def load_municipios_geo() -> tuple[str, pd.DataFrame]:
    """
    Returns (geojson_str, metadata_df).
    metadata_df columns: cd_geocodigo (str), nm_mun (str), cd_rgint (int), sigla_uf (str)
    GeoJSON featureidkey: 'properties.cd_geocodigo'
    Geometries are simplified to reduce payload size.

    Returns empty GeoJSON and empty DataFrame if the shapefile is not found.
    """
    if not _MUN_SHP.exists():
        empty_geojson = json.dumps({"type": "FeatureCollection", "features": []})
        empty_meta = pd.DataFrame(columns=["cd_geocodigo", "nm_mun", "cd_rgint", "sigla_uf"])
        return empty_geojson, empty_meta

    gdf = gpd.read_file(_MUN_SHP)
    gdf = gdf.to_crs(epsg=4326)

    # Normalise key to 7-digit string (CD_MUN in 2024 shapefile is 7-digit)
    gdf["cd_geocodigo"] = gdf["CD_MUN"].astype(str).str.zfill(7)
    gdf["cd_rgint"] = gdf["CD_RGINT"].astype(int)
    gdf["nm_mun"] = gdf["NM_MUN"]
    gdf["sigla_uf"] = gdf["SIGLA_UF"]

    # Simplify to reduce GeoJSON size (~5 570 polygons)
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.01, preserve_topology=True)

    geojson = json.loads(
        gdf[["cd_geocodigo", "nm_mun", "cd_rgint", "sigla_uf", "geometry"]].to_json()
    )
    meta = gdf[["cd_geocodigo", "nm_mun", "cd_rgint", "sigla_uf"]].copy()
    return json.dumps(geojson), meta


# ---------------------------------------------------------------------------
# Biomes
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando shapefile Biomas…")
def load_biomes_geo() -> tuple[str, pd.DataFrame]:
    """
    Returns (geojson_str, metadata_df).
    metadata_df columns: CD_Bioma (int), Bioma (str)
    GeoJSON featureidkey: 'properties.CD_Bioma'
    """
    gdf = gpd.read_file(_BIOME_SHP)
    gdf = gdf.to_crs(epsg=4326)
    gdf["CD_Bioma"] = gdf["CD_Bioma"].astype(int)

    geojson = json.loads(gdf[["CD_Bioma", "Bioma", "geometry"]].to_json())
    meta = gdf[["CD_Bioma", "Bioma"]].copy()
    return json.dumps(geojson), meta


# ---------------------------------------------------------------------------
# PAM by municipality (raw, no region aggregation)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando PAM por município…")
def load_pam_municipios() -> pd.DataFrame:
    """
    Parse all PAM CSVs and return long-format municipal data.

    Output columns:
        cd_geocodigo (str, 7-digit), municipio (str), ano (int),
        cultura (str), area_ha (float)
    """
    frames: list[pd.DataFrame] = []
    for csv_path in sorted(_PAM_DIR.glob("*.csv")):
        chunk = _parse_pam_csv(csv_path)
        frames.append(chunk)

    if not frames:
        return pd.DataFrame(
            columns=["cd_geocodigo", "municipio", "ano", "cultura", "area_ha"]
        )

    pam = pd.concat(frames, ignore_index=True)
    pam["cd_geocodigo"] = pam["cd_geocodigo"].str.strip().str.zfill(7)
    pam["ano"] = pam["ano"].astype(int)
    return pam.sort_values(["cd_geocodigo", "ano", "cultura"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Biome transitions (wide → long)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando transições por bioma…")
def load_biome_transitions() -> pd.DataFrame:
    """
    Load and melt the biome transitions CSV to long format.

    Output columns:
        CD_Bioma (int), bioma (str), ano_origem (int), ano_destino (int),
        transicao (str), area_km2 (float)
    """
    df = pd.read_csv(_BIOME_TRANS_CSV)
    df["CD_Bioma"] = df["CD_Bioma"].astype(int)
    df["ano_origem"] = df["ano_origem"].astype(int)
    df["ano_destino"] = df["ano_destino"].astype(int)

    transition_cols = [c for c in df.columns if c.endswith("_km2")]
    long = df.melt(
        id_vars=["CD_Bioma", "bioma", "ano_origem", "ano_destino"],
        value_vars=transition_cols,
        var_name="transicao_raw",
        value_name="area_km2",
    )
    long["transicao"] = long["transicao_raw"].str.replace("_km2", "", regex=False)
    long = long.drop(columns=["transicao_raw"])
    long["area_km2"] = pd.to_numeric(long["area_km2"], errors="coerce").fillna(0.0)
    return long.sort_values(["CD_Bioma", "ano_origem", "transicao"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Municipality land-cover from MB Collection 10
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Carregando cobertura MapBiomas por município…")
def load_coverage_municipios() -> pd.DataFrame:
    """
    Load MB_col10_municipios.csv and return long-format coverage data
    for a curated set of land-cover classes.

    Output columns:
        cd_geocodigo (str, 7-digit), municipio (str), biome (str),
        state (str), class_key (str), ano (int), area_ha (float)

    Only classes present in COVERAGE_CLASS_MAP are retained.
    Area is in ha (original values are in ha from MapBiomas).

    Returns empty DataFrame if the CSV is not found.
    """
    if not _MB_COL10_CSV.exists():
        return pd.DataFrame(
            columns=["biome", "state", "state_acronym", "municipality", "class_key", "ano", "area_ha"]
        )

    df = pd.read_csv(_MB_COL10_CSV, dtype=str)

    # Normalise municipality code — column is 'municipality' but we need the
    # IBGE code; MB col10 doesn't have a separate code column in standard exports.
    # Use 'municipality' name + state as display, join via NM_MUN in shapefile.
    # However if there's a numeric id column use it.
    year_cols = [c for c in df.columns if c.isdigit() and int(c) >= 1985]

    # Map class_level_2 to internal key
    df["class_key"] = df["class_level_2"].map(COVERAGE_CLASS_MAP)

    # Keep only mapped classes
    df = df[df["class_key"].notna()].copy()

    # Melt years
    id_cols = ["biome", "state", "state_acronym", "municipality", "class_key"]
    long = df[id_cols + year_cols].melt(
        id_vars=id_cols,
        value_vars=year_cols,
        var_name="ano",
        value_name="area_ha_raw",
    )
    long["ano"] = long["ano"].astype(int)
    long["area_ha"] = pd.to_numeric(long["area_ha_raw"], errors="coerce").fillna(0.0)
    long = long.drop(columns=["area_ha_raw"])

    return long.sort_values(["state_acronym", "municipality", "ano"]).reset_index(drop=True)
