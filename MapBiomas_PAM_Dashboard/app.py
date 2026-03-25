"""
MapBiomas × PAM Dashboard
Brazil Land Use Transitions × Agricultural Production 2008–2024

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import sys
import pathlib

# Ensure the dashboard root is on the Python path so that `utils.*` resolves
# regardless of the working directory when streamlit launches the app.
_APP_DIR = pathlib.Path(__file__).parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

from utils.constants import CROP_LABELS, TRANSITION_GROUPS, TRANSITION_LABELS, UF_DICT
from utils.load_data import apply_filters, load_pam_by_region, load_transitions

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MapBiomas × PAM — Brasil 2008–2024",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Data loading (cached per session)
# ---------------------------------------------------------------------------

df_mb_full = load_transitions()
df_pam_full = load_pam_by_region()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

with st.sidebar:
    try:
        st.image(
            "https://mapbiomas.org/assets/images/logo.png",
            width=160,
            caption="MapBiomas × IBGE PAM",
        )
    except Exception:
        st.markdown("**MapBiomas × IBGE PAM**")
    st.title("Filtros Globais")
    st.caption("Os filtros abaixo se aplicam a todas as abas.")

    # ── Year range ────────────────────────────────────────────────────────────
    year_min = int(df_mb_full["ano_fim"].min())
    year_max = int(df_mb_full["ano_fim"].max())
    year_range = st.slider(
        "Intervalo de Anos",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
        step=1,
        key="global_years",
    )

    # ── State (UF) filter ─────────────────────────────────────────────────────
    all_ufs = sorted(df_mb_full["uf"].unique())
    selected_ufs = st.multiselect(
        "Estado (UF)",
        options=all_ufs,
        default=[],
        placeholder="Todos os estados",
        key="global_ufs",
    )

    # ── Transition group filter ───────────────────────────────────────────────
    group_options = list(TRANSITION_GROUPS.keys())
    group_labels = {
        "deforestation": "Desmatamento (Floresta)",
        "cerrado": "Conversão Cerrado/Savana",
        "soy_expansion": "Expansão Soja (Pastagem)",
        "recovery": "Recuperação",
        "stable": "Classes Estáveis",
    }
    selected_groups = st.multiselect(
        "Grupo de Transição",
        options=group_options,
        default=["deforestation", "cerrado", "soy_expansion"],
        format_func=lambda g: group_labels.get(g, g),
        key="global_groups",
    )

    # Expand groups to individual transition names
    if selected_groups:
        allowed_transitions = [
            t for g in selected_groups for t in TRANSITION_GROUPS[g]
        ]
    else:
        allowed_transitions = None  # no filter

    # ── Crop focus ───────────────────────────────────────────────────────────
    crop_options = list(CROP_LABELS.keys())
    selected_crops = st.multiselect(
        "Culturas (PAM)",
        options=crop_options,
        default=["soja", "milho", "cana"],
        format_func=lambda c: CROP_LABELS.get(c, c),
        key="global_crops",
    )

    st.divider()
    st.caption("Fonte: MapBiomas Col. 10 | IBGE PAM 5457")
    st.caption("Pixel = 900 m² (30 × 30 m)")

# ---------------------------------------------------------------------------
# Apply global filters
# ---------------------------------------------------------------------------

df_mb, df_pam = apply_filters(
    df_mb_full,
    df_pam_full,
    ufs=selected_ufs if selected_ufs else None,
    transitions=allowed_transitions,
    year_range=year_range,
    crops=selected_crops if selected_crops else None,
)

# Guard against empty data after aggressive filtering
if df_mb.empty:
    st.warning(
        "Nenhum dado de transição encontrado para os filtros selecionados. "
        "Ajuste os filtros na barra lateral."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌍 Visão Nacional",
    "📍 Regiões",
    "🌾 Culturas",
    "🔥 Heatmap",
    "📊 Dados",
    "🗺 Mapas Espaciais",
])

with tab1:
    from tabs.tab1_overview import render as render_tab1
    render_tab1(df_mb, df_pam)

with tab2:
    from tabs.tab2_region import render as render_tab2
    render_tab2(df_mb, df_pam)

with tab3:
    from tabs.tab3_crops import render as render_tab3
    render_tab3(df_mb, df_pam)

with tab4:
    from tabs.tab4_heatmap import render as render_tab4
    render_tab4(df_mb)

with tab5:
    from tabs.tab5_data import render as render_tab5
    render_tab5(df_mb, df_pam)

with tab6:
    from tabs.tab6_maps import render as render_tab6
    render_tab6(df_mb, df_pam)
