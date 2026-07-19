# ETL — Benchmark LLM player

Simulation d'agent LLM dans une grille (collecte d'or, combats déterministes) instrumentée
pour produire un pipeline de data engineering complet (bronze → silver → gold) et un rapport
de benchmark. Spec complète dans [SPECS.md](SPECS.md), décisions de design et avancement dans
[ROADMAP.md](ROADMAP.md).

## Pipeline

```
npc_brain.ipynb          dbt_sim/                    reporting/
  sim + bronze     -->     staging → silver → gold  -->  Streamlit
  (parquet)                (dbt-duckdb)                  (lit gold via duckdb)
```

1. **Bronze** — `npc_brain.ipynb` fait tourner la simulation (perception `raw` / `hint` /
   `solved` × température × seed) et écrit `data/bronze/{runs,turns}/*.parquet`.
2. **Silver / Gold** — [dbt_sim/](dbt_sim/README.md) transforme le bronze en KPI métiers
   (`gold_run_kpis`, `gold_config_kpis`) via dbt-duckdb.
3. **Reporting** — [reporting/](reporting/README.md) affiche ces KPI dans un dashboard
   Streamlit (réussite vs température, robustesse, boucles, distribution des pièces).

## Démarrage rapide

```bash
# 1. Simulation -> bronze : exécuter npc_brain.ipynb

# 2. Silver + Gold
cd dbt_sim
pip install dbt-duckdb
dbt run --profiles-dir .
cd ..

# 3. Rapport
pip install streamlit altair duckdb pandas
python -m streamlit run reporting/app.py
```

## Repo layout

```
ETL/
  npc_brain.ipynb        # sim engine + génération bronze
  data/bronze/{runs,turns}/*.parquet
  dbt_sim/                # dbt-duckdb : staging/silver/gold
  reporting/              # dashboard Streamlit
  ROADMAP.md              # décisions de design + avancement
  SPECS.md                # énoncé du projet
```

## Design decisions clés

- Combats déterministes autorisés, ennemis statiques.
- Layout `enemy_path_leurre_v1` : pièce proche gardée par un ennemi (leurre), pièces sûres
  plus loin — sert à distinguer les niveaux d'algo.
- Trois niveaux de charge algorithmique (`raw`/`hint`/`solved`) × grille de température ×
  seeds → 63 runs de benchmark.
- Schéma versionné (`schema_version`) pour garder les anciens runs lisibles si la sim évolue.