# dbt_sim — pipeline médaillon (duckdb)

Transforme les logs bruts de la simulation (parquet bronze) en KPI métiers.

```
bronze (parquet)  ->  staging (view)  ->  silver (view)  ->  gold (table)
  runs/*.parquet       stg_runs           silver_turns        gold_run_kpis
  turns/*.parquet      stg_turns          (turns⋈runs +       gold_config_kpis
                                           champs dérivés)
```

## Modèles

- **staging/** — lecture brute des parquet (`read_parquet`), typage.
- **silver/silver_turns** — turns enrichis des dimensions du run + champs dérivés par pas :
  `got_closer` (rapproché de l'or), `non_productive_move` (bougé sans progresser, hors combat/ramassage/changement de cible), `cell_key` (détection de boucles).
- **gold/gold_run_kpis** — 1 ligne par run : `success_rate`, `steps_to_first_coin`,
  `wasted_move_rate`, `non_productive_rate`, `revisit_rate`, `hp_lost`, `avg_gold_dist`, `died`.
- **gold/gold_config_kpis** — 1 ligne par `(algo_level, temperature)`, agrégé sur les seeds :
  moyenne **et** écart-type (réussite + robustesse). Table phare du benchmark.

## Lancer

Depuis `dbt_sim/` (les chemins parquet sont relatifs à ce dossier) :

```bash
pip install dbt-duckdb
dbt run --profiles-dir .
```

Requête de contrôle :

```bash
dbt show --profiles-dir . -s gold_config_kpis --limit 30
```

Ou directement en duckdb :

```sql
SELECT * FROM gold_config_kpis ORDER BY algo_level, temperature;
```

## Cohérence de schéma

Chaque parquet porte `schema_version`. Si les colonnes de la simulation changent,
incrémenter `SCHEMA_VERSION` dans le notebook ; les anciens runs restent lisibles
(filtrer par version au besoin dans le staging).

## Paramètre

- `bronze_path` (var, défaut `../data/bronze`) — racine des parquet bronze.
```
