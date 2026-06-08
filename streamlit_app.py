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
    
    # Nettoyage des noms de colonnes
    df.columns = [str(c).strip() for c in df.columns]
    
    # Si la première colonne s'appelle "Unnamed: 0" ou "A", on la renomme "Âge"
    if "Unnamed" in df.columns[0] or df.columns[0] == "A":
        df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    
    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    age_col = "Âge"
    
    # Liste EXACTE de tes colonnes de statistiques (d'après ta capture d'écran)
    stats_cols = ['UTIL', 'ATTA', 'FINI', 'CREA', 'CENT', 'CONS', 'DRIB', 'PERC', 'ENGA', 'RECU', 'DEFE', 'ANTI', 'AERI']
    
    # Liste de tes colonnes de rôles
    roles_cols = ['SL', 'BB', 'MN', 'ST', 'RC']
    
    # Filtrer pour ne garder que celles qui existent vraiment dans ton fichier
    stats_cols = [c for c in stats_cols if c in df.columns]
    roles_cols = [c for c in roles_cols if c in df.columns]
    
    # Attribution du rôle majeur (la note la plus BASSE entre tes rôles)
    if roles_cols:
        df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    else:
        df['Rôle Majeur'] = "Non défini"
        
    # Calcul des centiles sur une base fixe de 362 joueurs
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[f'{col} (Centile)'] = (abs((df[col] / 362) - 1) * 100).round().astype(int)
            
    return df, player_col, age_col, stats_cols

try:
    df, player_col, age_col, stats_cols = load_and_process_data()
except Exception as e:
    st.error(f"Erreur lors du traitement du fichier : {e}")
    st.stop()

# Code couleur officiel pour l'affichage de tes centiles
def get_color_style(val):
    try:
        val = float(val)
        if 0 <= val <= 10: return 'background-color: #8A2BE2; color: white;' # Violet
        elif 11 <= val <= 29: return 'background-color: #FF4D4D; color: white;' # Rouge
        elif 30 <= val <= 49: return 'background-color: #FFA500; color: black;' # Orange
        elif 50 <= val <= 69: return 'background-color: #FFFF4D; color: black;' # Jaune
        elif 70 <= val <= 89: return 'background-color: #4CD964; color: black;' # Vert
        elif 90 <= val <= 100: return 'background-color: #00BFFF; color: black;' # Bleu clair
    except:
        pass
    return ''

def color_centiles(val):
    return get_color_style(val)

# --- INTERFACE UTILISATEUR ---
st.title("⚽ Dashboard de Scouting - Milieux de Terrain")

st.sidebar.header("Filtres de Recherche")

# Filtre par Âge
try:
    df[age_col] = pd.to_numeric(df[age_col], errors='coerce').fillna(20).astype(int)
    age_min, age_max = int(df[age_col].min()), int(df[age_col].max())
    selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))
    filtered_df = df[(df[age_col] >= selected_age[0]) & (df[age_col] <= selected_age[1])]
except:
    filtered_df = df.copy()

# Filtre par Rôle
if 'Rôle Majeur' in df.columns and df['Rôle Majeur'].nunique() > 1:
    unique_roles = list(df['Rôle Majeur'].unique())
    selected_roles = st.sidebar.multiselect("Filtrer par Rôle", options=unique_roles, default=unique_roles)
    filtered_df = filtered_df[filtered_df['Rôle Majeur'].isin(selected_roles)]

tab1, tab2, tab3 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur"])

# 1. Onglet Base de données
with tab1:
    st.subheader("Base globale des joueurs")
    cols_to_show = [player_col, age_col]
    if 'Équipe' in df.columns: cols_to_show.append('Équipe')
    if 'M' in df.columns: cols_to_show.append('M')
    if 'Rôle Majeur' in df.columns: cols_to_show.append('Rôle Majeur')
    
    centile_cols = [f'{c} (Centile)' for c in stats_cols]
    cols_to_show += centile_cols
    cols_to_show = [c for c in cols_to_show if c in filtered_df.columns]
    
    if centile_cols:
        st.dataframe(filtered_df[cols_to_show].style.applymap(color_centiles, subset=[c for c in centile_cols if c in cols_to_show]), use_container_width=True)
    else:
        st.dataframe(filtered_df[cols_to_show], use_container_width=True)

# 2. Onglet Profil Joueur
with tab2:
    st.subheader("Analyse d'un joueur")
    player_list = filtered_df[player_col].unique() if player_col in filtered_df.columns else []
    
    if len(player_list) > 0:
        selected_player = st.selectbox("Choisir un joueur", player_list)
        p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Nom", str(p_data[player_col]))
            st.metric("Âge", f"{p_data[age_col]} ans")
            if 'Équipe' in p_data: st.markdown(f"**Club :** {p_data['Équipe']}")
            if 'M' in p_data: st.metric("Note Moyenne (M)", round(float(p_data['M']), 2))
            if 'Rôle Majeur' in p_data: st.markdown(f"### Rôle Principal : **{p_data['Rôle Majeur']}**")
            
        with col2:
            st.write("### Centiles par caractéristique")
            for c in stats_cols:
                c_centile = f'{c} (Centile)'
                if c_centile in p_data:
                    val = p_data[c_centile]
                    style = get_color_style(val)
                    st.markdown(f"<div style='{style} padding:8px; border-radius:5px; margin-bottom:5px; font-weight:bold;'>{c} : {val}%</div>", unsafe_allow_html=True)
    else:
        st.write("Aucun joueur disponible.")

# 3. Onglet Comparateur
with tab3:
    st.subheader("Comparateur de joueurs")
    all_players = df[player_col].unique() if player_col in df.columns else []
    if len(all_players) > 1:
        c1, c2 = st.columns(2)
        with c1: p1 = st.selectbox("Joueur 1", all_players, index=0)
        with c2: p2 = st.selectbox("Joueur 2", all_players, index=1)
        
        p1_data = df[df[player_col] == p1].iloc[0]
        p2_data = df[df[player_col] == p2].iloc[0]
        
        comp_rows = []
        for c in stats_cols:
            c_centile = f'{c} (Centile)'
            if c_centile in df.columns:
                comp_rows.append({"Statistique": c, f"{p1} (Centile)": p1_data[c_centile], f"{p2} (Centile)": p2_data[c_centile]})
        
        if comp_rows:
            comp_df = pd.DataFrame(comp_rows)
            st.dataframe(comp_df.style.applymap(color_centiles, subset=[f"{p1} (Centile)", f"{p2} (Centile)"]), use_container_width=True)
