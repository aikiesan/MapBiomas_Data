"""
Tab 4 — Heatmap Explorer

Year-pair × top-30 intermediate regions heatmap,
with transition and UF filters.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.charts import fig_heatmap
from utils.constants import TRANSITION_LABELS


def render(df_mb: pd.DataFrame) -> None:
    st.header("Heatmap: Intensidade por Região e Período")

    col_ctrl1, col_ctrl2 = st.columns([2, 1])

    with col_ctrl1:
        all_transitions = sorted(df_mb["transicao"].unique())
        selected_transition = st.selectbox(
            "Tipo de transição",
            options=all_transitions,
            index=all_transitions.index("floresta_para_pastagem")
            if "floresta_para_pastagem" in all_transitions
            else 0,
            format_func=lambda t: TRANSITION_LABELS.get(t, t),
            key="tab4_transition",
        )

    with col_ctrl2:
        all_ufs = sorted(df_mb["uf"].unique())
        selected_ufs = st.multiselect(
            "Filtrar por Estado (UF)",
            options=all_ufs,
            default=[],
            key="tab4_ufs",
            placeholder="Todos os estados",
        )

    top_n = st.slider(
        "Número de regiões exibidas",
        min_value=10,
        max_value=50,
        value=30,
        step=5,
        key="tab4_top_n",
    )

    ufs_filter = selected_ufs if selected_ufs else None

    fig = fig_heatmap(df_mb, transition=selected_transition, ufs=ufs_filter, top_n=top_n)
    st.plotly_chart(fig, use_container_width=True)

    # Quick stats below
    sub = df_mb[df_mb["transicao"] == selected_transition]
    if ufs_filter:
        sub = sub[sub["uf"].isin(ufs_filter)]

    if not sub.empty:
        peak = sub.groupby("par_anos")["area_km2"].sum().idxmax()
        total = sub["area_km2"].sum()
        top_region = sub.groupby("zona_nome")["area_km2"].sum().idxmax()

        c1, c2, c3 = st.columns(3)
        c1.metric("Par de Anos com Maior Área", peak)
        c2.metric("Área Total (filtro atual)", f"{total:,.0f} km²")
        c3.metric("Região Mais Afetada", top_region)
