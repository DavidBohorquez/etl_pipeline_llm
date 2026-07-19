-- Staging : lecture brute des parquet `runs` (1 ligne = 1 partie / config)
select
    run_id,
    schema_version,
    cast("timestamp" as timestamp) as run_ts,
    model,
    model_params_b,
    temperature,
    seed,
    algo_level,
    map_id,
    max_turns,
    gold_total,
    turns_played
from read_parquet('{{ var("bronze_path") }}/runs/*.parquet')
