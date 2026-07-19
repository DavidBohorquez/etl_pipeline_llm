"""
Rapport de benchmark — joueur LLM (simulation ETL).
Lit les KPI gold produits par dbt-duckdb et les explique.

Lancer :  python -m streamlit run reporting/app.py
Mise a jour : `dbt run` (dans dbt_sim/) puis rafraichir la page.
"""
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

# =========================================================================
# Config
# =========================================================================
DB_PATH = Path(__file__).resolve().parent.parent / "dbt_sim" / "sim.duckdb"

# Palette categorielle Okabe-Ito (CVD-safe). Ordre FIXE par entite, jamais cycle.
ALGO_ORDER = ["raw", "hint", "solved"]
ALGO_COLORS = {"raw": "#D55E00", "hint": "#0072B2", "solved": "#E69F00"}
COLOR_SCALE = alt.Scale(domain=ALGO_ORDER, range=[ALGO_COLORS[a] for a in ALGO_ORDER])
COLOR_ENC = alt.Color("algo_level:N", scale=COLOR_SCALE, sort=ALGO_ORDER,
                      legend=alt.Legend(title="Niveau algo"))

# --- Description de la simulation (documentee ET affichee) ----------------
VOID, PLAYER, ENNEMY, GOLD = 0, 1, 2, 3
SYMBOLS = {VOID: "·", PLAYER: "🧍", ENNEMY: "👹", GOLD: "💰"}
INITIAL_MAP = [
    [0, 0, 0, 0, 0, 0, 3],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [1, 0, 2, 3, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 3],
]

ALGO_DEF = {
    "raw":    "LLM seul — reçoit uniquement les distances, doit déduire la direction. Charge algo minimale.",
    "hint":   "LLM assisté — reçoit les deltas signés (or + ennemi), décide direction et combat. Point d'équilibre.",
    "solved": "Règle déterministe — un if/else donne la direction ; le LLM ne fait qu'exécuter. Charge algo maximale.",
}

AXES = pd.DataFrame([
    ["algo_level", "raw · hint · solved", "Axe PRINCIPAL : charge algorithmique (couleur des séries)."],
    ["temperature", "0.0 · 0.2 · 0.3 · 0.5 · 0.7", "Axe SECONDAIRE : aléa d'échantillonnage du LLM (axe x)."],
    ["seed", "1 → 5", "Répétitions par (algo, temp>0) pour estimer moyenne + variance."],
    ["model", "google/gemma-4-e4b", "Modèle LLM interrogé."],
    ["map_id", "enemy_path_leurre_v1", "Layout de la carte (ennemi sur le chemin + leurre)."],
], columns=["variable", "valeurs", "rôle"])

GAME_RULES = pd.DataFrame([
    ["Grille", "7 × 7 cases"],
    ["Objectif", "ramasser TOUTES les pièces (💰)"],
    ["PV joueur", "3"],
    ["PV ennemi", "2"],
    ["Combat", "entrer sur un ennemi = −1 PV chacun ; 0 PV → mort"],
    ["Ennemis", "statiques (déterminisme)"],
    ["Leurre", "pièce la plus proche gardée par un ennemi ; pièces sûres plus loin"],
    ["Fin de partie", "toutes les pièces prises · joueur mort · max 20 tours"],
], columns=["règle", "valeur"])

GLOSSARY = pd.DataFrame([
    ["success_rate_mean", "Part de l'or total ramassée (moyenne sur les seeds). 1.0 = tout l'or."],
    ["success_rate_std", "Écart-type de la réussite sur les seeds = ROBUSTESSE. 0 = déterministe."],
    ["revisit_rate_mean", "Part de cases re-visitées → tourne en rond (oscillation)."],
    ["non_productive_rate_mean", "Pas où le joueur bouge SANS se rapprocher de l'or (hors combat/ramassage)."],
    ["wasted_move_rate_mean", "Pas bloqués (mur / hors grille)."],
    ["steps_to_first_coin_mean", "Nombre de pas avant la 1re pièce."],
    ["hp_lost_mean", "PV perdus (départ = 3)."],
    ["death_rate", "Part de runs où le joueur meurt."],
    ["avg_gold_dist", "Distance moyenne à l'or la plus proche (proxy de trajectoire)."],
    ["turns_mean", "Nombre de tours moyen."],
], columns=["colonne", "définition"])


# =========================================================================
# Helpers
# =========================================================================
st.set_page_config(page_title="Benchmark joueur LLM", page_icon="🎮", layout="wide")


@st.cache_data(ttl=60)
def load(table: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(f"SELECT * FROM {table}").df()
    finally:
        con.close()


def render_map(grid) -> str:
    return "\n".join("  ".join(SYMBOLS[c] for c in row) for row in grid)


if not DB_PATH.exists():
    st.error(
        f"Base introuvable : {DB_PATH}\n\n"
        "Génère d'abord les KPI :\n```\ncd dbt_sim\ndbt run --profiles-dir .\n```"
    )
    st.stop()

cfg_all = load("gold_config_kpis")
runs_all = load("gold_run_kpis")
cfg_all = cfg_all.assign(
    lo=(cfg_all["success_rate_mean"] - cfg_all["success_rate_std"]).clip(lower=0),
    hi=(cfg_all["success_rate_mean"] + cfg_all["success_rate_std"]).clip(upper=1),
)

# --- Filtres globaux (sidebar) -------------------------------------------
st.sidebar.header("Filtres")
sel_algo = st.sidebar.multiselect("Niveaux algo", ALGO_ORDER, default=ALGO_ORDER)
temps = sorted(cfg_all["temperature"].unique())
sel_temp = st.sidebar.select_slider("Température max", options=temps, value=temps[-1])
st.sidebar.caption("Palette Okabe-Ito (CVD-safe). Ordre fixe : raw · hint · solved.")

cfg = cfg_all[(cfg_all["algo_level"].isin(sel_algo)) & (cfg_all["temperature"] <= sel_temp)]
runs = runs_all[(runs_all["algo_level"].isin(sel_algo)) & (runs_all["temperature"] <= sel_temp)]

# =========================================================================
# En-tete
# =========================================================================
st.title("🎮 Benchmark — joueur LLM déterministe")
st.markdown(
    "**Question :** où placer le curseur entre *charge algorithmique* et *charge LLM* ? "
    "On compare trois niveaux d'aide (`raw` / `hint` / `solved`) sous différentes "
    "températures d'échantillonnage."
)

tab_over, tab_charts, tab_tables, tab_cfg, tab_gloss = st.tabs(
    ["📊 Vue d'ensemble", "📈 Graphiques", "🗄️ Tables & trajectoires",
     "⚙️ Config & dimensions", "📖 Glossaire"]
)

# =========================================================================
# Onglet 1 — Vue d'ensemble
# =========================================================================
with tab_over:
    st.subheader("Réussite déterministe (température = 0)")
    base0 = cfg_all[cfg_all["temperature"] == 0.0].set_index("algo_level")
    cols = st.columns(len(ALGO_ORDER))
    for c, algo in zip(cols, ALGO_ORDER):
        if algo in base0.index:
            r = base0.loc[algo]
            c.metric(
                label=f"{algo}",
                value=f"{r['success_rate_mean']*100:.0f}% or",
                delta=f"{r['revisit_rate_mean']*100:.0f}% boucles",
                delta_color="inverse",
            )
            c.caption(ALGO_DEF[algo])

    st.subheader("Réussite vs température")
    band = alt.Chart(cfg).mark_area(opacity=0.15).encode(
        x=alt.X("temperature:Q", title="Température"),
        y=alt.Y("lo:Q", title="Taux d'or", scale=alt.Scale(domain=[0, 1])),
        y2="hi:Q", color=COLOR_ENC,
    )
    line = alt.Chart(cfg).mark_line(point=True, strokeWidth=2).encode(
        x="temperature:Q",
        y=alt.Y("success_rate_mean:Q", scale=alt.Scale(domain=[0, 1])),
        color=COLOR_ENC,
        tooltip=["algo_level", "temperature",
                 alt.Tooltip("success_rate_mean:Q", format=".2f"),
                 alt.Tooltip("success_rate_std:Q", format=".2f")],
    )
    st.altair_chart((band + line).properties(height=340), use_container_width=True)
    st.info(
        "**Lecture :** `hint` maximise l'or avec une variance faible (bande fine) → point "
        "d'équilibre. `raw` échoue et tourne en rond. `solved` est plat (déterministe) mais "
        "fonce sur le leurre → pièces perdues."
    )

# =========================================================================
# Onglet 2 — Graphiques (chacun avec son explication)
# =========================================================================
with tab_charts:
    st.caption("Axes de tous les graphiques : **x = température** · **couleur = niveau algo** · **y = le KPI**.")

    st.subheader("1. Réussite vs température")
    st.altair_chart((band + line).properties(height=320), use_container_width=True)
    with st.expander("Axes & lecture"):
        st.markdown(
            "- **y** = `success_rate_mean` (part de l'or ramassée)\n"
            "- **bande** = ± `success_rate_std` (robustesse sur les seeds)\n"
            "- **couleur** = niveau algo\n\n"
            "Une bande large = résultats instables d'un seed à l'autre."
        )

    st.subheader("2. Boucles / oscillations")
    revisit = alt.Chart(cfg).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("temperature:Q", title="Température"),
        y=alt.Y("revisit_rate_mean:Q", title="Taux de re-visite", scale=alt.Scale(domain=[0, 1])),
        color=COLOR_ENC,
        tooltip=["algo_level", "temperature", alt.Tooltip("revisit_rate_mean:Q", format=".2f")],
    )
    st.altair_chart(revisit.properties(height=300), use_container_width=True)
    with st.expander("Pourquoi ce KPI ?"):
        st.markdown(
            "`revisit_rate` = part de cases déjà visitées. Il capture les allers-retours que "
            "`wasted_move` (pas bloqués) rate : un joueur qui oscille BAS/HAUT fait des pas "
            "*valides* mais inutiles. C'est le vrai « déplacement inutile » de `raw`."
        )

    st.subheader("3. Distribution des pièces (par run)")
    box = alt.Chart(runs).mark_boxplot(size=28).encode(
        x=alt.X("algo_level:N", sort=ALGO_ORDER, title=None),
        y=alt.Y("coins_collected:Q", title="Pièces ramassées"),
        color=COLOR_ENC,
    )
    st.altair_chart(box.properties(height=300), use_container_width=True)
    with st.expander("Lecture"):
        st.markdown(
            "Chaque boîte = distribution des pièces sur tous les runs du niveau. "
            "Boîte étroite = stable (`hint`, `solved`) ; large = instable (`raw`)."
        )

# =========================================================================
# Onglet 3 — Tables & trajectoires
# =========================================================================
with tab_tables:
    st.subheader("gold_config_kpis — KPI par configuration (agrégé sur les seeds)")
    st.caption("Table phare du benchmark : 1 ligne par (niveau algo, température).")
    show_cfg = cfg[["algo_level", "temperature", "n_runs", "success_rate_mean",
                    "success_rate_std", "revisit_rate_mean", "non_productive_rate_mean",
                    "wasted_move_rate_mean", "steps_to_first_coin_mean", "hp_lost_mean",
                    "death_rate"]].round(3).sort_values(["algo_level", "temperature"])
    st.dataframe(show_cfg, use_container_width=True, hide_index=True)
    st.download_button("⬇️ gold_config_kpis.csv", show_cfg.to_csv(index=False),
                       "gold_config_kpis.csv", "text/csv")

    st.subheader("gold_run_kpis — KPI par run individuel")
    show_runs = runs[["run_id", "algo_level", "temperature", "seed", "coins_collected",
                      "success_rate", "turns_played", "revisit_rate", "hp_lost",
                      "died"]].round(3)
    st.dataframe(show_runs, use_container_width=True, hide_index=True)
    st.download_button("⬇️ gold_run_kpis.csv", show_runs.to_csv(index=False),
                       "gold_run_kpis.csv", "text/csv")

    st.divider()
    st.subheader("🔎 Trajectoire d'un run (silver_turns)")
    st.caption("Trace pas-à-pas : comprendre CHAQUE choix du LLM.")
    runs_lbl = runs.sort_values(["algo_level", "temperature", "seed"]).copy()
    runs_lbl["label"] = (runs_lbl["algo_level"] + " | t=" + runs_lbl["temperature"].astype(str)
                         + " | seed=" + runs_lbl["seed"].astype(str)
                         + " | " + runs_lbl["run_id"].str.slice(0, 8))
    choice = st.selectbox("Choisir un run", runs_lbl["label"].tolist())
    if choice:
        rid = runs_lbl.loc[runs_lbl["label"] == choice, "run_id"].iloc[0]
        trace = load("silver_turns")
        trace = trace[trace["run_id"] == rid].sort_values("turn")
        tcols = ["turn", "decision", "player_row", "player_col", "player_hp",
                 "gold_dist_min", "combat", "gold_collected", "got_closer",
                 "non_productive_move"]
        c1, c2 = st.columns([3, 2])
        with c1:
            st.dataframe(trace[tcols], use_container_width=True, hide_index=True, height=380)
        with c2:
            path = alt.Chart(trace).mark_line(point=True).encode(
                x=alt.X("player_col:Q", title="colonne", scale=alt.Scale(domain=[-0.5, 6.5])),
                y=alt.Y("player_row:Q", title="ligne", scale=alt.Scale(domain=[6.5, -0.5])),
                order="turn:Q",
                color=alt.Color("turn:Q", scale=alt.Scale(scheme="blues"), title="tour"),
                tooltip=["turn", "decision", "player_row", "player_col", "player_hp"],
            ).properties(height=380, title="Chemin parcouru")
            st.altair_chart(path, use_container_width=True)

# =========================================================================
# Onglet 4 — Config & dimensions
# =========================================================================
with tab_cfg:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Carte de départ")
        st.text(render_map(INITIAL_MAP))
        st.caption("🧍 joueur (3,0) · 👹 ennemi (3,2) · 💰 leurre (3,3) + pièces sûres (0,6) et (6,6)")
    with c2:
        st.subheader("Règles de game design")
        st.dataframe(GAME_RULES, use_container_width=True, hide_index=True)

    st.subheader("Axes & variables du benchmark")
    st.dataframe(AXES, use_container_width=True, hide_index=True)

    st.subheader("Les 3 niveaux de charge algorithmique")
    for algo in ALGO_ORDER:
        st.markdown(f"- **{algo}** — {ALGO_DEF[algo]}")

    st.subheader("Pipeline (médaillon)")
    st.code(
        "notebook game_loop\n"
        "   → BRONZE  data/bronze/{runs,turns}/*.parquet   (brut)\n"
        "   → dbt     staging → silver (typé, joint, dérivé)\n"
        "   → GOLD    gold_run_kpis · gold_config_kpis      (KPI)\n"
        "   → Streamlit (ce rapport)",
        language="text",
    )

# =========================================================================
# Onglet 5 — Glossaire
# =========================================================================
with tab_gloss:
    st.subheader("Définition des KPI / colonnes")
    st.dataframe(GLOSSARY, use_container_width=True, hide_index=True)
    st.caption("Ces colonnes proviennent des modèles dbt gold ; chaque .sql = une table.")