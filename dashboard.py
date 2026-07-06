import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="IA Benchmark", page_icon="🤖", layout="wide")
st.title("🤖 Analyse de la simulation IA : Impact de l'Algorithme")

@st.cache_data
def load_data():
    try:
        con = duckdb.connect('benchmark_ia/data/benchmark.duckdb')
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
    st.warning("Aucune donnée trouvée.")
else:
    st.header("🏆 KPIs Comparatifs (Couche Gold)")
    
    # Création de deux colonnes pour comparer directement les deux modes
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ IA Assistée (Python filtre les murs/ennemis)")
        df_assisted = df_gold[df_gold['assist_mode'] == True]
        st.metric("Tours moyens par partie", round(df_assisted['avg_tours_par_partie'].mean(), 1))
        st.metric("Mouvements inutiles (collisions)", round(df_assisted['avg_mouvements_inutiles'].mean(), 1))
        
    with col2:
        st.subheader("❌ IA Surchargée (Le LLM se débrouille)")
        df_solo = df_gold[df_gold['assist_mode'] == False]
        st.metric("Tours moyens par partie", round(df_solo['avg_tours_par_partie'].mean(), 1))
        st.metric("Mouvements inutiles (collisions)", round(df_solo['avg_mouvements_inutiles'].mean(), 1))

    # Graphique en barres pour le Benchmark
    fig_bar = px.bar(
        df_gold, 
        x="map_name", 
        y="avg_mouvements_inutiles", 
        color="Mode", 
        barmode="group",
        title="Benchmark : Nombre de collisions contre les murs selon le mode",
        labels={"avg_mouvements_inutiles": "Mouvements inutiles moyens", "map_name": "Carte jouée"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    st.header("📍 Suivi de trajectoire (Couche Silver)")
    
    # On ajoute la couleur basée sur le "Mode" pour voir la différence de comportement
    fig_line = px.line(
        df_silver, 
        x="turn", 
        y="nearest_gold_distance", 
        color="run_id",
        line_dash="Mode",
        markers=True,
        title="Évolution de la distance vers l'or (Pointillés = IA Surchargée)",
        labels={"turn": "Tour", "nearest_gold_distance": "Distance vers la pièce", "run_id": "Partie"}
    )
    fig_line.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_line, use_container_width=True)