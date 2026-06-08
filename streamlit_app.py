import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# 1. Chargement et traitement des données
@st.cache_data
def load_and_process_data():
    # Lecture du fichier ODS
 df = pd.read_excel("MILIEUX.ods")
    
    # Définition des colonnes
    roles_cols = ['SL', 'BB', 'MN', 'ST', 'RC']
    stats_cols = ['Util', 'Attaque', 'Finition', 'Création', 'Centres', 
                  'Construction', 'Dribble', 'Percussion', 'Engagement', 
                  'Récupérations', 'Défense', 'Anticipation', 'Aérien']
    
    # Attribution du rôle (la note la plus BASSE entre SL, BB, MN, ST, RC)
    df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    
    # Calcul des centiles pour les statistiques clés (sur une base fixe de 362 joueurs)
    for col in stats_cols:
        if col in df.columns:
            df[f'{col} (Centile)'] = (abs((df[col] / 362) - 1) * 100).round().astype(int)
            
    return df, roles_cols, stats_cols

try:
    df, roles_cols, stats_cols = load_and_process_data()
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier MILIEUX.ods : {e}")
    st.info("Vérifiez que le fichier est bien nommé 'MILIEUX.ods' et à la racine du projet.")
    st.stop()

# Fonctions pour appliquer le code couleur demandé
def get_color_style(val):
    if 0 <= val <= 10:
        return 'background-color: #8A2BE2; color: white;' # Violet
    elif 11 <= val <= 29:
        return 'background-color: #FF4D4D; color: white;' # Rouge
    elif 30 <= val <= 49:
        return 'background-color: #FFA500; color: black;' # Orange
    elif 50 <= val <= 69:
        return 'background-color: #FFFF4D; color: black;' # Jaune
    elif 70 <= val <= 89:
        return 'background-color: #4CD964; color: black;' # Vert
    elif 90 <= val <= 100:
        return 'background-color: #00BFFF; color: black;' # Bleu clair
    return ''

def color_centiles(val):
    return get_color_style(val)

# --- INTERFACE UTILISATEUR ---
st.title("⚽ Dashboard de Scouting - Milieux de Terrain")

# Barre latérale pour les filtres globaux
st.sidebar.header("Filtres de Recherche")
age_min, age_max = int(df.iloc[:, 0].min()), int(df.iloc[:, 0].max()) # Colonne A pour l'âge
selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))

selected_roles = st.sidebar.multiselect("Filtrer par Rôle", options=roles_cols, default=roles_cols)

# Filtrer le dataset
filtered_df = df[(df.iloc[:, 0] >= selected_age[0]) & 
                 (df.iloc[:, 0] <= selected_age[1]) & 
                 (df['Rôle Majeur'].isin(selected_roles))]

# Onglets de l'application
tab1, tab2, tab3 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur"])

with tab1:
    st.subheader("Liste des joueurs et leurs centiles")
    
    # Sélection des colonnes à afficher (Nom en Col B, Âge en Col A, M en Col D, Rôle, et les Centiles)
    display_cols = [df.columns[1], df.columns[0], 'M', 'Rôle Majeur'] + [f'{c} (Centile)' for c in stats_cols]
    
    centile_cols_format = [f'{c} (Centile)' for c in stats_cols]
    styled_df = filtered_df[display_cols].style.applymap(color_centiles, subset=centile_cols_format)
    
    st.dataframe(styled_df, use_container_width=True)

with tab2:
    st.subheader("Analyse d'un joueur")
    player_column = df.columns[1] # Nom du joueur en colonne B
    player_list = filtered_df[player_column].unique()
    
    selected_player = st.selectbox("Choisir un joueur", player_list)
    
    if selected_player:
        p_data = filtered_df[filtered_df[player_column] == selected_player].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Nom", p_data[player_column])
            st.metric("Âge", f"{p_data.iloc[0]} ans")
            st.metric("Note Moyenne (M)", p_data['M'])
            st.markdown(f"### Rôle Principal : **{p_data['Rôle Majeur']}**")
            
        with col2:
            st.write("### Centiles par caractéristique")
            for c in stats_cols:
                centile_val = p_data[f'{c} (Centile)']
                color_css = get_color_style(centile_val)
                st.markdown(
                    f"<div style='{color_css} padding:8px; border-radius:5px; margin-bottom:5px; font-weight:bold;'>"
                    f"{c} : {centile_val}%"
                    f"</div>", 
                    unsafe_allow_html=True
                )

with tab3:
    st.subheader("Comparer deux joueurs")
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        p1 = st.selectbox("Joueur 1", df[player_column].unique(), index=0)
    with col_comp2:
        p2 = st.selectbox("Joueur 2", df[player_column].unique(), index=min(1, len(df)-1))
        
    if p1 and p2:
        p1_data = df[df[player_column] == p1].iloc[0]
        p2_data = df[df[player_column] == p2].iloc[0]
        
        comp_data = []
        for c in stats_cols:
            comp_data.append({
                "Caractéristique": c,
                f"{p1} (Centile)": p1_data[f'{c} (Centile)'],
                f"{p2} (Centile)": p2_data[f'{c} (Centile)']
            })
        
        comp_df = pd.DataFrame(comp_data)
        st.dataframe(
            comp_df.style.applymap(color_centiles, subset=[f"{p1} (Centile)", f"{p2} (Centile)"]),
            use_container_width=True
        )
