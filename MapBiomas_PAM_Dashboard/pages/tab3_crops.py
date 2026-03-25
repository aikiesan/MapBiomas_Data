"""
Tab 3 — Crop Comparison: Soy × Corn × Sugarcane

Per-crop PAM area by state, correlation scatter, and indirect
deforestation index.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.charts import (
    fig_crop_by_uf,
    fig_indirect_deforestation_index,
    fig_scatter_correlation,
)
from utils.constants import CROP_LABELS


def render(df_mb: pd.DataFrame, df_pam: pd.DataFrame) -> None:
    st.header("Comparativo de Culturas: Soja × Milho × Cana")

    # ── Crop trend by UF ──────────────────────────────────────────────────────
    st.subheader("Área Colhida por Estado (Top 10) — PAM")
    available_crops = [c for c in ["soja", "milho", "cana"] if c in df_pam["cultura"].values]

    if not available_crops:
        st.warning("Sem dados de culturas no filtro atual.")
        return

    crop_tabs = st.tabs([CROP_LABELS.get(c, c) for c in available_crops])
    for tab, crop in zip(crop_tabs, available_crops):
        with tab:
            sub = df_pam[df_pam["cultura"] == crop]
            if sub.empty:
                st.info(f"Sem dados para {CROP_LABELS.get(crop, crop)} no período selecionado.")
            else:
                st.plotly_chart(
                    fig_crop_by_uf(df_pam, crop),
                    width="stretch",
                )

    st.divider()

    # ── Correlation scatter ────────────────────────────────────────────────────
    st.subheader("Correlação: Desflorestamento (Floresta→Pastagem) × Área Soja (PAM)")
    st.caption(
        "Cada ponto representa uma região intermediária × ano. "
        "Uma correlação positiva indica que o desmatamento e a expansão da soja "
        "ocorrem simultaneamente nas mesmas regiões."
    )
    st.plotly_chart(
        fig_scatter_correlation(df_mb, df_pam),
        width="stretch",
    )

    st.divider()

    # ── Indirect deforestation index ─────────────────────────────────────────
    st.subheader("Índice de Desflorestamento Indireto (Top 30 Regiões)")
    st.caption(
        "Razão entre a área de Pastagem→Soja e Floresta→Pastagem. "
        "Valores altos indicam regiões onde a soja ocupa pastagens, "
        "deslocando a pecuária para novas fronteiras."
    )
    st.plotly_chart(
        fig_indirect_deforestation_index(df_mb),
        width="stretch",
    )
