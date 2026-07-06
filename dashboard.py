import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="IA Benchmark", page_icon="🤖", layout="wide")
st.title("🤖 Analyse de la simulation IA : Impact de l'Algorithme")

# Connexion à la base DuckDB générée par dbt
@st.cache_data
def load_data():
    try:
        # On pointe vers le fichier généré par dbt
        con = duckdb.connect('benchmark_ia/data/benchmark.duckdb')
        
        # Récupération des tables
        gold = con.execute("SELECT * FROM main.gold_benchmark_kpis").df()
        silver = con.execute("SELECT * FROM main.silver_game_turns").df()
        
        # On remplace les True/False par des labels plus lisibles pour les graphiques
        gold['Mode'] = gold['assist_mode'].map({True: 'IA Assistée (Python filtre)', False: 'IA Surchargée (Zéro filtre)'})
        silver['Mode'] = silver['assist_mode'].map({True: 'Assistée', False: 'Surchargée'})
        
        return gold, silver
    except Exception as e:
        st.error(f"Erreur DuckDB : {e}")
        return pd.DataFrame(), pd.DataFrame()

df_gold, df_silver = load_data()

if df_gold.empty:
    st.warning("Aucune donnée trouvée. Lance d'abord la simulation et la commande 'dbt run' !")
else:
    # --- SECTION 1 : VUE MACRO (Table Gold) ---
    st.header("🏆 KPIs Comparatifs (Couche Gold)")
    
    # Création de deux colonnes pour comparer directement les deux modes
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ IA Assistée (Python filtre)")
        df_assisted = df_gold[df_gold['assist_mode'] == True]
        if not df_assisted.empty:
            st.metric("Taux de Succès (Or ramassé)", f"{round(df_assisted['success_rate_pct'].mean(), 1)} %")
            st.metric("Taux de mouvements inutiles", f"{round(df_assisted['wasted_move_rate_pct'].mean(), 1)} %")
            st.metric("Tours moyens avant la 1ère pièce", round(df_assisted['avg_steps_to_first_coin'].mean(), 1))
            st.metric("Tours moyens par pièce", round(df_assisted['avg_steps_per_coin'].mean(), 1))
        else:
            st.info("Aucune partie assistée trouvée.")
            
    with col2:
        st.subheader("❌ IA Surchargée (Zéro filtre)")
        df_solo = df_gold[df_gold['assist_mode'] == False]
        if not df_solo.empty:
            st.metric("Taux de Succès (Or ramassé)", f"{round(df_solo['success_rate_pct'].mean(), 1)} %")
            st.metric("Taux de mouvements inutiles", f"{round(df_solo['wasted_move_rate_pct'].mean(), 1)} %")
            st.metric("Tours moyens avant la 1ère pièce", round(df_solo['avg_steps_to_first_coin'].mean(), 1))
            st.metric("Tours moyens par pièce", round(df_solo['avg_steps_per_coin'].mean(), 1))
        else:
            st.info("Aucune partie surchargée trouvée.")

    # Graphique en barres pour le Benchmark (Wasted move rate)
    fig_bar = px.bar(
        df_gold, 
        x="map_name", 
        y="wasted_move_rate_pct", 
        color="Mode", 
        barmode="group",
        title="Benchmark : Taux de mouvements inutiles (Wasted Move Rate)",
        labels={"wasted_move_rate_pct": "% Mouvements Inutiles", "map_name": "Carte jouée"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- SECTION 2 : VUE MICRO (Table Silver) ---
    st.header("📍 Suivi de trajectoire (Couche Silver)")
    
    # Graphique : Évolution de la distance avec l'or
    fig_line = px.line(
        df_silver, 
        x="turn", 
        y="nearest_gold_distance", 
        color="run_id",
        line_dash="Mode",
        markers=True,
        title="Évolution de la distance vers l'or (Pointillés = IA Surchargée)",
        labels={"turn": "Numéro du tour", "nearest_gold_distance": "Distance vers la pièce", "run_id": "ID de la partie"}
    )
    
    # On inverse l'axe Y (plus on s'approche de 0, mieux c'est)
    fig_line.update_yaxes(autorange="reversed")
    
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Affichage des logs bruts du parcours pour audit
    with st.expander("Voir le détail des mouvements de la couche Silver"):
        st.dataframe(df_silver[['run_id', 'Mode', 'turn', 'decision', 'is_useless_move', 'distance_delta', 'coins_collected']])