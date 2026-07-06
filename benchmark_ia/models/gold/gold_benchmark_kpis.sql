{{ config(materialized='table') }}

WITH run_stats AS (
    SELECT 
        run_id,
        map_name,
        model_name,
        assist_mode,
        MAX(turn) AS total_turns,
        SUM(CAST(is_useless_move AS INT)) AS useless_moves,
        
        -- Extraction des métriques pour les pièces
        MAX(initial_gold) AS total_gold,
        MAX(coins_collected) AS total_collected,
        
        -- Trouve le premier tour où coins_collected passe à 1
        MIN(CASE WHEN coins_collected > 0 THEN turn END) AS steps_to_first_coin
        
    FROM {{ ref('silver_game_turns') }}
    GROUP BY 1, 2, 3, 4
)

SELECT 
    map_name,
    model_name,
    assist_mode,
    COUNT(run_id) AS nb_simulations,
    
    -- Le KPI Taux de succès (Success rate)
    ROUND(AVG(total_collected * 100.0 / total_gold), 1) AS success_rate_pct,
    
    -- Le KPI Wasted move rate
    ROUND(AVG(useless_moves * 100.0 / total_turns), 1) AS wasted_move_rate_pct,
    
    -- Les KPIs d'efficacité temporelle
    ROUND(AVG(steps_to_first_coin), 1) AS avg_steps_to_first_coin,
    
    -- Attention à la division par zéro si aucune pièce n'est ramassée
    ROUND(AVG(total_turns / NULLIF(total_collected, 0)), 1) AS avg_steps_per_coin

FROM run_stats
GROUP BY 1, 2, 3
ORDER BY map_name, assist_mode DESC