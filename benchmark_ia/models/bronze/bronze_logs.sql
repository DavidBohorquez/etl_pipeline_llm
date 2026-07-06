{{ config(materialized='view') }}

-- DuckDB lit directement tous les fichiers parquet présents dans le dossier data
SELECT * 
FROM read_parquet('data/bronze_*.parquet')