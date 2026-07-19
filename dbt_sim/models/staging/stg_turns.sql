-- Staging : lecture brute des parquet `turns` (1 ligne = 1 pas de jeu)
select
    run_id,
    schema_version,
    turn,
    player_row,
    player_col,
    player_hp,
    gold_delta_row,
    gold_delta_col,
    gold_dist_min,
    enemy_delta_row,
    enemy_delta_col,
    decision,
    combat,
    enemy_killed,
    gold_collected,
    coins_collected,
    coins_remaining,
    wasted_move,
    player_died
from read_parquet('{{ var("bronze_path") }}/turns/*.parquet')
