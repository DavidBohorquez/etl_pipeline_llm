# reporting — dataviz (Streamlit)

Rapport de benchmark. Lit les tables **gold** (`gold_config_kpis`, `gold_run_kpis`)
depuis `dbt_sim/sim.duckdb` et les met en graphiques.

## Lancer

```bash
pip install streamlit altair duckdb pandas
python -m streamlit run reporting/app.py
```

Ouvre http://localhost:8501.

## Workflow "mise à jour à chaque run" (spec §2.3)

Pas de temps réel : on régénère puis on rafraîchit.

```bash
# 1. (option) nouveaux runs de simulation -> bronze parquet   (notebook)
# 2. recompute des KPI
cd dbt_sim && dbt run --profiles-dir . && cd ..
# 3. rafraîchir la page Streamlit (le cache expire en 60 s, ou bouton "Rerun")
```

## Graphiques

- **Réussite vs température** — ligne = taux d'or moyen, bande = ± écart-type (robustesse).
- **Boucles / oscillations** — `revisit_rate` par température.
- **Distribution des pièces** — boxplot par niveau algo (dispersion run-à-run).
- **Table KPI** — vue accessible de `gold_config_kpis`.

## Design

Palette catégorielle **Okabe-Ito** (CVD-safe), ordre fixe par niveau
(`raw` / `hint` / `solved`), légende toujours présente, un seul axe y par graphique.
