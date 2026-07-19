-- Gold : KPI par run (1 ligne = 1 partie). Base des aggregats metiers.
-- NB : PV de depart = 3 (PLAYER_MAX_HP dans la simulation).
with s as (
    select * from {{ ref('silver_turns') }}
)
select
    run_id,
    any_value(algo_level)      as algo_level,
    any_value(temperature)     as temperature,
    any_value(seed)            as seed,
    any_value(model)           as model,
    any_value(model_params_b)  as model_params_b,
    any_value(map_id)          as map_id,
    any_value(gold_total)      as gold_total,

    -- efficacite / reussite
    max(coins_collected)                               as coins_collected,
    max(coins_collected) * 1.0 / any_value(gold_total) as success_rate,
    count(*)                                           as turns_played,
    min(case when gold_collected then turn end)        as steps_to_first_coin,

    -- deplacements inutiles
    sum(case when wasted_move then 1 else 0 end)                  as wasted_moves,
    sum(case when wasted_move then 1 else 0 end) * 1.0 / count(*) as wasted_move_rate,
    sum(case when non_productive_move then 1 else 0 end)                  as non_productive_moves,
    sum(case when non_productive_move then 1 else 0 end) * 1.0 / count(*) as non_productive_rate,

    -- boucles / oscillations : peu de cases distinctes = joueur qui tourne en rond
    count(distinct cell_key)                                 as distinct_cells,
    1 - count(distinct cell_key) * 1.0 / count(*)            as revisit_rate,

    -- combat / survie
    sum(case when combat then 1 else 0 end)      as combats,
    sum(case when enemy_killed then 1 else 0 end) as enemy_kills,
    bool_or(player_died)                          as died,
    3 - min(player_hp)                            as hp_lost,

    -- distance moyenne a l'or (proxy de la trajectoire ; cf. moyenne glissante en dataviz)
    avg(gold_dist_min) as avg_gold_dist
from s
group by run_id
