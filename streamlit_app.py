import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# Injection CSS minimale pour garantir le fond sombre "gaming" de l'application
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
    
    # Mapping mis à jour sans la catégorie "CENTRES"
    stats_mapping = {
        'UTIL': 'MINUTES', 'ATTA': 'ATTAQUE', 'FINI': 'FINITION', 
        'CREA': 'CRÉATION', 'CONS': 'CONSTRUCTION', 'DRIB': 'DRIBBLES', 
        'PERC': 'PERCUSSION', 'ENGA': 'ENGAGEMENT', 'RECU': 'RÉCUPÉRATION', 'DEFE': 'UN CONTRE UN', 
        'ANTI': 'ANTICIPATION', 'AERI': 'AÉRIEN'
    }
    
    # Ordre strict mis à jour (sans 'CENT')
    ordered_keys = ['UTIL', 'ATTA', 'FINI', 'CREA', 'CONS', 'DRIB', 'PERC', 'ENGA', 'RECU', 'DEFE', 'ANTI', 'AERI']
    stats_cols = [c for c in ordered_keys if c in df.columns]
    
    roles_cols = [c for c in ['SL', 'BB', 'MN', 'ST', 'RC'] if c in df.columns]
    
    if roles_cols:
        df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    else:
        df['Rôle Majeur'] = "Non défini"
        
    # Calcul des centiles et de la note moyenne
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
    st.error(f"Erreur lors du traitement du fichier : {e}")
    st.stop()

# Code couleur unique pour bordure et texte
def get_colors(val):
    try:
        val = float(val)
        if 0 <= val <= 10: return '#8A2BE2'      # Violet
        elif 11 <= val <= 29: return '#FF4D4D'    # Rouge
        elif 30 <= val <= 49: return '#D35400'    # Orange
        elif 50 <= val <= 69: return '#FFFF4D'    # Jaune
        elif 70 <= val <= 89: return '#4CD964'    # Vert
        elif 90 <= val <= 100: return '#00BFFF'   # Bleu
    except:
        pass
    return '#444444'

def color_centiles(val):
    color = get_colors(val)
    return f'background-color: #161b22; color: {color}; border: 1px solid {color};'

# --- INTERFACE UTILISATEUR ---
st.title("⚽ Dashboard de Scouting - Milieux de Terrain")

st.sidebar.header("Filtres de Recherche")
try:
    df[age_col] = pd.to_numeric(df[age_col], errors='coerce').fillna(20).astype(int)
    age_min, age_max = int(df[age_col].min()), int(df[age_col].max())
    selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))
    filtered_df = df[(df[age_col] >= selected_age[0]) & (df[age_col] <= selected_age[1])]
except:
    filtered_df = df.copy()

tab1, tab2, tab3 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur"])

# 1. BASE DE DONNÉES
with tab1:
    st.subheader("Base globale des joueurs")
    
    base_cols = [player_col, age_col]
    if 'Équipe' in df.columns: 
        base_cols.append('Équipe')
    base_cols.append('Note_Moyenne_Stats')
    
    centile_cols = [f'{c} (Centile)' for c in stats_cols]
    all_cols_to_show = base_cols + centile_cols
    existing_cols = [c for c in all_cols_to_show if c in filtered_df.columns]
    
    view_df = filtered_df[existing_cols].copy()
    
    rename_dict = {'Note_Moyenne_Stats': 'NOTE MOYENNE'}
    for c in stats_cols:
        if f'{c} (Centile)' in view_df.columns:
            rename_dict[f'{c} (Centile)'] = stats_mapping[c]
    view_df.rename(columns=rename_dict, inplace=True)
    
    styled_columns = [stats_mapping[c] for c in stats_cols if stats_mapping[c] in view_df.columns]
    
    st.dataframe(
        view_df.style.map(color_centiles, subset=styled_columns), 
        use_container_width=True
    )

# 2. PROFIL JOUEUR
with tab2:
    st.subheader("👤 Fiche d'identité & Profil du Joueur")
    player_list = filtered_df[player_col].unique() if player_col in filtered_df.columns else []
    
    if len(player_list) > 0:
        selected_player = st.selectbox("Choisir un joueur", player_list)
        p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
        
        p_club = p_data['Équipe'] if 'Équipe' in p_data else "Non défini"
        p_role = p_data['Rôle Majeur'] if 'Rôle Majeur' in p_data else "Milieu"
        p_note = p_data['Note_Moyenne_Stats']
        
        p_taille = p_data['Taille'] if 'Taille' in p_data else "-"
        p_valeur = p_data['Valeur'] if 'Valeur' in p_data else "-"
        p_saison = "2025/2026"
        
        id_col1, id_col2 = st.columns([1.2, 2])
        
        with id_col1:
            st.markdown(f"""
                <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; text-align: center; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                    <div style='width: 110px; height: 110px; border-radius: 50%; background-color: #0d1117; border: 2px solid #00BFFF; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;'>
                        <span style='font-size: 50px;'>🏃‍♂️</span>
                    </div>
                    <div style='font-size: 24px; font-weight: bold; color: #ffffff; margin-bottom: 5px;'>{str(p_data[player_col]).upper()}</div>
                    <div style='font-size: 16px; font-weight: bold; color: #FF4D4D; margin-bottom: 15px;'>⚽ {p_club}</div>
                    <div style='background-color: #0d1117; border: 1px solid #30363d; padding: 6px 12px; border-radius: 20px; font-size: 13px; color: #4CD964; font-weight: bold;'>
                        {p_role}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with id_col2:
            st.markdown(f"""
                <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; height: 100%;'>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                        <div style='border-bottom: 1px solid #30363d; padding-bottom: 8px;'>
                            <div style='font-size: 11px; color: #8b949e; text-transform: uppercase;'>Âge</div>
                            <div style='font-size: 18px; font-weight: bold; color: #ffffff;'>🎂 {p_data[age_col]} ans</div>
                        </div>
                        <div style='border-bottom: 1px solid #30363d; padding-bottom: 8px;'>
                            <div style='font-size: 11px; color: #8b949e; text-transform
