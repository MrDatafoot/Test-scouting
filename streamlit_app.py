import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# Injection CSS globale pour l'application (Thème sombre Gaming)
st.markdown("""
    <style>
        .stApp {
            background-color: #0d1117 !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #888888 !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom-color: #00BFFF !important;
        }
        div[data-testid="stDataFrame"] {
            background-color: #161b22;
            border-radius: 8px;
            padding: 10px;
            border: 1px solid #30363d;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Chargement et traitement des données
@st.cache_data
def load_and_process_data():
    df = pd.read_excel("MILIEUX.ods")
    df.columns = [str(c).strip() for c in df.columns]
    
    if "Unnamed" in df.columns[0] or df.columns[0] == "A":
        df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    
    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    age_col = "Âge"
    
    stats_mapping = {
        'UTIL': 'MINUTES', 'ATTA': 'ATTAQUE', 'FINI': 'FINITION', 
        'CREA': 'CRÉATION', 'CONS': 'CONSTRUCTION', 'DRIB': 'DRIBBLES', 
        'PERC': 'PERCUSSION', 'ENGA': 'ENGAGEMENT', 'RECU': 'RÉCUPÉRATION', 
        'DEFE': 'UN CONTRE UN', 'ANTI': 'ANTICIPATION', 'AERI': 'AÉRIEN'
    }
    
    ordered_keys = ['UTIL', 'ATTA', 'FINI', 'CREA', 'CONS', 'DRIB', 'PERC', 'ENGA', 'RECU', 'DEFE', 'ANTI', 'AERI']
    stats_cols = [c for c in ordered_keys if c in df.columns]
    
    roles_cols = [c for c in ['SL', 'BB', 'MN', 'ST', 'RC'] if c in df.columns]
    if roles_cols:
        df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    else:
        df['Rôle Majeur'] = "Non défini"
        
    centile_cols_generated = []
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        centile_name = f'{col} (Centile)'
        df[centile_name] = (abs((df[col] / 362) - 1) * 100).round().astype(int)
        centile_cols_generated.append(centile_name)
    
    if centile_cols_generated:
        df['Note_Moyenne_Stats'] = df[centile_cols_generated].mean(axis=1).round(1)
    else:
        df['Note_Moyenne_Stats'] = 0
            
    return df, player_col, age_col, stats_cols, stats_mapping

try:
    df, player_col, age_col, stats_cols, stats_mapping = load_and_process_data()
except Exception as e:
    st.error(f"Erreur lors du chargement : {e}")
    st.stop()

def get_color_emoji(val):
    try:
        val = float(val)
        if 90 <= val <= 100: return "🔵"
        elif 70 <= val < 90: return "🟢"
        elif 50 <= val < 70: return "🟡"
        elif 30 <= val < 50: return "🟠"
        else: return "🔴"
    except: return "⚪"

def get_colors_raw(val):
    try:
        val = float(val)
        if 90 <= val <= 100: return '#00BFFF'
        elif 70 <= val < 90: return '#4CD964'
        elif 50 <= val < 70: return '#FFFF4D'
        elif 30 <= val < 50: return '#D35400'
        return '#FF4D4D'
    except: return '#444444'

st.title("⚽ Dashboard de Scouting - Milieux de Terrain")

st.sidebar.header("Filtres de Recherche")
df[age_col] = pd.to_numeric(df[age_col], errors='coerce').fillna(20).astype(int)
age_min, age_max = int(df[df[age_col] > 0][age_col].min()), int(df[age_col].max())
selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))
filtered_df = df[(df[age_col] >= selected_age[0]) & (df[age_col] <= selected_age[1])]

tab1, tab2, tab3, tab4 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur", "📈 Analyse Graphique"])

with tab1:
    st.subheader("Base globale des joueurs")
    table_df = pd.DataFrame()
    clubs = filtered_df['Équipe'].fillna('Sans club').astype(str)
    table_df['JOUEUR / CLUB'] = filtered_df[player_col].str.upper() + " (" + clubs + ")"
    table_df['ÂGE'] = filtered_df[age_col]
    table_df['NOTE MOYENNE'] = filtered_df['Note_Moyenne_Stats']
    for c in stats_cols:
        table_df[stats_mapping[c]] = filtered_df[f"{c} (Centile)"].apply(lambda x: f"{get_color_emoji(x)} {x}")
    
    st.dataframe(table_df.sort_values(by='NOTE MOYENNE', ascending=False), hide_index=True, use_container_width=True)

with tab2:
    st.subheader("👤 Fiche d'identité")
    player_list = filtered_df[player_col].unique()
    selected_player = st.selectbox("Choisir un joueur", player_list)
    p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
    st.write(f"Détails complets pour {p_data[player_col]}")
    # (Tes autres éléments visuels ici...)

with tab3:
    st.subheader("⚔️ Comparateur")
    players = st.multiselect("Sélectionnez les joueurs", player_list, default=player_list[:2])
    # (Ta logique de comparaison ici...)

with tab4:
    st.subheader("📈 Analyse Graphique")
    # (Ta logique plotly ici...)
