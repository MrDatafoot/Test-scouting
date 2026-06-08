import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# Injection de CSS pour basculer l'application en mode sombre "gaming" comme le visuel
st.markdown("""
    <style>
        .stApp {
            background-color: #0d1117;
        }
        h1, h2, h3, p, span, label {
            color: #ffffff !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #888888;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff;
            border-bottom-color: #00BFFF;
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
    
    # Mapping des colonnes réelles vers les noms propres du visuel
    stats_mapping = {
        'UTIL': 'MINUTES', 'ATTA': 'ATTAQUE', 'FINI': 'FINITION', 
        'CREA': 'CRÉATION', 'CONS': 'CONSTRUCTION', 'DRIB': 'DRIBBLES', 
        'PERC': 'PERCUSSION', 'RECU': 'RÉCUPÉRATION', 'DEFE': 'UN CONTRE UN', 
        'AERI': 'AÉRIEN', 'CENT': 'CENTRES', 'ENGA': 'ENGAGEMENT', 'ANTI': 'ANTICIPATION'
    }
    
    stats_cols = [c for c in stats_mapping.keys() if c in df.columns]
    roles_cols = [c for c in ['SL', 'BB', 'MN', 'ST', 'RC'] if c in df.columns]
    
    if roles_cols:
        df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    else:
        df['Rôle Majeur'] = "Non défini"
        
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[f'{col} (Centile)'] = (abs((df[col] / 362) - 1) * 100).round().astype(int)
            
    return df, player_col, age_col, stats_cols, stats_mapping

try:
    df, player_col, age_col, stats_cols, stats_mapping = load_and_process_data()
except Exception as e:
    st.error(f"Erreur lors du traitement du fichier : {e}")
    st.stop()

# Dictionnaire de couleurs (Fonds et Bordures) calqué sur le visuel
def get_colors(val):
    try:
        val = float(val)
        if 0 <= val <= 10: return '#8A2BE2', '#b066ff'      # Violet
        elif 11 <= val <= 29: return '#FF4D4D', '#ff8080'    # Rouge
        elif 30 <= val <= 49: return '#D35400', '#E67E22'    # Orange / Marron terne
        elif 50 <= val <= 69: return '#B39200', '#F1C40F'    # Jaune foncé / Or
        elif 70 <= val <= 89: return '#27AE60', '#2ECC71'    # Vert
        elif 90 <= val <= 100: return '#2980B9', '#3498DB'   # Bleu
    except:
        pass
    return '#222', '#444'

def color_centiles(val):
    bg, border = get_colors(val)
    return f'background-color: {bg}; color: white;'

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
    cols_to_show = [player_col, age_col]
    if 'Équipe' in df.columns: cols_to_show.append('Équipe')
    if 'M' in df.columns: cols_to_show.append('M')
    
    centile_cols = [f'{c} (Centile)' for c in stats_cols]
    cols_to_show += centile_cols
    cols_to_show = [c for c in cols_to_show if c in filtered_df.columns]
    
    if centile_cols:
        st.dataframe(filtered_df[cols_to_show].style.map(color_centiles, subset=[c for c in centile_cols if c in cols_to_show]), use_container_width=True)
    else:
        st.dataframe(filtered_df[cols_to_show], use_container_width=True)

# 2. PROFIL JOUEUR
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
            
        with col2:
            st.write("### Centiles par caractéristique")
            for c in stats_cols:
                c_centile = f'{c} (Centile)'
                if c_centile in p_data:
                    val = p_data[c_centile]
                    bg, border = get_colors(val)
                    label_clean = stats_mapping.get(c, c)
                    st.markdown(f"""
                        <div style='background-color: #161b22; border: 1px solid {border}; padding:10px; border-radius:6px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;'>
                            <span style='font-weight:bold; color:#fff; font-size:14px;'>{label_clean}</span>
                            <span style='background-color:{bg}; border: 2px solid {border}; color:white; padding:4px 12px; border-radius:4px; font-weight:bold; font-size:16px;'>{val}</span>
                        </div>
                    """, unsafe_allow_html=True)

# 3. COMPARATEUR (INSPIRÉ DU VISUEL)
with tab3:
    st.subheader("Comparateur de Cartes")
    all_players = df[player_col].unique() if player_col in df.columns else []
    
    if len(all_players) > 1:
        # Sélection de 2 à 4 joueurs pour coller au visuel
        selected_players = st.multiselect("Sélectionnez les joueurs à comparer (2 à 4)", options=all_players, default=list(all_players[:2]))
        
        if len(selected_players) >= 2:
            # Création de la structure en lignes (1 ligne par stat)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # En-tête avec les Noms des joueurs
            cols_header = st.columns([2] + [2] * len(selected_players))
            with cols_header[0]:
                st.markdown("<h3 style='text-align: left; color: #888 !important;'>STATISTIQUE</h3>", unsafe_allow_html=True)
                
            for idx, p_name in enumerate(selected_players):
                p_club = df[df[player_col] == p_name]['Équipe'].values[0] if 'Équipe' in df.columns else ""
                with cols_header[idx + 1]:
                    st.markdown(f"""
                        <div style='background-color: #161b22; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #30363d;'>
                            <div style='font-size: 20px; font-weight: bold; color: #fff;'>{p_name.upper()}</div>
                            <div style='font-size: 12px; color: #8b949e;'>{p_club}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
            
            # Affichage des lignes de stats
            for c in stats_cols:
                cols_data = st.columns([2] + [2] * len(selected_players))
                label_clean = stats_mapping.get(c, c)
                
                # Nom de la stat à gauche
                with cols_data[0]:
                    st.markdown(f"<div style='padding: 10px 0; font-size: 16px; font-weight: bold; color: #e6edf2; letter-spacing: 0.5px;'>{label_clean}</div>", unsafe_allow_html=True)
                
                # Notes des joueurs au milieu/droite
                for idx, p_name in enumerate(selected_players):
                    p_data = df[df[player_col] == p_name].iloc[0]
                    val = p_data[f'{c} (Centile)']
                    bg, border = get_colors(val)
                    
                    with cols_data[idx + 1]:
                        st.markdown(f"""
                            <div style='text-align: center; padding: 4px 0;'>
                                <span style='display: inline-block; background-color: #0d1117; border: 2px solid {border}; color: white; padding: 6px 18px; border-radius: 6px; font-weight: bold; font-size: 18px; min-width: 50px; box-shadow: inset 0 0 10px {bg};'>
                                    {val}
                                </span>
                            </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("Veuillez sélectionner au moins 2 joueurs.")
    else:
        st.write("Pas assez de données pour comparer.")
