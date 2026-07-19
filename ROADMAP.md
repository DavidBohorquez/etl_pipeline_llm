# Roadmap — LLM player benchmark (ETL)

Aligned to `SPECS.md`. Grading: benchmark /8, data engineering /8, consignes /4.

## Design decisions (locked)

**Game design (§1.2)**
- Coins: **multiple** — collect all gold, episode ends when board empty / player dead / `max_turns`.
- Combat: **allowed**, deterministic. Player HP 3, enemy HP 2. Entering an enemy cell = attack: −1 HP each. 0 HP dies. Enemy dies → player advances onto cell.
- Enemies: **static** (determinism).
- Layout: **enemy-on-path + leurre** — nearest coin is a decoy guarded by an enemy; safe coins farther. `map_id = enemy_path_leurre_v1`.

**Perception / algo balance (§1.1)** — three levels = the main benchmark axis:
- `raw` — LLM gets distances only, must infer direction.
- `hint` — signed deltas to nearest gold + enemy; LLM maps delta→direction and weighs combat vs HP. **Target balance point.**
- `solved` — explicit deterministic rule ladder; LLM rubber-stamps. Grabs the leurre, takes damage.

**Why `hint` is the thesis:** `solved` walks into the trap (algorithm can't reason about the leurre); `hint` can route around it. That contrast is the benchmark story.

## Benchmark axes (§2.1)
1. Algorithmic load: `raw` × `hint` × `solved`.
2. LLM model: `model_name`, `model_params_b`.
3. LLM sampling: temperature sweep `[0.0, 0.2, 0.3, 0.5, 0.7]` × `N_SEEDS` repetitions.
   - `temp=0` is deterministic → 1 seed. `temp>0` → N seeds to estimate mean/variance.
   - Story: robustness vs temperature per algo level — `raw` degrades fast, `hint` stays stable, `solved` is temperature-immune.
   - Default grid = `(1+5+5+5+5) × 3 algos = 63 runs`.

## KPIs (§2.2) — computed in the gold layer
- `steps_to_first_coin`, `steps_per_coin`
- `coins_collected / gold_total` (success rate)
- `wasted_move_rate` (blocked / off-grid moves)
- `hp_lost`, `died` (bool), `leurre_grabbed` (bool)
- `combats`, `enemy_kills`
- sliding mean of distance-to-nearest-gold over turns (spec line 44)

## Data model (§2.3)
Two grains, normalized:
- **`runs`** — one row per simulation = the config/dimensions (independent variables) + `run_id`, `timestamp`, `schema_version`, `gold_total`, `turns_played`.
- **`turns`** — one row per step (raw observations) + `run_id` FK.

Schema coherence: every row carries `schema_version`; one parquet file per `run_id` (append-only, no rewrite of old data). Bumping the sim → bump `schema_version`, old runs stay readable.

## Medallion pipeline (§2.3) — parquet + duckdb + dbt-duckdb
- **Bronze** — raw `runs/*.parquet` + `turns/*.parquet`, exactly as emitted. *(this step)*
- **Silver** — dbt models: typed, deduped, turns joined to run config, per-turn derived fields (moved-toward-gold, distance).
- **Gold** — dbt aggregates = one KPI row per run / per config-group. Feeds the report.

## Step-by-step

1. ✅ Stabilize sim: directional perception, deterministic combat, 3 algo levels.
2. ✅ **Bronze**: runs/turns split, `make_config`, parquet write, benchmark runner.
3. ✅ Benchmark runner grid: `algo_level × temperature × seed` → 63 runs → bronze.
4. ✅ dbt-duckdb project (`dbt_sim/`): bronze parquet → silver → gold KPIs.
5. ✅ Dataviz report (`reporting/app.py`, Streamlit) reading gold; rebuild via `dbt run` + refresh.
6. ⏳ Justification write-up: defend every design/KPI choice (spec line 3).

## Repo layout (target)
```
ETL/
  npc_brain.ipynb        # sim engine + bronze generation
  data/bronze/{runs,turns}/*.parquet
  dbt_sim/               # dbt-duckdb: models/silver, models/gold
  reporting/             # dataviz output
  ROADMAP.md
```
