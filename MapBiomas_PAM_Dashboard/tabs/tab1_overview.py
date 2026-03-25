"""
Tab 1 — National Overview

KPI cards + dual-axis trend line + stacked bar by UF.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.charts import (
    compute_kpis,
    fig_national_trend,
    fig_stacked_bar_uf,
)
from utils.constants import TRANSITION_GROUPS, TRANSITION_LABELS


def render(df_mb: pd.DataFrame, df_pam: pd.DataFrame) -> None:
    st.header("Visão Nacional: Transições de Uso do Solo × PAM")

    # ── KPI row ──────────────────────────────────────────────────────────────
    kpis = compute_kpis(df_mb, df_pam)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric(
            "Desflorestamento Total",
            f"{kpis['total_deforestation_km2']:,.0f} km²",
            help="Soma de floresta→pastagem, floresta→soja, savana→pastagem, savana→soja",
        )
    with c2:
        st.metric("Ano Pico", str(kpis["peak_year"] or "N/A"))
    with c3:
        st.metric("Região Mais Afetada", kpis["top_region"])
    with c4:
        st.metric("Estado Mais Afetado", kpis["top_uf"])
    with c5:
        soy_m = kpis["total_soy_ha"] / 1_000_000
        st.metric(
            "Total Soja PAM",
            f"{soy_m:,.1f} M ha",
            help="Soma acumulada de área colhida (PAM) para soja",
        )

    st.divider()

    # ── Trend selection ───────────────────────────────────────────────────────
    all_transitions = sorted(df_mb["transicao"].unique())
    default_trends = [
        t for t in ["floresta_para_pastagem", "savana_para_pastagem", "pastagem_para_soja"]
        if t in all_transitions
    ]
    selected_trends = st.multiselect(
        "Transições no gráfico de tendência",
        options=all_transitions,
        default=default_trends,
        format_func=lambda t: TRANSITION_LABELS.get(t, t),
        key="tab1_trends",
    )

    if not selected_trends:
        st.info("Selecione pelo menos uma transição para exibir o gráfico.")
        return

    st.plotly_chart(
        fig_national_trend(df_mb, df_pam, transitions=selected_trends),
        width="stretch",
    )

    st.divider()

    # ── Stacked bar by UF ────────────────────────────────────────────────────
    st.subheader("Área Acumulada por Estado (UF)")
    st.plotly_chart(fig_stacked_bar_uf(df_mb), width="stretch")
