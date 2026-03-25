"""
Shared constants for the MapBiomas × PAM dashboard.
"""

PIXEL_AREA_KM2 = 0.0009  # 30m × 30m pixel

# IBGE UF codes derived from the first 2 digits of zona_id / cod_rgint
UF_DICT: dict[int, str] = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA",
    16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE",
    24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE",
    29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT",
    52: "GO", 53: "DF",
}

UF_NAMES: dict[str, str] = {
    "RO": "Rondônia", "AC": "Acre", "AM": "Amazonas", "RR": "Roraima",
    "PA": "Pará", "AP": "Amapá", "TO": "Tocantins", "MA": "Maranhão",
    "PI": "Piauí", "CE": "Ceará", "RN": "Rio Grande do Norte",
    "PB": "Paraíba", "PE": "Pernambuco", "AL": "Alagoas",
    "SE": "Sergipe", "BA": "Bahia", "MG": "Minas Gerais",
    "ES": "Espírito Santo", "RJ": "Rio de Janeiro", "SP": "São Paulo",
    "PR": "Paraná", "SC": "Santa Catarina", "RS": "Rio Grande do Sul",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "GO": "Goiás", "DF": "Distrito Federal",
}

# Transition types grouped by theme
TRANSITION_GROUPS: dict[str, list[str]] = {
    "deforestation": [
        "floresta_para_pastagem",
        "floresta_para_soja",
        "floresta_para_outras_temp",
        "floresta_para_cana",
        "floresta_para_veg_sec",
    ],
    "cerrado": [
        "savana_para_pastagem",
        "savana_para_soja",
        "savana_para_outras_temp",
    ],
    "soy_expansion": [
        "pastagem_para_soja",
        "pastagem_para_outras_temp",
        "pastagem_para_cana",
        "pastagem_para_veg_sec",
    ],
    "recovery": [
        "soja_para_veg_sec",
    ],
    "stable": [
        "floresta_estavel",
        "pastagem_estavel",
        "soja_estavel",
        "savana_estavel",
    ],
}

# Reverse lookup: transition name → group
TRANSITION_TO_GROUP: dict[str, str] = {
    t: group
    for group, transitions in TRANSITION_GROUPS.items()
    for t in transitions
}

# Human-readable transition labels (Portuguese)
TRANSITION_LABELS: dict[str, str] = {
    "floresta_para_pastagem":    "Floresta → Pastagem",
    "floresta_para_soja":        "Floresta → Soja",
    "floresta_para_outras_temp": "Floresta → Outras Temp.",
    "floresta_para_cana":        "Floresta → Cana",
    "floresta_para_veg_sec":     "Floresta → Veg. Secundária",
    "savana_para_pastagem":      "Savana → Pastagem",
    "savana_para_soja":          "Savana → Soja",
    "savana_para_outras_temp":   "Savana → Outras Temp.",
    "pastagem_para_soja":        "Pastagem → Soja",
    "pastagem_para_outras_temp": "Pastagem → Outras Temp.",
    "pastagem_para_cana":        "Pastagem → Cana",
    "pastagem_para_veg_sec":     "Pastagem → Veg. Secundária",
    "soja_para_veg_sec":         "Soja → Veg. Secundária",
    "floresta_estavel":          "Floresta Estável",
    "pastagem_estavel":          "Pastagem Estável",
    "soja_estavel":              "Soja Estável",
    "savana_estavel":            "Savana Estável",
}

# PAM crops: internal key → display label
CROP_LABELS: dict[str, str] = {
    "soja":             "Soja (Soy)",
    "milho":            "Milho (Corn)",
    "cana":             "Cana-de-açúcar (Sugarcane)",
    "algodao_herbaceo": "Algodão Herbáceo (Cotton)",
    "algodao_arboreo":  "Algodão Arbóreo (Tree Cotton)",
}

# Mapping from IBGE raw crop names in PAM CSVs to internal keys.
# CSVs are UTF-8 with BOM. These are the exact strings after decoding.
PAM_CROP_MAP: dict[str, str] = {
    "Soja (em gr\u00e3o)":                        "soja",
    "Milho (em gr\u00e3o)":                        "milho",
    "Cana-de-a\u00e7\u00facar":                    "cana",
    "Algod\u00e3o herb\u00e1ceo (em caro\u00e7o)": "algodao_herbaceo",
    "Algod\u00e3o arb\u00f3reo (em caro\u00e7o)":  "algodao_arboreo",
}

# Group-level color palette (Plotly-compatible)
GROUP_COLORS: dict[str, str] = {
    "deforestation": "#d62728",
    "cerrado":       "#ff7f0e",
    "soy_expansion": "#ffd700",
    "recovery":      "#2ca02c",
    "stable":        "#aec7e8",
}

# Per-transition color map (derived from group colors with alpha variation)
TRANSITION_COLORS: dict[str, str] = {
    "floresta_para_pastagem":    "#d62728",
    "floresta_para_soja":        "#e86c6c",
    "floresta_para_outras_temp": "#f0a0a0",
    "floresta_para_cana":        "#c05050",
    "floresta_para_veg_sec":     "#a01010",
    "savana_para_pastagem":      "#ff7f0e",
    "savana_para_soja":          "#ffb366",
    "savana_para_outras_temp":   "#ffd9a8",
    "pastagem_para_soja":        "#ffd700",
    "pastagem_para_outras_temp": "#ffe566",
    "pastagem_para_cana":        "#fffaaa",
    "pastagem_para_veg_sec":     "#c8e06b",
    "soja_para_veg_sec":         "#2ca02c",
    "floresta_estavel":          "#1f77b4",
    "pastagem_estavel":          "#aec7e8",
    "soja_estavel":              "#98df8a",
    "savana_estavel":            "#ffbb78",
}

YEARS = list(range(2008, 2025))
YEAR_PAIRS = [f"{y}_{y+1}" for y in range(2008, 2024)]
