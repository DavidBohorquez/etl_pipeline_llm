{{ config(materialized='table') }}

WITH run_stats AS (
    SELECT 
        run_id,
        map_name,
        model_name,
        assist_mode, -- NOUVELLE COLONNE
        MAX(turn) AS total_turns,
        SUM(CAST(is_useless_move AS INT)) AS useless_moves
    FROM {{ ref('silver_game_turns') }}
    GROUP BY 1, 2, 3, 4
)

SELECT 
    map_name,
    model_name,
    assist_mode,
    COUNT(run_id) AS nb_simulations,
    ROUND(AVG(total_turns), 2) AS avg_tours_par_partie,
    ROUND(AVG(useless_moves), 2) AS avg_mouvements_inutiles
FROM run_stats
GROUP BY 1, 2, 3
ORDER BY map_name, assist_mode DESC