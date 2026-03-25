"""
Plotly figure factory functions for the MapBiomas × PAM dashboard.

Every function accepts pre-filtered DataFrames and returns a go.Figure.
No Streamlit calls here — pure Plotly.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.constants import (
    CROP_LABELS,
    GROUP_COLORS,
    TRANSITION_COLORS,
    TRANSITION_LABELS,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    font_family="Inter, sans-serif",
    margin=dict(l=60, r=30, t=50, b=60),
    legend=dict(orientation="v", x=1.02, y=1),
)


def _apply_defaults(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(title_text=title, title_x=0.0, **_LAYOUT_DEFAULTS)
    return fig


def _transition_color(name: str) -> str:
    return TRANSITION_COLORS.get(name, "#888888")


# ---------------------------------------------------------------------------
# Tab 1 — National Overview
# ---------------------------------------------------------------------------

def fig_national_trend(
    df_mb: pd.DataFrame,
    df_pam: pd.DataFrame,
    transitions: list[str] | None = None,
) -> go.Figure:
    """
    Dual-axis line chart: selected deforestation transitions (km², left axis)
    vs PAM soy harvested area (ha, right axis).
    """
    if transitions is None:
        transitions = ["floresta_para_pastagem", "savana_para_pastagem", "pastagem_para_soja"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    mb_agg = (
        df_mb[df_mb["transicao"].isin(transitions)]
        .groupby(["ano_fim", "transicao"], as_index=False)["area_km2"]
        .sum()
    )
    for trans in transitions:
        sub = mb_agg[mb_agg["transicao"] == trans]
        label = TRANSITION_LABELS.get(trans, trans)
        fig.add_trace(
            go.Scatter(
                x=sub["ano_fim"],
                y=sub["area_km2"],
                name=label,
                mode="lines+markers",
                line=dict(color=_transition_color(trans), width=2),
            ),
            secondary_y=False,
        )

    # PAM soy national total
    soy = df_pam[df_pam["cultura"] == "soja"].groupby("ano", as_index=False)["area_ha"].sum()
    if not soy.empty:
        fig.add_trace(
            go.Scatter(
                x=soy["ano"],
                y=soy["area_ha"],
                name="PAM Soja (ha)",
                mode="lines+markers",
                line=dict(color="#2ca02c", width=2, dash="dot"),
            ),
            secondary_y=True,
        )

    fig.update_yaxes(title_text="Área (km²)", secondary_y=False)
    fig.update_yaxes(title_text="Área Colhida PAM (ha)", secondary_y=True)
    fig.update_xaxes(title_text="Ano")
    return _apply_defaults(fig, "Tendência Nacional: Transições × Produção Agrícola")


def fig_stacked_bar_uf(df_mb: pd.DataFrame) -> go.Figure:
    """
    Stacked horizontal bar: cumulative transition area by UF,
    coloured by transition group.
    """
    agg = (
        df_mb.groupby(["uf", "transition_group"], as_index=False)["area_km2"]
        .sum()
    )
    # Sort UFs by total area descending
    totals = agg.groupby("uf")["area_km2"].sum().sort_values(ascending=True)
    uf_order = totals.index.tolist()

    fig = go.Figure()
    for group, color in GROUP_COLORS.items():
        sub = agg[agg["transition_group"] == group]
        fig.add_trace(
            go.Bar(
                x=sub["area_km2"],
                y=sub["uf"],
                name=group.replace("_", " ").title(),
                orientation="h",
                marker_color=color,
            )
        )

    fig.update_layout(
        barmode="stack",
        yaxis=dict(categoryorder="array", categoryarray=uf_order),
        xaxis_title="Área (km²)",
        yaxis_title="Estado (UF)",
    )
    return _apply_defaults(fig, "Área Acumulada por Estado e Grupo de Transição")


# ---------------------------------------------------------------------------
# Tab 2 — Region Explorer
# ---------------------------------------------------------------------------

def fig_region_transitions(df_mb: pd.DataFrame, region: str) -> go.Figure:
    """
    Grouped bar chart of all transition types for the selected region,
    one bar per year.
    """
    sub = df_mb[df_mb["zona_nome"] == region]
    agg = sub.groupby(["ano_fim", "transicao"], as_index=False)["area_km2"].sum()

    fig = go.Figure()
    for trans in agg["transicao"].unique():
        t_sub = agg[agg["transicao"] == trans]
        fig.add_trace(
            go.Bar(
                x=t_sub["ano_fim"],
                y=t_sub["area_km2"],
                name=TRANSITION_LABELS.get(trans, trans),
                marker_color=_transition_color(trans),
            )
        )

    fig.update_layout(
        barmode="stack",
        xaxis_title="Ano",
        yaxis_title="Área (km²)",
    )
    return _apply_defaults(fig, f"Transições por Ano — {region}")


def fig_region_pam(df_pam: pd.DataFrame, cod_rgint: int) -> go.Figure:
    """
    Grouped bar of PAM area by crop and year for the selected region.
    """
    sub = df_pam[df_pam["cod_rgint"] == cod_rgint]
    agg = sub.groupby(["ano", "cultura"], as_index=False)["area_ha"].sum()

    crops = [c for c in ["soja", "milho", "cana", "algodao_herbaceo"] if c in agg["cultura"].values]
    crop_colors = {
        "soja": "#2ca02c",
        "milho": "#ffd700",
        "cana": "#ff7f0e",
        "algodao_herbaceo": "#1f77b4",
    }

    fig = go.Figure()
    for crop in crops:
        c_sub = agg[agg["cultura"] == crop]
        fig.add_trace(
            go.Bar(
                x=c_sub["ano"],
                y=c_sub["area_ha"],
                name=CROP_LABELS.get(crop, crop),
                marker_color=crop_colors.get(crop, "#888"),
            )
        )

    fig.update_layout(
        barmode="group",
        xaxis_title="Ano",
        yaxis_title="Área Colhida (ha)",
    )
    region_name = sub["nome_rgint"].iloc[0] if not sub.empty else str(cod_rgint)
    return _apply_defaults(fig, f"Produção Agrícola PAM — {region_name}")


def fig_timeseries_pair(
    df_mb: pd.DataFrame,
    df_pam: pd.DataFrame,
    region: str,
    cod_rgint: int,
) -> go.Figure:
    """
    Dual-axis time series: deforestation pressure (km²) vs soy PAM area (ha).
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    mb_sub = df_mb[
        (df_mb["zona_nome"] == region)
        & (df_mb["transition_group"].isin(["deforestation", "cerrado"]))
    ]
    mb_agg = mb_sub.groupby("ano_fim", as_index=False)["area_km2"].sum()

    fig.add_trace(
        go.Scatter(
            x=mb_agg["ano_fim"],
            y=mb_agg["area_km2"],
            name="Pressão Desflorestamento (km²)",
            mode="lines+markers",
            line=dict(color="#d62728", width=2),
        ),
        secondary_y=False,
    )

    pam_sub = df_pam[
        (df_pam["cod_rgint"] == cod_rgint) & (df_pam["cultura"] == "soja")
    ]
    pam_agg = pam_sub.groupby("ano", as_index=False)["area_ha"].sum()
    fig.add_trace(
        go.Scatter(
            x=pam_agg["ano"],
            y=pam_agg["area_ha"],
            name="Soja PAM (ha)",
            mode="lines+markers",
            line=dict(color="#2ca02c", width=2, dash="dot"),
        ),
        secondary_y=True,
    )

    fig.update_yaxes(title_text="Desflorestamento (km²)", secondary_y=False)
    fig.update_yaxes(title_text="Área Soja (ha)", secondary_y=True)
    fig.update_xaxes(title_text="Ano")
    return _apply_defaults(fig, f"Pressão × Expansão Soja — {region}")


# ---------------------------------------------------------------------------
# Tab 3 — Crop Comparison
# ---------------------------------------------------------------------------

def fig_crop_by_uf(df_pam: pd.DataFrame, crop: str) -> go.Figure:
    """
    Line chart of PAM harvested area trend per state for a given crop.
    Shows top-10 states by total area.
    """
    sub = df_pam[df_pam["cultura"] == crop].copy()
    sub["uf_code"] = (sub["cod_rgint"] // 100).astype(int)

    from utils.constants import UF_DICT
    sub["uf"] = sub["uf_code"].map(UF_DICT).fillna("??")

    agg = sub.groupby(["uf", "ano"], as_index=False)["area_ha"].sum()
    top_ufs = (
        agg.groupby("uf")["area_ha"].sum()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )
    agg = agg[agg["uf"].isin(top_ufs)]

    fig = px.line(
        agg,
        x="ano",
        y="area_ha",
        color="uf",
        markers=True,
        labels={"ano": "Ano", "area_ha": "Área Colhida (ha)", "uf": "Estado"},
        template="plotly_white",
    )
    crop_label = CROP_LABELS.get(crop, crop)
    return _apply_defaults(fig, f"Área Colhida {crop_label} por Estado (Top 10)")


def fig_scatter_correlation(
    df_mb: pd.DataFrame,
    df_pam: pd.DataFrame,
) -> go.Figure:
    """
    Scatter plot: floresta→pastagem deforestation area vs PAM soy area
    per region per year, coloured by UF.
    """
    mb_def = (
        df_mb[df_mb["transicao"] == "floresta_para_pastagem"]
        .groupby(["zona_id", "zona_nome", "ano_fim", "uf"], as_index=False)["area_km2"]
        .sum()
        .rename(columns={"area_km2": "desmat_km2", "ano_fim": "ano"})
    )

    pam_soy = (
        df_pam[df_pam["cultura"] == "soja"]
        .groupby(["cod_rgint", "nome_rgint", "ano"], as_index=False)["area_ha"]
        .sum()
        .rename(columns={"cod_rgint": "zona_id"})
    )

    merged = mb_def.merge(pam_soy, on=["zona_id", "ano"], how="inner")
    if merged.empty:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para correlação", showarrow=False)
        return _apply_defaults(fig)

    fig = px.scatter(
        merged,
        x="desmat_km2",
        y="area_ha",
        color="uf",
        hover_data=["zona_nome", "ano"],
        labels={
            "desmat_km2": "Floresta → Pastagem (km²)",
            "area_ha": "Soja PAM (ha)",
            "uf": "Estado",
        },
        opacity=0.7,
        template="plotly_white",
    )
    return _apply_defaults(fig, "Correlação: Desflorestamento × Expansão Soja")


def fig_indirect_deforestation_index(df_mb: pd.DataFrame) -> go.Figure:
    """
    Bar chart: (pastagem→soja) / (floresta→pastagem) ratio per region.
    Higher ratio = more indirect deforestation pressure in Cerrado/Matopiba.
    """
    pas_soja = (
        df_mb[df_mb["transicao"] == "pastagem_para_soja"]
        .groupby("zona_nome", as_index=False)["area_km2"]
        .sum()
        .rename(columns={"area_km2": "pas_soja"})
    )
    flor_past = (
        df_mb[df_mb["transicao"] == "floresta_para_pastagem"]
        .groupby("zona_nome", as_index=False)["area_km2"]
        .sum()
        .rename(columns={"area_km2": "flor_past"})
    )
    ratio = pas_soja.merge(flor_past, on="zona_nome", how="outer").fillna(0)
    ratio["indice"] = ratio["pas_soja"] / ratio["flor_past"].replace(0, float("nan"))
    ratio = ratio.dropna(subset=["indice"]).sort_values("indice", ascending=False).head(30)

    fig = go.Figure(
        go.Bar(
            x=ratio["indice"],
            y=ratio["zona_nome"],
            orientation="h",
            marker_color="#ff7f0e",
        )
    )
    fig.update_layout(
        xaxis_title="Índice (Pastagem→Soja / Floresta→Pastagem)",
        yaxis_title="Região",
        yaxis=dict(autorange="reversed"),
    )
    return _apply_defaults(fig, "Índice de Desflorestamento Indireto (Top 30 Regiões)")


# ---------------------------------------------------------------------------
# Tab 4 — Heatmap Explorer
# ---------------------------------------------------------------------------

def fig_heatmap(
    df_mb: pd.DataFrame,
    transition: str = "floresta_para_pastagem",
    ufs: list[str] | None = None,
    top_n: int = 30,
) -> go.Figure:
    """
    Heatmap: year-pair (x) × top-N regions (y), colour = area_km2.
    """
    sub = df_mb[df_mb["transicao"] == transition].copy()
    if ufs:
        sub = sub[sub["uf"].isin(ufs)]

    agg = sub.groupby(["zona_nome", "par_anos"], as_index=False)["area_km2"].sum()

    top_regions = (
        agg.groupby("zona_nome")["area_km2"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index.tolist()
    )
    agg = agg[agg["zona_nome"].isin(top_regions)]

    pivot = agg.pivot_table(
        index="zona_nome", columns="par_anos", values="area_km2", fill_value=0
    )
    # Sort regions by total area (highest on top)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    label = TRANSITION_LABELS.get(transition, transition)
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="YlOrRd",
            colorbar=dict(title="km²"),
            hoverongaps=False,
        )
    )
    fig.update_xaxes(tickangle=45, title_text="Par de Anos")
    fig.update_yaxes(title_text="Região")
    return _apply_defaults(fig, f"Heatmap: {label}")


# ---------------------------------------------------------------------------
# Tab 1 KPI helpers (return scalar values)
# ---------------------------------------------------------------------------

def compute_kpis(df_mb: pd.DataFrame, df_pam: pd.DataFrame) -> dict:
    """
    Compute scalar KPIs for the national overview cards.
    Returns a dict with keys: total_deforestation_km2, peak_year,
    top_region, top_uf, total_soy_ha.
    """
    defor_types = ["floresta_para_pastagem", "floresta_para_soja",
                   "savana_para_pastagem", "savana_para_soja"]
    defor = df_mb[df_mb["transicao"].isin(defor_types)]

    total_km2 = defor["area_km2"].sum()

    peak_year_series = defor.groupby("ano_fim")["area_km2"].sum()
    peak_year = int(peak_year_series.idxmax()) if not peak_year_series.empty else None

    top_region_series = defor.groupby("zona_nome")["area_km2"].sum()
    top_region = top_region_series.idxmax() if not top_region_series.empty else "N/A"

    top_uf_series = defor.groupby("uf")["area_km2"].sum()
    top_uf = top_uf_series.idxmax() if not top_uf_series.empty else "N/A"

    soy = df_pam[df_pam["cultura"] == "soja"]
    total_soy_ha = soy["area_ha"].sum()

    return dict(
        total_deforestation_km2=total_km2,
        peak_year=peak_year,
        top_region=top_region,
        top_uf=top_uf,
        total_soy_ha=total_soy_ha,
    )
