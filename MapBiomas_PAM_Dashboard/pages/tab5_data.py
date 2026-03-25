"""
Tab 5 — Data Table & Export

Filtered data table with download button and summary statistics.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from utils.constants import CROP_LABELS, TRANSITION_LABELS


def render(df_mb: pd.DataFrame, df_pam: pd.DataFrame) -> None:
    st.header("Tabela de Dados e Exportação")

    dataset = st.radio(
        "Selecione o conjunto de dados",
        ["MapBiomas — Transições", "PAM — Produção Agrícola"],
        horizontal=True,
        key="tab5_dataset",
    )

    if dataset == "MapBiomas — Transições":
        _render_mb(df_mb)
    else:
        _render_pam(df_pam)


def _render_mb(df: pd.DataFrame) -> None:
    st.subheader("MapBiomas — Transições de Uso do Solo")

    col1, col2 = st.columns(2)
    with col1:
        all_ufs = sorted(df["uf"].unique())
        sel_ufs = st.multiselect("Estado (UF)", all_ufs, key="t5_mb_ufs")
    with col2:
        all_trans = sorted(df["transicao"].unique())
        sel_trans = st.multiselect(
            "Transição",
            all_trans,
            format_func=lambda t: TRANSITION_LABELS.get(t, t),
            key="t5_mb_trans",
        )

    filtered = df.copy()
    if sel_ufs:
        filtered = filtered[filtered["uf"].isin(sel_ufs)]
    if sel_trans:
        filtered = filtered[filtered["transicao"].isin(sel_trans)]

    display_cols = [
        "zona_id", "zona_nome", "uf", "ano_inicio", "ano_fim",
        "par_anos", "transicao", "transition_group", "n_pixels", "area_km2",
    ]
    display = filtered[display_cols].copy()
    display["area_km2"] = display["area_km2"].round(4)

    st.caption(f"{len(display):,} linhas | {display['area_km2'].sum():,.1f} km² total")
    st.dataframe(display, width="stretch", hide_index=True, height=400)

    _summary_stats(display, "area_km2", "Área (km²)")
    _download_button(display, "transicoes_filtrado.csv")


def _render_pam(df: pd.DataFrame) -> None:
    st.subheader("PAM — Área Colhida por Região Intermediária")

    col1, col2, col3 = st.columns(3)
    with col1:
        all_crops = sorted(df["cultura"].unique())
        sel_crops = st.multiselect(
            "Cultura",
            all_crops,
            format_func=lambda c: CROP_LABELS.get(c, c),
            key="t5_pam_crops",
        )
    with col2:
        all_regions = sorted(df["nome_rgint"].unique())
        sel_regions = st.multiselect("Região", all_regions, key="t5_pam_regions")
    with col3:
        year_min = int(df["ano"].min())
        year_max = int(df["ano"].max())
        sel_years = st.slider(
            "Intervalo de Anos",
            year_min, year_max,
            (year_min, year_max),
            key="t5_pam_years",
        )

    filtered = df.copy()
    if sel_crops:
        filtered = filtered[filtered["cultura"].isin(sel_crops)]
    if sel_regions:
        filtered = filtered[filtered["nome_rgint"].isin(sel_regions)]
    filtered = filtered[(filtered["ano"] >= sel_years[0]) & (filtered["ano"] <= sel_years[1])]

    display = filtered.copy()
    display["area_ha"] = display["area_ha"].round(0)
    display["cultura_label"] = display["cultura"].map(CROP_LABELS).fillna(display["cultura"])

    cols = ["cod_rgint", "nome_rgint", "ano", "cultura_label", "area_ha"]
    display = display[cols].rename(columns={"cultura_label": "cultura"})

    st.caption(f"{len(display):,} linhas | {display['area_ha'].sum():,.0f} ha total")
    st.dataframe(display, width="stretch", hide_index=True, height=400)

    _summary_stats(display, "area_ha", "Área Colhida (ha)")
    _download_button(display, "pam_filtrado.csv")


def _summary_stats(df: pd.DataFrame, col: str, label: str) -> None:
    if col not in df.columns or df.empty:
        return
    with st.expander("Estatísticas Descritivas"):
        stats = df[col].describe().rename({
            "count": "contagem", "mean": "média", "std": "desvio padrão",
            "min": "mínimo", "25%": "quartil 25%", "50%": "mediana",
            "75%": "quartil 75%", "max": "máximo",
        })
        st.dataframe(stats.to_frame(label), width="content")


def _download_button(df: pd.DataFrame, filename: str) -> None:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        label=f"⬇ Baixar CSV ({filename})",
        data=buf.getvalue().encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=f"dl_{filename}",
    )
