-- Gold : KPI par configuration (algo_level x temperature), aggreges sur les seeds.
-- Table "phare" du benchmark : moyenne ET variance -> montre reussite + robustesse.
with runs as (
    select * from {{ ref('gold_run_kpis') }}
)
select
    algo_level,
    temperature,
    count(*)                         as n_runs,

    -- reussite (moyenne) + robustesse (ecart-type sur les seeds)
    avg(success_rate)                as success_rate_mean,
    coalesce(stddev_samp(success_rate), 0) as success_rate_std,
    avg(coins_collected)             as coins_mean,

    -- efficacite
    avg(turns_played)                as turns_mean,
    avg(steps_to_first_coin)         as steps_to_first_coin_mean,
    avg(wasted_move_rate)            as wasted_move_rate_mean,
    avg(non_productive_rate)         as non_productive_rate_mean,
    avg(revisit_rate)                as revisit_rate_mean,
    coalesce(stddev_samp(revisit_rate), 0) as revisit_rate_std,

    -- survie
    avg(hp_lost)                     as hp_lost_mean,
    sum(case when died then 1 else 0 end) * 1.0 / count(*) as death_rate
from runs
group by algo_level, temperature
order by algo_level, temperature