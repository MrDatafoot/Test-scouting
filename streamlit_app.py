import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode

# Configuration page
st.set_page_config(page_title="Scouting Milieux", layout="wide")

# CSS identique à ta version stylisée
st.markdown("""
    <style>
        .stApp {background-color: #0d1117;}
        .fm-badge {padding: 4px 12px; border-radius: 6px; font-weight: bold; text-align: center;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_process_data():
    df = pd.read_excel("MILIEUX.ods")
    df.columns = [str(c).strip() for c in df.columns]
    if "Unnamed" in df.columns[0] or df.columns[0] == "A":
        df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    
    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    stats_mapping = {'UTIL': 'MINUTES', 'ATTA': 'ATTAQUE', 'FINI': 'FINITION', 'CREA': 'CRÉATION', 'CONS': 'CONSTRUCTION', 'DRIB': 'DRIBBLES', 'PERC': 'PERCUSSION', 'ENGA': 'ENGAGEMENT', 'RECU': 'RÉCUPÉRATION', 'DEFE': 'UN CONTRE UN', 'ANTI': 'ANTICIPATION', 'AERI': 'AÉRIEN'}
    stats_cols = [c for c in stats_mapping.keys() if c in df.columns]
    
    # Calculs
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Note_Moyenne_Stats'] = df[stats_cols].mean(axis=1).round(1)
    return df, player_col, stats_cols, stats_mapping

df, player_col, stats_cols, stats_mapping = load_and_process_data()

# --- INTERFACE ---
st.title("⚽ Dashboard de Scouting Complet")
tab1, tab2, tab3, tab4 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur", "📈 Analyse"])

# 1. BASE DE DONNÉES (Ag-Grid pour le TRI)
with tab1:
    st.subheader("Base globale des joueurs")
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filter=True)
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, theme='alpine', height=500, width='100%', 
           columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)

# 2. PROFIL JOUEUR
with tab2:
    st.subheader("👤 Fiche Identité")
    selected_player = st.selectbox("Choisir un joueur", df[player_col].unique())
    p_data = df[df[player_col] == selected_player].iloc[0]
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"### {p_data[player_col]}")
        st.write(f"Âge: {p_data['Âge']}")
    with col2:
        st.metric("Note Moyenne", p_data['Note_Moyenne_Stats'])

# 3. COMPARATEUR
with tab3:
    st.subheader("⚔️ Comparateur")
    players = st.multiselect("Sélectionnez les joueurs", df[player_col].unique(), default=df[player_col].iloc[:2])
    if players:
        comp_df = df[df[player_col].isin(players)]
        st.table(comp_df[[player_col, 'Note_Moyenne_Stats'] + stats_cols])

# 4. ANALYSE GRAPHIQUE
with tab4:
    st.subheader("📈 Analyse")
    fig = px.scatter(df, x='CREA', y='ATTA', color='Note_Moyenne_Stats', hover_name=player_col)
    st.plotly_chart(fig)
