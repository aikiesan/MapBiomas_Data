"""
Tab 6 — Mapas Espaciais
Spatial evolution of soy expansion in Brazil 2008–2024.

Sub-tabs:
  A. Regiões Intermediárias — MapBiomas transition choropleths (animated by year)
  B. Municípios — PAM soy/crop planted area by municipality
  C. Biomas — Transition flows over time (stacked area + Sankey + biome map)
  D. Cobertura — Forest / Pasture / Soy land coverage by municipality
"""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.constants import (
    TRANSITION_GROUPS,
    TRANSITION_LABELS,
    CROP_LABELS,
    GROUP_COLORS,
    TRANSITION_COLORS,
)
from utils.geo_data import (
    load_biome_transitions,
    load_biomes_geo,
    load_coverage_municipios,
    load_municipios_geo,
    load_pam_municipios,
    load_rgint_geo,
    COVERAGE_DISPLAY,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MAP_STYLE = "carto-positron"
_BRAZIL_LAT = -14.2
_BRAZIL_LON = -51.9
_BRAZIL_ZOOM = 3.5

_GROUP_LABELS: dict[str, str] = {
    "deforestation": "Desmatamento (Floresta)",
    "cerrado": "Conversão Cerrado/Savana",
    "soy_expansion": "Expansão Soja (Pastagem → Soja)",
    "recovery": "Recuperação",
    "stable": "Classes Estáveis",
}

_BIOME_COLORS: dict[str, str] = {
    "Amazônia": "#1a7c3e",
    "Cerrado": "#c8a227",
    "Caatinga": "#c97d3a",
    "Mata Atlântica": "#2e7d32",
    "Pampa": "#7cb342",
    "Pantanal": "#0288d1",
}

_TRANSITION_READABLE: dict[str, str] = {
    "floresta_para_pastagem": "Floresta → Pastagem",
    "floresta_para_soja": "Floresta → Soja",
    "floresta_para_outras_temp": "Floresta → Outras Temp.",
    "floresta_para_cana": "Floresta → Cana",
    "floresta_para_veg_sec": "Floresta → Veg. Sec.",
    "savana_para_pastagem": "Savana → Pastagem",
    "savana_para_soja": "Savana → Soja",
    "savana_para_outras_temp": "Savana → Outras Temp.",
    "pastagem_para_soja": "Pastagem → Soja",
    "pastagem_para_outras_temp": "Pastagem → Outras Temp.",
    "pastagem_para_cana": "Pastagem → Cana",
    "pastagem_para_veg_sec": "Pastagem → Veg. Sec.",
    "soja_para_veg_sec": "Soja → Veg. Sec.",
    "floresta_estavel": "Floresta Estável",
    "pastagem_estavel": "Pastagem Estável",
    "soja_estavel": "Soja Estável",
    "savana_estavel": "Savana Estável",
}

# Sankey node definitions for biome flow
_SANKEY_NODES = ["Floresta", "Savana", "Pastagem", "Soja", "Outras Temp.", "Veg. Sec."]
_SANKEY_NODE_IDX: dict[str, int] = {n: i for i, n in enumerate(_SANKEY_NODES)}
_SANKEY_COLORS = ["#1a7c3e", "#c8a227", "#a5682a", "#ffd700", "#9e9e9e", "#66bb6a"]

_SANKEY_TRANSITION_MAP: dict[str, tuple[str, str]] = {
    "floresta_para_pastagem": ("Floresta", "Pastagem"),
    "floresta_para_soja": ("Floresta", "Soja"),
    "floresta_para_outras_temp": ("Floresta", "Outras Temp."),
    "floresta_para_cana": ("Floresta", "Outras Temp."),
    "floresta_para_veg_sec": ("Floresta", "Veg. Sec."),
    "savana_para_pastagem": ("Savana", "Pastagem"),
    "savana_para_soja": ("Savana", "Soja"),
    "savana_para_outras_temp": ("Savana", "Outras Temp."),
    "pastagem_para_soja": ("Pastagem", "Soja"),
    "pastagem_para_outras_temp": ("Pastagem", "Outras Temp."),
    "pastagem_para_cana": ("Pastagem", "Outras Temp."),
    "pastagem_para_veg_sec": ("Pastagem", "Veg. Sec."),
    "soja_para_veg_sec": ("Soja", "Veg. Sec."),
}


# ---------------------------------------------------------------------------
# Sub-tab A — Intermediate Regions Choropleth
# ---------------------------------------------------------------------------

def _render_subtab_rgint(df_mb: pd.DataFrame) -> None:
    st.subheader("Expansão por Região Geográfica Intermediária")
    st.caption(
        "Área total (km²) das transições MapBiomas por Região Intermediária. "
        "Use o controle de animação para visualizar a evolução ano a ano."
    )

    geojson_str, meta_df = load_rgint_geo()
    geojson = json.loads(geojson_str)

    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    with col_ctrl1:
        group_options = [g for g in TRANSITION_GROUPS if g != "stable"]
        selected_group = st.selectbox(
            "Grupo de Transição",
            options=group_options,
            format_func=lambda g: _GROUP_LABELS.get(g, g),
            key="map_rgint_group",
        )
    with col_ctrl2:
        available_transitions = TRANSITION_GROUPS[selected_group]
        readable_opts = {t: _TRANSITION_READABLE.get(t, t) for t in available_transitions}
        selected_transitions = st.multiselect(
            "Transições",
            options=available_transitions,
            default=available_transitions,
            format_func=lambda t: readable_opts.get(t, t),
            key="map_rgint_transitions",
        )

    if not selected_transitions:
        st.warning("Selecione ao menos uma transição.")
        return

    # Aggregate: zona_id × ano_fim × transition → area_km2
    filtered = df_mb[df_mb["transicao"].isin(selected_transitions)].copy()
    agg = (
        filtered.groupby(["zona_id", "zona_nome", "ano_fim"], as_index=False)["area_km2"].sum()
    )
    agg["ano_fim_str"] = agg["ano_fim"].astype(str)

    # Ensure all region × year combinations exist (fill 0 for regions with no data)
    all_years = sorted(agg["ano_fim"].unique())
    all_zones = meta_df[["zona_id", "nome_rgint"]].copy()
    full_idx = pd.MultiIndex.from_product(
        [all_zones["zona_id"], all_years], names=["zona_id", "ano_fim"]
    )
    full_df = pd.DataFrame(index=full_idx).reset_index()
    full_df = full_df.merge(all_zones, on="zona_id", how="left")
    full_df = full_df.merge(
        agg[["zona_id", "ano_fim", "area_km2"]],
        on=["zona_id", "ano_fim"],
        how="left",
    )
    full_df["area_km2"] = full_df["area_km2"].fillna(0.0)
    full_df["ano_fim_str"] = full_df["ano_fim"].astype(str)

    color_label = "Área (km²)"
    fig = px.choropleth_map(
        full_df,
        geojson=geojson,
        locations="zona_id",
        featureidkey="properties.zona_id",
        color="area_km2",
        color_continuous_scale="YlOrRd",
        animation_frame="ano_fim_str",
        map_style=_MAP_STYLE,
        zoom=_BRAZIL_ZOOM,
        center={"lat": _BRAZIL_LAT, "lon": _BRAZIL_LON},
        opacity=0.75,
        hover_name="nome_rgint",
        hover_data={"area_km2": ":.1f", "zona_id": False, "ano_fim_str": False},
        labels={"area_km2": color_label},
        title=f"{_GROUP_LABELS[selected_group]} — evolução 2009–2024",
    )
    fig.update_layout(
        height=600,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title=color_label),
    )
    st.plotly_chart(fig, width="stretch")

    # Top-10 regions table for the last year
    last_year = full_df["ano_fim"].max()
    top10 = (
        full_df[full_df["ano_fim"] == last_year]
        .nlargest(10, "area_km2")[["nome_rgint", "area_km2"]]
        .rename(columns={"nome_rgint": "Região", "area_km2": "Área km² (último ano)"})
        .reset_index(drop=True)
    )
    with st.expander(f"Top 10 Regiões — {last_year}"):
        st.dataframe(top10, width="stretch")


# ---------------------------------------------------------------------------
# Sub-tab B — Municipalities: PAM Crop Area
# ---------------------------------------------------------------------------

def _render_subtab_pam_muni() -> None:
    st.subheader("Área Plantada por Município (PAM/IBGE)")
    st.caption(
        "Área plantada (ha) por cultura conforme Pesquisa Agrícola Municipal (IBGE PAM 5457). "
        "Dados disponíveis a cada 3 anos nos CSVs municipais."
    )

    pam = load_pam_municipios()
    geojson_str, meta_df = load_municipios_geo()
    geojson = json.loads(geojson_str)

    col1, col2, col3 = st.columns(3)
    with col1:
        crop_opts = sorted(pam["cultura"].unique())
        selected_crop = st.selectbox(
            "Cultura",
            options=crop_opts,
            format_func=lambda c: CROP_LABELS.get(c, c),
            key="map_muni_crop",
        )
    with col2:
        available_years = sorted(pam["ano"].unique())
        selected_year = st.selectbox(
            "Ano",
            options=available_years,
            index=len(available_years) - 1,
            key="map_muni_year",
        )
    with col3:
        uf_opts = ["Todos"] + sorted(meta_df["sigla_uf"].unique())
        selected_uf = st.selectbox("Estado (UF)", options=uf_opts, key="map_muni_uf")

    filtered_pam = pam[(pam["cultura"] == selected_crop) & (pam["ano"] == selected_year)].copy()

    # Merge with municipality metadata to get display name
    filtered_pam = filtered_pam.merge(
        meta_df[["cd_geocodigo", "nm_mun", "sigla_uf"]],
        on="cd_geocodigo",
        how="left",
    )

    if selected_uf != "Todos":
        filtered_pam = filtered_pam[filtered_pam["sigla_uf"] == selected_uf]

    if filtered_pam.empty or filtered_pam["area_ha"].sum() == 0:
        st.info("Nenhum dado disponível para a seleção. Ajuste cultura, ano ou UF.")
        return

    # For whole-Brazil view use simplified geojson; for single UF keep full detail
    color_max = filtered_pam["area_ha"].quantile(0.98)

    fig = px.choropleth_map(
        filtered_pam,
        geojson=geojson,
        locations="cd_geocodigo",
        featureidkey="properties.cd_geocodigo",
        color="area_ha",
        color_continuous_scale="YlGn",
        range_color=(0, max(color_max, 1)),
        map_style=_MAP_STYLE,
        zoom=_BRAZIL_ZOOM if selected_uf == "Todos" else 5.5,
        center={"lat": _BRAZIL_LAT, "lon": _BRAZIL_LON},
        opacity=0.75,
        hover_name="nm_mun",
        hover_data={"area_ha": ":,.0f", "cd_geocodigo": False, "sigla_uf": True},
        labels={"area_ha": "Área (ha)", "sigla_uf": "UF"},
        title=f"{CROP_LABELS.get(selected_crop, selected_crop)} — Área Plantada {selected_year} (ha)",
    )
    fig.update_layout(
        height=600,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Área (ha)"),
    )
    st.plotly_chart(fig, width="stretch")

    # Bar chart: top 15 municipalities
    top15 = (
        filtered_pam.nlargest(15, "area_ha")[["nm_mun", "sigla_uf", "area_ha"]]
        .reset_index(drop=True)
    )
    top15["label"] = top15["nm_mun"] + " (" + top15["sigla_uf"] + ")"
    fig_bar = px.bar(
        top15,
        x="area_ha",
        y="label",
        orientation="h",
        title=f"Top 15 Municípios — {CROP_LABELS.get(selected_crop, selected_crop)} {selected_year}",
        labels={"area_ha": "Área (ha)", "label": "Município"},
        color="area_ha",
        color_continuous_scale="YlGn",
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    st.plotly_chart(fig_bar, width="stretch")


# ---------------------------------------------------------------------------
# Sub-tab C — Biome Transitions
# ---------------------------------------------------------------------------

def _render_subtab_biomes() -> None:
    st.subheader("Transições por Bioma (2008–2024)")
    st.caption(
        "Fluxo de conversão de cobertura vegetal por bioma. "
        "Fontes: MapBiomas Coleção 10 — transições bianuais."
    )

    biome_trans = load_biome_transitions()
    geojson_str, biome_meta = load_biomes_geo()
    geojson = json.loads(geojson_str)

    all_biomes = sorted(biome_trans["bioma"].unique())
    col1, col2 = st.columns(2)
    with col1:
        selected_biomes = st.multiselect(
            "Biomas",
            options=all_biomes,
            default=all_biomes[:3],
            key="map_biome_biomes",
        )
    with col2:
        transition_opts = [t for t in biome_trans["transicao"].unique() if t in _TRANSITION_READABLE]
        default_trans = [
            t for t in ["floresta_para_pastagem", "floresta_para_soja", "savana_para_soja",
                         "pastagem_para_soja", "savana_para_pastagem"]
            if t in transition_opts
        ]
        selected_trans = st.multiselect(
            "Transições",
            options=transition_opts,
            default=default_trans,
            format_func=lambda t: _TRANSITION_READABLE.get(t, t),
            key="map_biome_trans",
        )

    if not selected_biomes or not selected_trans:
        st.warning("Selecione ao menos um bioma e uma transição.")
        return

    filtered = biome_trans[
        biome_trans["bioma"].isin(selected_biomes) & biome_trans["transicao"].isin(selected_trans)
    ].copy()

    # --- Stacked area chart: total area per year-pair per transition --------
    area_by_trans = (
        filtered.groupby(["ano_destino", "transicao"], as_index=False)["area_km2"].sum()
    )
    area_by_trans["transicao_label"] = area_by_trans["transicao"].map(
        lambda t: _TRANSITION_READABLE.get(t, t)
    )

    color_map = {_TRANSITION_READABLE.get(t, t): TRANSITION_COLORS.get(t, "#888") for t in selected_trans}

    fig_area = px.area(
        area_by_trans,
        x="ano_destino",
        y="area_km2",
        color="transicao_label",
        color_discrete_map=color_map,
        title="Área de Conversão por Tipo de Transição (todos os biomas selecionados)",
        labels={"ano_destino": "Ano", "area_km2": "Área (km²)", "transicao_label": "Transição"},
    )
    fig_area.update_layout(height=380, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_area, width="stretch")

    # --- Stacked area per biome for a single transition ---------------------
    st.markdown("---")
    st.markdown("#### Evolução por Bioma")
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        pivot_trans = st.selectbox(
            "Transição para detalhar por bioma",
            options=selected_trans,
            format_func=lambda t: _TRANSITION_READABLE.get(t, t),
            key="biome_pivot_trans",
        )

    by_biome = (
        filtered[filtered["transicao"] == pivot_trans]
        .groupby(["ano_destino", "bioma"], as_index=False)["area_km2"].sum()
    )
    biome_color_map = {b: _BIOME_COLORS.get(b, "#888") for b in selected_biomes}
    fig_biome = px.area(
        by_biome,
        x="ano_destino",
        y="area_km2",
        color="bioma",
        color_discrete_map=biome_color_map,
        title=f"{_TRANSITION_READABLE.get(pivot_trans, pivot_trans)} — por Bioma",
        labels={"ano_destino": "Ano", "area_km2": "Área (km²)", "bioma": "Bioma"},
    )
    fig_biome.update_layout(height=360, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_biome, width="stretch")

    # --- Sankey diagram (cumulative 2008–2024) -------------------------------
    st.markdown("---")
    st.markdown("#### Fluxo Cumulativo 2008–2024 (Sankey)")

    cum = (
        filtered.groupby("transicao", as_index=False)["area_km2"].sum()
    )
    cum = cum[cum["transicao"].isin(_SANKEY_TRANSITION_MAP)]

    if not cum.empty:
        sources, targets, values, link_labels = [], [], [], []
        for _, row in cum.iterrows():
            src_name, tgt_name = _SANKEY_TRANSITION_MAP.get(row["transicao"], (None, None))
            if src_name is None or tgt_name is None or row["area_km2"] <= 0:
                continue
            sources.append(_SANKEY_NODE_IDX[src_name])
            targets.append(_SANKEY_NODE_IDX[tgt_name])
            values.append(row["area_km2"])
            link_labels.append(f"{_TRANSITION_READABLE.get(row['transicao'], row['transicao'])}: {row['area_km2']:,.0f} km²")

        if sources:
            fig_sankey = go.Figure(go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=_SANKEY_NODES,
                    color=_SANKEY_COLORS,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    label=link_labels,
                    color="rgba(180,180,180,0.4)",
                ),
            ))
            biome_str = ", ".join(selected_biomes)
            fig_sankey.update_layout(
                title_text=f"Fluxo Cumulativo de Conversão — {biome_str}",
                height=450,
                font_size=13,
            )
            st.plotly_chart(fig_sankey, width="stretch")

    # --- Biome map: cumulative conversion intensity -------------------------
    st.markdown("---")
    st.markdown("#### Mapa de Intensidade de Conversão por Bioma")

    biome_intensity = (
        filtered.groupby(["CD_Bioma", "bioma"], as_index=False)["area_km2"].sum()
    )
    fig_map = px.choropleth_map(
        biome_intensity,
        geojson=geojson,
        locations="CD_Bioma",
        featureidkey="properties.CD_Bioma",
        color="area_km2",
        color_continuous_scale="OrRd",
        map_style=_MAP_STYLE,
        zoom=_BRAZIL_ZOOM,
        center={"lat": _BRAZIL_LAT, "lon": _BRAZIL_LON},
        opacity=0.7,
        hover_name="bioma",
        hover_data={"area_km2": ":,.0f", "CD_Bioma": False},
        labels={"area_km2": "Área Total (km²)"},
        title="Conversão Acumulada 2008–2024 por Bioma",
    )
    fig_map.update_layout(height=500, margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig_map, width="stretch")


# ---------------------------------------------------------------------------
# Sub-tab D — Forest/Pasture/Soy Coverage by Municipality
# ---------------------------------------------------------------------------

def _render_subtab_coverage() -> None:
    st.subheader("Cobertura e Uso do Solo por Município (MapBiomas Col. 10)")
    st.caption(
        "Área (ha) por classe de uso do solo, por município, a partir do MapBiomas Coleção 10. "
        "Série histórica 1985–2024."
    )

    cov = load_coverage_municipios()
    geojson_str, muni_meta = load_municipios_geo()
    geojson = json.loads(geojson_str)

    col1, col2, col3 = st.columns(3)
    with col1:
        class_opts = [k for k in COVERAGE_DISPLAY if k in cov["class_key"].unique()]
        selected_class = st.selectbox(
            "Classe de Cobertura",
            options=class_opts,
            format_func=lambda k: COVERAGE_DISPLAY.get(k, k),
            key="map_cov_class",
        )
    with col2:
        year_opts = sorted(cov["ano"].unique())
        selected_year = st.select_slider(
            "Ano",
            options=year_opts,
            value=year_opts[-1],
            key="map_cov_year",
        )
    with col3:
        uf_opts = ["Todos"] + sorted(muni_meta["sigla_uf"].unique())
        selected_uf = st.selectbox("Estado (UF)", options=uf_opts, key="map_cov_uf")

    filtered = cov[
        (cov["class_key"] == selected_class) & (cov["ano"] == selected_year)
    ].copy()

    # Join with municipality metadata for cd_geocodigo
    # MB col10 uses municipality name + state — join on both
    muni_meta_lower = muni_meta.copy()
    muni_meta_lower["nm_mun_upper"] = muni_meta_lower["nm_mun"].str.upper().str.strip()
    filtered["mun_upper"] = filtered["municipality"].str.upper().str.strip()

    filtered = filtered.merge(
        muni_meta_lower[["cd_geocodigo", "nm_mun", "nm_mun_upper", "sigla_uf"]],
        left_on=["mun_upper", "state_acronym"],
        right_on=["nm_mun_upper", "sigla_uf"],
        how="left",
    )

    if selected_uf != "Todos":
        filtered = filtered[filtered["sigla_uf"] == selected_uf]

    matched = filtered.dropna(subset=["cd_geocodigo"])

    if matched.empty or matched["area_ha"].sum() == 0:
        st.info(
            "Nenhum dado disponível para a combinação selecionada. "
            "Alguns municípios podem não ter correspondência exata de nome."
        )
        return

    color_max = matched["area_ha"].quantile(0.97)
    color_label = COVERAGE_DISPLAY.get(selected_class, selected_class)

    fig = px.choropleth_map(
        matched,
        geojson=geojson,
        locations="cd_geocodigo",
        featureidkey="properties.cd_geocodigo",
        color="area_ha",
        color_continuous_scale="Greens" if selected_class in ("floresta", "savana") else "YlOrBr",
        range_color=(0, max(color_max, 1)),
        map_style=_MAP_STYLE,
        zoom=_BRAZIL_ZOOM if selected_uf == "Todos" else 5.5,
        center={"lat": _BRAZIL_LAT, "lon": _BRAZIL_LON},
        opacity=0.75,
        hover_name="nm_mun",
        hover_data={"area_ha": ":,.0f", "cd_geocodigo": False, "sigla_uf": True},
        labels={"area_ha": "Área (ha)", "sigla_uf": "UF"},
        title=f"{color_label} — {selected_year} (ha)",
    )
    fig.update_layout(
        height=600,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Área (ha)"),
    )
    st.plotly_chart(fig, width="stretch")

    # --- Trend chart for top soy-expanding municipalities -------------------
    if selected_class == "soja":
        st.markdown("---")
        st.markdown("#### Crescimento de Soja: Top 10 Municípios")

        # Compute growth 2008 → selected_year
        base_year = 2008
        soy_recent = cov[
            (cov["class_key"] == "soja") & (cov["ano"].isin([base_year, selected_year]))
        ].copy()
        soy_recent["mun_upper"] = soy_recent["municipality"].str.upper().str.strip()
        soy_recent = soy_recent.merge(
            muni_meta_lower[["cd_geocodigo", "nm_mun", "nm_mun_upper", "sigla_uf"]],
            left_on=["mun_upper", "state_acronym"],
            right_on=["nm_mun_upper", "sigla_uf"],
            how="left",
        )
        soy_pivot = soy_recent.pivot_table(
            index=["cd_geocodigo", "nm_mun", "state_acronym"],
            columns="ano",
            values="area_ha",
            aggfunc="sum",
        ).reset_index()
        soy_pivot.columns.name = None

        if base_year in soy_pivot.columns and selected_year in soy_pivot.columns:
            soy_pivot["growth_ha"] = soy_pivot[selected_year] - soy_pivot[base_year]
            top10 = soy_pivot.nlargest(10, "growth_ha")
            top10_names = top10["nm_mun"].dropna().tolist()

            soy_trend = cov[
                (cov["class_key"] == "soja") &
                (cov["municipality"].isin(top10_names)) &
                (cov["ano"] >= base_year)
            ].copy()

            fig_trend = px.line(
                soy_trend,
                x="ano",
                y="area_ha",
                color="municipality",
                title=f"Evolução da Área de Soja — Top 10 Municípios (crescimento {base_year}→{selected_year})",
                labels={"ano": "Ano", "area_ha": "Área (ha)", "municipality": "Município"},
            )
            fig_trend.update_layout(height=380, legend=dict(orientation="h", y=-0.4))
            st.plotly_chart(fig_trend, width="stretch")

    # --- Stacked bar: evolution of selected class top 15 municipalities -----
    st.markdown("---")
    st.markdown(f"#### Top 15 Municípios — {COVERAGE_DISPLAY.get(selected_class, selected_class)} em {selected_year}")

    top15 = matched.nlargest(15, "area_ha")[["nm_mun", "sigla_uf", "area_ha"]].copy()
    top15["label"] = top15["nm_mun"] + " (" + top15["sigla_uf"] + ")"
    fig_bar = px.bar(
        top15.reset_index(drop=True),
        x="area_ha",
        y="label",
        orientation="h",
        color="area_ha",
        color_continuous_scale="YlGn",
        labels={"area_ha": "Área (ha)", "label": "Município"},
        title=f"Top 15 — {COVERAGE_DISPLAY.get(selected_class, selected_class)} {selected_year}",
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    st.plotly_chart(fig_bar, width="stretch")


# ---------------------------------------------------------------------------
# Main render entry point
# ---------------------------------------------------------------------------

def render(df_mb: pd.DataFrame, df_pam: pd.DataFrame) -> None:  # noqa: ARG001
    """Entry point called from app.py tab context."""

    st.markdown(
        "Visualização espacial da expansão da soja e conversão de cobertura nativa no Brasil. "
        "Selecione uma das abas abaixo para explorar diferentes dimensões geográficas."
    )

    sub_a, sub_b, sub_c, sub_d = st.tabs([
        "🗺 Regiões Intermediárias",
        "🏙 Municípios (PAM)",
        "🌿 Biomas",
        "🌱 Cobertura do Solo",
    ])

    with sub_a:
        _render_subtab_rgint(df_mb)

    with sub_b:
        _render_subtab_pam_muni()

    with sub_c:
        _render_subtab_biomes()

    with sub_d:
        _render_subtab_coverage()
