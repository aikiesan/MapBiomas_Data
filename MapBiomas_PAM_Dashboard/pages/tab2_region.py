"""
Tab 2 — Region Explorer

Dropdown to select an intermediate region; shows transition breakdown
and PAM production side-by-side, plus a dual time-series below.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.charts import (
    fig_region_pam,
    fig_region_transitions,
    fig_timeseries_pair,
)


def render(df_mb: pd.DataFrame, df_pam: pd.DataFrame) -> None:
    st.header("Explorador de Regiões Geográficas Intermediárias")

    # ── Region selector ──────────────────────────────────────────────────────
    regions_mb = sorted(df_mb["zona_nome"].unique())
    regions_pam = set(df_pam["nome_rgint"].unique())

    # Prefer regions present in both datasets
    regions_both = [r for r in regions_mb if r in regions_pam]
    region_options = regions_both if regions_both else regions_mb

    default_region = "Sinop" if "Sinop" in region_options else region_options[0]
    selected_region = st.selectbox(
        "Selecione a Região Intermediária",
        options=region_options,
        index=region_options.index(default_region),
        key="tab2_region",
    )

    # Look up cod_rgint for the selected region
    pam_sub = df_pam[df_pam["nome_rgint"] == selected_region]
    if pam_sub.empty:
        # Try to match via MapBiomas zona_id
        mb_sub = df_mb[df_mb["zona_nome"] == selected_region]
        cod_rgint = int(mb_sub["zona_id"].iloc[0]) if not mb_sub.empty else None
    else:
        cod_rgint = int(pam_sub["cod_rgint"].iloc[0])

    # ── Side-by-side charts ───────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Transições MapBiomas")
        mb_region = df_mb[df_mb["zona_nome"] == selected_region]
        if mb_region.empty:
            st.warning("Sem dados de transição para esta região.")
        else:
            st.plotly_chart(
                fig_region_transitions(df_mb, selected_region),
                use_container_width=True,
            )
            # Summary table
            total = (
                mb_region.groupby("transicao")["area_km2"]
                .sum()
                .reset_index()
                .sort_values("area_km2", ascending=False)
            )
            total.columns = ["Transição", "Área Total (km²)"]
            total["Área Total (km²)"] = total["Área Total (km²)"].round(1)
            st.dataframe(total, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Produção Agrícola PAM")
        if cod_rgint is None or pam_sub.empty:
            st.warning("Sem dados PAM para esta região.")
        else:
            st.plotly_chart(
                fig_region_pam(df_pam, cod_rgint),
                use_container_width=True,
            )

    # ── Dual time series ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Série Temporal: Pressão de Desflorestamento × Expansão Soja")
    if cod_rgint is not None:
        st.plotly_chart(
            fig_timeseries_pair(df_mb, df_pam, selected_region, cod_rgint),
            use_container_width=True,
        )
    else:
        st.info("Código de região PAM não encontrado para esta seleção.")
