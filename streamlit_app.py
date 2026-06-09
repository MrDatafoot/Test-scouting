import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FM Scouting Pro - Milieux", layout="wide", initial_sidebar_state="expanded")

# --- INJECTION CSS & STYLE CHROME DARK ---
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/sorts/tablesort.number.min.js"></script>

    <style>
        /* Thème sombre Premium */
        .stApp {
            background-color: #05070a !important;
            color: #e6edf2 !important;
            font-family: 'Inter', Arial, sans-serif;
        }
        
        /* Personnalisation de la barre latérale */
        section[data-testid="stSidebar"] {
            background-color: #0c1017 !important;
            border-right: 1px solid #21262d !important;
        }
        
        /* Onglets style FM */
        .stTabs [data-baseweb="tab"] {
            color: #8b949e !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            padding: 12px 20px !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #00d2ff !important;
            border-bottom-color: #00d2ff !important;
            background-color: #0c1017 !important;
        }

        /* Table de données immersive */
        .fm-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 15px;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid #21262d;
        }
        .fm-th {
            background-color: #0c1017;
            color: #8b949e;
            text-transform: uppercase;
            font-size: 11px;
            font-weight: 700;
            padding: 14px 10px;
            text-align: center;
            border-bottom: 2px solid #21262d;
            cursor: pointer;
        }
        .fm-th:hover { color: #ffffff; background-color: #161b22; }
        .fm-th-left { text-align: left; padding-left: 15px; }
        
        .fm-tr { background-color: #05070a; transition: background-color 0.15s ease; }
        .fm-tr:hover { background-color: #0c1017; }
        
        .fm-td {
            padding: 12px 10px;
            vertical-align: middle;
            text-align: center;
            color: #c9d1d9;
            font-size: 14px;
            border-bottom: 1px solid #161b22;
        }
        .fm-td-left { text-align: left; padding-left: 15px; }

        /* Badges de Notes en Contour */
        .fm-badge {
            display: inline-block;
            font-weight: 700;
            font-size: 13px;
            padding: 4px 0;
            width: 40px;
            border-radius: 4px;
            text-align: center;
            background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)


# --- CHARGEMENT ET TRAITEMENT DES DONNÉES ---
@st.cache_data
def load_and_process_data():
    df = pd.read_excel("MILIEUX.ods")
    df.columns = [str(c).strip() for c in df.columns]
    
    df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    df["Âge"] = pd.to_numeric(df["Âge"], errors='coerce').fillna(22).astype(int)
    
    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    
    roles_mapping = {
        'SL': 'Seconde Lame', 'BB': 'Box to Box', 'MN': 'Meneur', 
        'ST': 'Sentinelle', 'RC': 'Récupérateur'
    }
    actual_role_cols = [c for c in roles_mapping.keys() if c in df.columns]
    
    if actual_role_cols:
        for r_col in actual_role_cols:
            df[r_col] = pd.to_numeric(df[r_col], errors='coerce').fillna(999)
        df['Rôle Majeur'] = df[actual_role_cols].idxmin(axis=1).map(roles_mapping)
    else:
        df['Rôle Majeur'] = "Milieu"

    stats_mapping = {
        'UTIL': 'Utilisation', 'ATTA': 'Attaque', 'FINI': 'Finition', 
        'CREA': 'Création', 'CONS': 'Construction', 'DRIB': 'Dribble', 
        'PERC': 'Percussion', 'ENGA': 'Engagement', 'RECU': 'Récupération', 
        'DEFE': 'Un contre un', 'ANTI': 'Anticipation', 'AERI': 'Aérien'
    }
    stats_cols = [c for c in stats_mapping.keys() if c in df.columns]
    
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].max() + 1)
        df[f'{col} (Centile)'] = (df[col].rank(ascending=False, pct=True) * 100).round().astype(int)
        
    centile_cols_generated = [f'{col} (Centile)' for col in stats_cols]
    if centile_cols_generated:
        df['Note_Moyenne_Stats'] = df[centile_cols_generated].mean(axis=1).round(1)
    else:
        df['Note_Moyenne_Stats'] = 0
        
    return df, player_col, stats_cols, stats_mapping


try:
    df, player_col, stats_cols, stats_mapping = load_and_process_data()
except Exception as e:
    st.error(f"Impossible de charger le fichier : {e}")
    st.stop()


def get_fm_color(val):
    try:
        val = float(val)
        if val >= 90: return '#00d2ff'     # ELITE (Cyan)
        elif val >= 70: return '#00ff66'   # FORT (Vert)
        elif val >= 50: return '#ffd60a'   # CORRECT (Jaune)
        elif val >= 30: return '#ff9f0a'   # FRAGILE (Orange)
        elif val >= 15: return '#ff453a'   # FAIBLE (Rouge)
        else: return '#bf5af2'             # CRITIQUE (Violet)
    except:
        return '#4a5568'


# --- INTERFACE SIDEBAR ---
st.sidebar.markdown("<h2 style='color:#00d2ff; margin-bottom:0;'>⚽ FM SCOUTING</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

search_query = st.sidebar.text_input("🔍 Rechercher un joueur", "").strip().lower()

age_min, age_max = int(df["Âge"].min()), int(df["Âge"].max())
selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))

available_clubs = sorted(df['Équipe'].dropna().unique()) if 'Équipe' in df.columns else []
selected_clubs = st.sidebar.multiselect("Clubs / Équipes", options=available_clubs)

available_roles = sorted(df['Rôle Majeur'].dropna().unique())
selected_roles = st.sidebar.multiselect("Rôles Tactiques", options=available_roles)

filtered_df = df[(df["Âge"] >= selected_age[0]) & (df["Âge"] <= selected_age[1])]
if search_query:
    filtered_df = filtered_df[filtered_df[player_col].str.lower().str.contains(search_query, na=False)]
if selected_clubs:
    filtered_df = filtered_df[filtered_df['Équipe'].isin(selected_clubs)]
if selected_roles:
    filtered_df = filtered_df[filtered_df['Rôle Majeur'].isin(selected_roles)]

display_df = filtered_df.sort_values(by='Note_Moyenne_Stats', ascending=False)


# --- NAVIGATION PRINCIPALE ---
st.title("📊 Dashboard de Scouting Premium")

tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Base Globale", 
    "👤 Fiche Profil Individuelle", 
    "⚔️ Comparateur Face-à-Face", 
    "📈 Analyse Quadrant"
])


# --- ONGLET 1 : BASE GLOBALE ---
with tab1:
    st.subheader("Base de Données des Joueurs (Notes en Centiles)")
    if len(display_df) > 0:
        html_table = "<table class='fm-table' id='fmin-table'><thead><tr>"
        html_table += "<th class='fm-th fm-th-left'>Joueur / Club</th><th class='fm-th'>Âge</th><th class='fm-th'>Rôle</th><th class='fm-th'>Général</th>"
        for c in stats_cols:
            html_table += f"<th class='fm-th'>{stats_mapping[c].upper()}</th>"
        html_table += "</tr></thead><tbody>"
        
        for _, row in display_df.iterrows():
            p_name = str(row[player_col]).upper()
            p_age = row["Âge"]
            p_club = row['Équipe'] if 'Équipe' in row and pd.notna(row['Équipe']) else "Sans club"
            p_role = row['Rôle Majeur']
            p_note = row['Note_Moyenne_Stats']
            c_note = get_fm_color(p_note)
            
            html_table += f"<tr class='fm-tr'><td class='fm-td fm-td-left' data-sort='{p_name}'><div style='display:flex; align-items:center; gap:12px;'><div style='width:30px; height:30px; background:#0c1017; border:1px solid #21262d; border-radius:50%; display:flex; align-items:center; justify-content:center;'>🏃‍♂️</div><div><div style='font-weight:700; color:#fff;'>{p_name}</div><div style='font-size:11px; color:#00d2ff;'>🛡️ {p_club}</div></div></div></td>"
            html_table += f"<td class='fm-td' style='font-weight:600;'>{p_age}</td>"
            html_table += f"<td class='fm-td'><span style='color:#8b949e; font-size:12px; font-weight:600; background:#0c1017; padding:3px 8px; border-radius:4px; border:1px solid #21262d;'>{p_role}</span></td>"
            html_table += f"<td class='fm-td' data-sort='{p_note}'><span class='fm-badge' style='border:2px solid {c_note}; color:{c_note} !important;'>{int(round(p_note))}</span></td>"
            
            for c in stats_cols:
                val = row[f"{c} (Centile)"]
                c_val = get_fm_color(val)
                html_table += f"<td class='fm-td' data-sort='{val}'><span class='fm-badge' style='border:2px solid {c_val}; color:{c_val} !important;'>{val}</span></td>"
            html_table += "</tr>"
        html_table += "</tbody></table>"
        
        st.markdown(html_table + "<script>setTimeout(function(){ new Tablesort(document.getElementById('fmin-table'), {descending:true}); }, 300);</script>", unsafe_allow_html=True)
    else:
        st.warning("Aucun joueur ne correspond aux critères.")


# --- ONGLET 2 : PROFIL INDIVIDUEL ---
with tab2:
    if len(filtered_df) > 0:
        player_list = sorted(filtered_df[player_col].unique())
        selected_player = st.selectbox("🎯 Sélectionner un joueur pour charger sa fiche graphique", player_list)
        
        p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
        
        p_name_upper = str(p_data[player_col]).upper()
        p_club_str = str(p_data['Équipe']).upper() if pd.notna(p_data['Équipe']) else 'SANS CLUB'
        p_role_str = str(p_data['Rôle Majeur']).upper()
        general_note = int(round(p_data['Note_Moyenne_Stats']))
        note_color = get_fm_color(general_note)
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        top_dashboard_html = f"""
<div style="display: grid; grid-template-columns: 1.2fr 1.5fr 1fr; gap: 15px; margin-bottom: 25px;">
<div style="border: 1px solid #21262d; background: #0c1017; padding: 15px; border-radius: 6px; display: flex; gap: 15px; align-items: center;">
<div style="font-size: 40px; background: #05070a; border: 1px solid #21262d; border-radius: 6px; padding: 12px; width: 65px; height: 65px; display: flex; align-items: center; justify-content: center;">🏃‍♂️</div>
<div>
<div style="font-size: 22px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; line-height:1.1;">{p_name_upper}</div>
<div style="color: #ff453a; font-size: 13px; font-weight: 700; margin-top: 4px;">🛡️ {p_club_str}</div>
<div style="color: #00d2ff; font-size: 12px; font-weight: 700; margin-top: 4px; text-transform: uppercase;">⚙️ {p_role_str}</div>
</div>
</div>
<div style="border: 1px solid #21262d; background: #0c1017; padding: 15px; border-radius: 6px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px;">
<div style="color:#8b949e;">🎂 AGE : <span style="color:#fff; font-weight:700;">{p_data['Âge']} ANS</span></div>
<div style="color:#8b949e;">🔍 SOURCE : <span style="color:#fff; font-weight:700;">WYSCOUT</span></div>
<div style="color:#8b949e;">📏 TAILLE : <span style="color:#fff; font-weight:700;">X</span></div>
<div style="color:#8b949e;">⏳ SAISON : <span style="color:#fff; font-weight:700;">2025/2026</span></div>
<div style="color:#8b949e;">🦶 PIED FORT : <span style="color:#fff; font-weight:700;">X</span></div>
<div style="color:#8b949e;">📅 DATE : <span style="color:#fff; font-weight:700;">{current_date_str}</span></div>
</div>
<div style="border: 1px solid #21262d; background: #0c1017; padding: 15px; border-radius: 6px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;">
<div style="font-size: 12px; font-weight: 800; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px;">NOTE GÉNÉRALE</div>
<div style="font-size: 54px; font-weight: 900; color: {note_color}; line-height: 1; text-shadow: 0 0 15px {note_color}40;">{general_note}<span style="font-size: 18px; color: #8b949e; font-weight: 500;">/100</span></div>
</div>
</div>
"""
        st.markdown(top_dashboard_html, unsafe_allow_html=True)
        st.markdown("<h3 style='color:#ffffff; font-size:16px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:15px;'>PERFORMANCES STATISTIQUES</h3>", unsafe_allow_html=True)
        
        # --- CONSTRUCTEUR DU GRAPHIQUE INTEGRÉ ---
        # On insère une colonne vide ("") à l'index 0 de l'axe X pour y projeter la légende
        categories = [""] + [stats_mapping[c].upper().replace(" ", "<br>") for c in stats_cols]
        values = [0] + [int(p_data[f"{c} (Centile)"]) for c in stats_cols]
        colors = ["rgba(0,0,0,0)"] + [get_fm_color(v) for v in values[1:]]
        text_labels = [""] + [str(v) for v in values[1:]]
        
        fig_bars = go.Figure()
        fig_bars.add_trace(go.Bar(
            x=categories, y=values,
            marker=dict(color=colors, line=dict(color='rgba(0,0,0,0)', width=0)),
            text=text_labels, textposition='outside',
            textfont=dict(size=12, color='#ffffff', family='Inter, Arial, sans-serif'),
            hovertemplate="<b>%{x}</b><br>Score Centile: %{y}/100<extra></extra>"
        ))
        
        # Définition des blocs géométriques de la légende un
