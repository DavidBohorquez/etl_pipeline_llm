{{ config(materialized='table') }}

WITH raw_data AS (
    SELECT * FROM {{ ref('bronze_logs') }}
)

SELECT 
    run_id::VARCHAR AS run_id,
    map_name::VARCHAR AS map_name,
    model_name::VARCHAR AS model_name,
    assist_mode::BOOLEAN AS assist_mode, -- NOUVELLE COLONNE
    turn::INT AS turn,
    player_row::INT AS player_row,
    player_col::INT AS player_col,
    decision::VARCHAR AS decision,
    nearest_gold_distance::FLOAT AS nearest_gold_distance,
    is_useless_move::BOOLEAN AS is_useless_move,
    
    nearest_gold_distance - LAG(nearest_gold_distance) OVER (PARTITION BY run_id ORDER BY turn) AS distance_delta

FROM raw_data