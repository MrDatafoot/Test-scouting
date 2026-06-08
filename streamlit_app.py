import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# 1. Chargement et traitement des données
@st.cache_data
def load_and_process_data():
    df = pd.read_excel("MILIEUX.ods")
    
    # Nettoyage sommaire des noms de colonnes au cas où (espaces en trop)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Définition des colonnes de rôles
    roles_cols = [c for c in ['SL', 'BB', 'MN', 'ST', 'RC'] if c in df.columns]
    
    # Liste théorique des statistiques attendues
    all_stats = ['Util', 'Attaque', 'Finition', 'Création', 'Centres', 
                 'Construction', 'Dribble', 'Percussion', 'Engagement', 
                 'Récupérations', 'Défense', 'Anticipation', 'Aérien']
    
    # On ne garde que celles qui existent RÉELLEMENT dans ton fichier
    stats_cols = [c for c in all_stats if c in df.columns]
    
    # Attribution du rôle majeur si les colonnes existent
    if roles_cols:
        df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    else:
        df['Rôle Majeur'] = "Non défini"
    
    # Calcul des centiles uniquement sur les colonnes présentes
    for col in stats_cols:
        df[f'{col} (Centile)'] = (abs((df[col] / 362) - 1) * 100).round().astype(int)
            
    return df, roles_cols, stats_cols

try:
    df, roles_cols, stats_cols = load_and_process_data()
except Exception as e:
    st.error(f"Erreur lors du traitement du fichier : {e}")
    st.stop()

# Fonctions pour appliquer le code couleur demandé
def get_color_style(val):
    try:
        val = float(val)
        if 0 <= val <= 10: return 'background-color: #8A2BE2; color: white;'
        elif 11 <= val <= 29: return 'background-color: #FF4D4D; color: white;'
        elif 30 <= val <= 49: return 'background-color: #FFA500; color: black;'
        elif 50 <= val <= 69: return 'background-color: #FFFF4D; color: black;'
        elif 70 <= val <= 89: return 'background-color: #4CD964; color: black;'
        elif 90 <= val <= 100: return 'background-color: #00BFFF; color: black;'
    except:
        pass
    return ''

def color_centiles(val):
    return get_color_style(val)

# --- INTERFACE UTILISATEUR ---
st.title("⚽ Dashboard de Scouting - Milieux de Terrain")

st.sidebar.header("Filtres de Recherche")

# Gestion dynamique de la colonne Âge (première colonne)
age_col = df.columns[0]
try:
    age_min, age_max = int(df[age_col].min()), int(df[age_col].max())
    selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))
    filtered_df = df[(df[age_col] >= selected_age[0]) & (df[age_col] <= selected_age[1])]
except:
    st.sidebar.warning("Impossible de filtrer par âge.")
    filtered_df = df.copy()

# Filtre par rôle
if roles_cols and 'Rôle Majeur' in df.columns:
    unique_roles = list(df['Rôle Majeur'].unique())
    selected_roles = st.sidebar.multiselect("Filtrer par Rôle", options=unique_roles, default=unique_roles)
    filtered_df = filtered_df[filtered_df['Rôle Majeur'].isin(selected_roles)]

tab1, tab2, tab3 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur"])

# Trouver le nom de la colonne joueur (deuxième colonne) et note M
player_column = df.columns[1]
m_col = 'M' if 'M' in df.columns else (df.columns[3] if len(df.columns) > 3 else df.columns[0])

with tab1:
    st.subheader("Liste des joueurs et leurs centiles")
    
    # Construction dynamique des colonnes d'affichage pour éviter le crash KeyError
    display_cols = [player_column, age_col]
    if 'M' in df.columns: display_cols.append('M')
    if 'Rôle Majeur' in df.columns: display_cols.append('Rôle Majeur')
    
    centile_cols_format = [f'{c} (Centile)' for c in stats_cols]
    display_cols += centile_cols_format
    
    # Sécurité : on ne garde que ce qui existe vraiment
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    
    if centile_cols_format:
        styled_df = filtered_df[display_cols].style.applymap(color_centiles, subset=[c for c in centile_cols_format if c in display_cols])
    else:
        styled_df = filtered_df[display_cols]
        
    st.dataframe(styled_df, use_container_width=True)

with tab2:
    st.subheader("Analyse d'un joueur")
    player_list = filtered_df[player_column].unique() if player_column in filtered_df.columns else []
    
    if len(player_list) > 0:
        selected_player = st.selectbox("Choisir un joueur", player_list)
        p_data = filtered_df[filtered_df[player_column] == selected_player].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Nom", str(p_data[player_column]))
            st.metric("Âge", f"{p_data[age_col]} ans")
            if 'M' in df.columns: st.metric("Note Moyenne (M)", p_data['M'])
            if 'Rôle Majeur' in df.columns: st.markdown(f"### Rôle Principal : **{p_data['Rôle Majeur']}**")
            
        with col2:
            st.write("### Centiles par caractéristique")
            for c in stats_cols:
                c_centile = f'{c} (Centile)'
                if c_centile in p_data:
                    centile_val = p_data[c_centile]
                    color_css = get_color_style(centile_val)
                    st.markdown(
                        f"<div style='{color_css} padding:8px; border-radius:5px; margin-bottom:5px; font-weight:bold;'>"
                        f"{c} : {centile_val}%"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
    else:
        st.write("Aucun joueur trouvé.")

with tab3:
    st.subheader("Comparer deux joueurs")
    if player_column in df.columns and len(df[player_column].unique()) > 1:
        col_comp1, col_comp2 = st.columns(2)
        all_players = df[player_column].unique()
        
        with col_comp1:
            p1 = st.selectbox("Joueur 1", all_players, index=0)
        with col_comp2:
            p2 = st.selectbox("Joueur 2", all_players, index=1)
            
        p1_data = df[df[player_column] == p1].iloc[0]
        p2_data = df[df[player_column] == p2].iloc[0]
        
        comp_data = []
        for c in stats_cols:
            c_centile = f'{c} (Centile)'
            if c_centile in df.columns:
                comp_data.append({
                    "Caractéristique": c,
                    f"{p1} (Centile)": p1_data[c_centile],
                    f"{p2} (Centile)": p2_data[c_centile]
                })
        
        if comp_data:
            comp_df = pd.DataFrame(comp_data)
            subset_cols = [f"{p1} (Centile)", f"{p2} (Centile)"]
            st.dataframe(
                comp_df.style.applymap(color_centiles, subset=[c for c in subset_cols if c in comp_df.columns]),
                use_container_width=True
            )
    else:
        st.write("Pas assez de joueurs pour comparer.")
