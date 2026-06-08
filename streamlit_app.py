import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# Injection CSS pour le fond sombre "gaming" de l'application
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
    
    # Mapping mis à jour : "CENT" (Centres) est totalement retiré
    stats_mapping = {
        'UTIL': 'MINUTES', 'ATTA': 'ATTAQUE', 'FINI': 'FINITION', 
        'CREA': 'CRÉATION', 'CONS': 'CONSTRUCTION', 'DRIB': 'DRIBBLES', 
        'PERC': 'PERCUSSION', 'ENGA': 'ENGAGEMENT', 'RECU': 'RÉCUPÉRATION', 
        'DEFE': 'UN CONTRE UN', 'ANTI': 'ANTICIPATION', 'AERI': 'AÉRIEN'
    }
    
    # Ordre des clés sans 'CENT'
    ordered_keys = ['UTIL', 'ATTA', 'FINI', 'CREA', 'CONS', 'DRIB', 'PERC', 'ENGA', 'RECU', 'DEFE', 'ANTI', 'AERI']
    stats_cols = [c for c in ordered_keys if c in df.columns]
    
    roles_cols = [c for c in ['SL', 'BB', 'MN', 'ST', 'RC'] if c in df.columns]
    if roles_cols:
        df['Rôle Majeur'] = df[roles_cols].idxmin(axis=1)
    else:
        df['Rôle Majeur'] = "Non défini"
        
    # Calcul des centiles et de la note moyenne basée sur les catégories présentes
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
    st.error(f"Erreur lors du chargement du fichier MILIEUX.ods : {e}")
    st.stop()

# Code couleur pour l'affichage des centiles
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

# 1. ENGLONGLET : BASE DE DONNÉES
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
    
    # Renommer proprement les colonnes avec leur nom complet
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

# 2. ENGLONGLET : PROFIL JOUEUR
with tab2:
    st.subheader("👤 Fiche d'identité & Profil du Joueur")
    player_list = filtered_df[player_col].unique() if player_col in filtered_df.columns else []
    
    if len(player_list) > 0:
        selected_player = st.selectbox("Choisir un joueur", player_list)
        p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
        
        p_club = p_data['Équipe'] if 'Équipe' in p_data else "Non défini"
        p_role = p_data['Rôle Majeur'] if 'Rôle Majeur' in p_data else "Milieu"
        p_note = p_data['Note_Moyenne_Stats']
        p_age = p_data[age_col]
        
        p_taille = p_data['Taille'] if 'Taille' in p_data else "1m80"
        p_valeur = p_data['Valeur'] if 'Valeur' in p_data else "-"
        p_saison = "2025/2026"
        
        id_col1, id_col2 = st.columns([1.2, 2])
        
        with id_col1:
            st.markdown(f"""
                <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; text-align: center;'>
                    <div style='width: 100px; height: 100px; border-radius: 50%; background-color: #0d1117; border: 2px solid #00BFFF; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto;'>
                        <span style='font-size: 50px;'>🏃‍♂️</span>
                    </div>
                    <div style='font-size: 22px; font-weight: bold; color: #ffffff;'>{str(p_data[player_col]).upper()}</div>
                    <div style='font-size: 15px; font-weight: bold; color: #FF4D4D; margin: 5px 0 15px 0;'>⚽ {p_club}</div>
                    <span style='background-color: #0d1117; border: 1px solid #30363d; padding: 6px 12px; border-radius: 20px; font-size: 13px; color: #4CD964; font-weight: bold;'>{p_role}</span>
                </div>
            """, unsafe_allow_html=True)
            
        with id_col2:
            st.markdown(f"""
                <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; height: 100%;'>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                        <div>
                            <div style='font-size: 11px; color: #8b949e; text-transform: uppercase;'>Âge</div>
                            <div style='font-size: 18px; font-weight: bold; color: #ffffff;'>🎂 {p_age} ans</div>
                        </div>
                        <div>
                            <div style='font-size: 11px; color: #8b949e; text-transform: uppercase;'>Note Moyenne</div>
                            <div style='font-size: 18px; font-weight: bold; color: #ffffff;'>📈 {p_note} / 100</div>
                        </div>
                        <div>
                            <div style='font-size: 11px; color: #8b949e; text-transform: uppercase;'>Taille</div>
                            <div style='font-size: 18px; font-weight: bold; color: #ffffff;'>📏 {p_taille}</div>
                        </div>
                        <div>
                            <div style='font-size: 11px; color: #8b949e; text-transform: uppercase;'>Saison</div>
                            <div style='font-size: 18px; font-weight: bold; color: #ffffff;'>⏳ {p_saison}</div>
                        </div>
                        <div style='grid-column: span 2; border-top: 1px solid #30363d; padding-top: 10px;'>
                            <div style='font-size: 11px; color: #8b949e; text-transform: uppercase;'>Valeur Marchande</div>
                            <div style='font-size: 18px; font-weight: bold; color: #ffffff;'>💰 {p_valeur}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("### 📊 Centiles par caractéristique")
        
        stat_col1, stat_col2 = st.columns(2)
        half = len(stats_cols) // 2 + (1 if len(stats_cols) % 2 != 0 else 0)
        
        for idx, c in enumerate(stats_cols):
            c_centile = f'{c} (Centile)'
            if c_centile in p_data:
                val = p_data[c_centile]
                color = get_colors(val)
                label_clean = stats_mapping.get(c, c)
                
                target_col = stat_col1 if idx < half else stat_col2
                
                with target_col:
                    st.markdown(f"""
                        <div style='background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;'>
                            <div style='font-weight: bold; color: #ffffff; font-size: 14px;'>{label_clean}</div>
                            <div style='background-color: #0d1117; border: 2px solid {color}; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 16px; color: {color} !important;'>
                                {val}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.write("Aucun joueur disponible.")

# 3. ENGLONGLET : COMPARATEUR
with tab3:
    st.subheader("Comparateur de Cartes")
    all_players = df[player_col].unique() if player_col in df.columns else []
    
    if len(all_players) > 1:
        selected_players = st.multiselect("Sélectionnez les joueurs à comparer (2 à 4)", options=all_players, default=list(all_players[:2]))
        
        if len(selected_players) >= 2:
            st.markdown("<br>", unsafe_allow_html=True)
            
            cols_header = st.columns([2] + [2] * len(selected_players))
            with cols_header[0]:
                st.markdown("""
                    <div style='background-color: #161b22; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #30363d; min-height: 68px; display: flex; flex-direction: column; justify-content: center;'>
                        <div style='font-size: 16px; font-weight: bold; color: #ffffff;'>COMPARAISON</div>
                    </div>
                """, unsafe_allow_html=True)
                
            for idx, p_name in enumerate(selected_players):
                p_club = df[df[player_col] == p_name]['Équipe'].values[0] if 'Équipe' in df.columns else ""
                with cols_header[idx + 1]:
                    st.markdown(f"""
                        <div style='background-color: #161b22; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #30363d; min-height: 68px; display: flex; flex-direction: column; justify-content: center;'>
                            <div style='font-size: 16px; font-weight: bold; color: #ffffff;'>{p_name.upper()}</div>
                            <div style='font-size: 11px; color: #8b949e;'>{p_club}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #30363d; margin: 10px 0;'>", unsafe_allow_html=True)
            
            # Affichage de la Note Moyenne Générale
            cols_note = st.columns([2] + [2] * len(selected_players))
            with cols_note[0]:
                st.markdown("<div style='padding: 12px 0; font-size: 14px; font-weight: bold; color: #00BFFF;'>NOTE MOYENNE</div>", unsafe_allow_html=True)
            for idx, p_name in enumerate(selected_players):
                p_data = df[df[player_col] == p_name].iloc[0]
                val_note = p_data['Note_Moyenne_Stats']
                color_note = get_colors(val_note)
                with cols_note[idx + 1]:
                    st.markdown(f"""
                        <div style='display: flex; justify-content: center; align-items: center; padding: 4px 0;'>
                            <div style='background-color: #0d1117; border: 2px solid {color_note}; padding: 6px 0; border-radius: 6px; width: 65px; text-align: center; font-weight: bold; font-size: 16px; color: {color_note} !important;'>
                                {val_note}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
            st.markdown("<hr style='border-color: #30363d; opacity: 0.5; margin: 10px 0;'>", unsafe_allow_html=True)
            
            # Affichage de toutes les autres catégories (sans centres)
            for c in stats_cols:
                cols_data = st.columns([2] + [2] * len(selected_players))
                label_clean = stats_mapping.get(c, c)
                
                with cols_data[0]:
                    st.markdown(f"""
                        <div style='padding: 12px 0;'>
                            <div style='font-size: 14px; font-weight: bold; color: #e6edf2;'>{label_clean}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                for idx, p_name in enumerate(selected_players):
                    p_data = df[df[player_col] == p_name].iloc[0]
                    val = p_data[f'{c} (Centile)']
                    color = get_colors(val)
                    
                    with cols_data[idx + 1]:
                        st.markdown(f"""
                            <div style='display: flex; justify-content: center; align-items: center; padding: 4px 0;'>
                                <div style='background-color: #0d1117; border: 2px solid {color}; padding: 6px 0; border-radius: 6px; width: 65px; text-align: center; font-weight: bold; font-size: 16px; color: {color} !important;'>
                                    {val}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("Veuillez sélectionner au moins 2 joueurs.")
    else:
        st.write("Pas assez de données pour faire une comparaison.")
