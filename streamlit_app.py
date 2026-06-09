import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux de Terrain", layout="wide")

# Injection CSS globale et script de tri par clic direct (Sortable)
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/sorts/tablesort.number.min.js"></script>

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
        
        /* Styles pour la table personnalisée style FMInside */
        .fm-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Source Sans Pro', sans-serif;
            margin-top: 15px;
        }
        .fm-th {
            color: #8b949e;
            text-transform: uppercase;
            font-size: 11px;
            font-weight: 600;
            padding: 12px 10px;
            text-align: center;
            border-bottom: 2px solid #30363d;
            cursor: pointer;
            user-select: none;
        }
        .fm-th:hover {
            color: #ffffff;
            background-color: #21262d;
        }
        .fm-th-left {
            text-align: left;
        }
        
        /* Flèches indicatrices de tri */
        .fm-th[aria-sort="ascending"]::after {
            content: " ▲";
            font-size: 9px;
            color: #00BFFF;
        }
        .fm-th[aria-sort="descending"]::after {
            content: " ▼";
            font-size: 9px;
            color: #00BFFF;
        }

        .fm-tr {
            background-color: #161b22;
            border-bottom: 1px solid #21262d;
            transition: background-color 0.2s;
        }
        .fm-tr:hover {
            background-color: #1f242c;
        }
        .fm-td {
            padding: 12px 10px;
            vertical-align: middle;
            text-align: center;
            color: #c9d1d9;
            font-size: 14px;
        }
        .fm-td-left {
            text-align: left;
        }
        .fm-player-cell {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .fm-avatar {
            width: 32px;
            height: 32px;
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }
        .fm-player-name {
            font-weight: bold;
            color: #ffffff;
        }
        .fm-player-club {
            font-size: 11px;
            color: #8b949e;
        }
        .fm-badge {
            display: inline-block;
            font-weight: bold;
            font-size: 13px;
            padding: 4px 0;
            width: 36px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
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
    st.error(f"Erreur lors du chargement du fichier MILIEUX.ods : {e}")
    st.stop()

# Code couleur
def get_colors(val):
    try:
        val = float(val)
        if 0 <= val < 11: return '#8A2BE2', '#ffffff'        
        elif 11 <= val < 30: return '#FF4D4D', '#ffffff'    
        elif 30 <= val < 50: return '#D35400', '#ffffff'    
        elif 50 <= val < 70: return '#FFFF4D', '#0d1117'    
        elif 70 <= val < 90: return '#4CD964', '#0d1117'    
        elif 90 <= val <= 100: return '#00BFFF', '#0d1117'  
    except:
        pass
    return '#444444', '#ffffff'

# --- INTERFACE UTILISATEUR ---
st.title("⚽ Dashboard de Scouting - Milieux de Terrain")

st.sidebar.header("Filtres de Recherche")
try:
    df[age_col] = pd.to_numeric(df[age_col], errors='coerce').fillna(20).astype(int)
    age_min, age_max = int(df[df[age_col] > 0][age_col].min()), int(df[age_col].max())
    selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))
    filtered_df = df[(df[age_col] >= selected_age[0]) & (df[age_col] <= selected_age[1])]
except:
    filtered_df = df.copy()

display_df = filtered_df.sort_values(by='Note_Moyenne_Stats', ascending=False)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur", "📈 Analyse Graphique"])

with tab1:
    st.subheader("Base globale des joueurs")
    st.caption("💡 Cliquez sur le nom d'une colonne pour trier directement la liste.")
    
    if len(display_df) > 0:
        html_table = "<table class='fm-table' id='fmin-table'>"
        html_table += "<thead><tr>"
        html_table += "<th class='fm-th fm-th-left'>Joueur / Club</th>"
        html_table += "<th class='fm-th'>Âge</th>"
        html_table += "<th class='fm-th'>Note Moyenne</th>"
        
        for c in stats_cols:
            html_table += f"<th class='fm-th'>{stats_mapping[c]}</th>"
        html_table += "</tr></thead><tbody>"
        
        for _, row in display_df.iterrows():
            p_name = str(row[player_col]).upper()
            p_age = row[age_col]
            p_club = row['Équipe'] if 'Équipe' in row and pd.notna(row['Équipe']) else "Sans club"
            p_note = row['Note_Moyenne_Stats']
            
            bg_note, text_note = get_colors(p_note)
            
            html_table += "<tr class='fm-tr'>"
            html_table += f"""
            <td class='fm-td fm-td-left' data-sort='{p_name}'>
                <div class='fm-player-cell'>
                    <div class='fm-avatar'>🏃‍♂️</div>
                    <div>
                        <div class='fm-player-name'>{p_name}</div>
                        <div class='fm-player-club'>⚽ {p_club}</div>
                    </div>
                </div>
            </td>
            """
            html_table += f"<td class='fm-td' style='font-weight: 500;'>{p_age}</td>"
            html_table += f"<td class='fm-td' data-sort='{p_note}'><span class='fm-badge' style='background-color: {bg_note}; color: {text_note}; width: 45px; font-size: 14px;'>{p_note}</span></td>"
            
            for c in stats_cols:
                val = row[f"{c} (Centile)"]
                bg_c, text_c = get_colors(val)
                html_table += f"<td class='fm-td' data-sort='{val}'><span class='fm-badge' style='background-color: {bg_c}; color: {text_c};'>{val}</span></td>"
                
            html_table += "</tr>"
            
        html_table += "</tbody></table>"
        
        js_script = """
        <script>
            setTimeout(function() {
                new Tablesort(document.getElementById('fmin-table'), {
                    descending: true
                });
            }, 500);
        </script>
        """
        
        st.markdown(html_table + js_script, unsafe_allow_html=True)
    else:
        st.warning("Aucun joueur trouvé avec les filtres sélectionnés.")

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
                color, text_color = get_colors(val)
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

with tab3:
    st.subheader("Comparateur de Cartes")
    all_players = df[player_col].unique() if player_col in df.columns else []
    
    if len(all_players) > 1:
        selected_players = st.multiselect("Sélectionnez les joueurs à comparer (2 à 4)", options=all_players, default=list(all_players[:2]))
        
        if len(selected_players) >= 2:
            st.markdown("<br>", unsafe_allow_html=True)
            
            cols_header = st.columns([2] + [2] * len(selected_players))
            with cols_header[0]:
                st.markdown("<div style='background-color: #161b22; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #30363d; min-height: 68px; display: flex; flex-direction: column; justify-content: center;'><div style='font-size: 16px; font-weight: bold; color: #ffffff;'>COMPARAISON</div></div>", unsafe_allow_html=True)
                
            for idx, p_name in enumerate(selected_players):
                p_club = df[df[player_col] == p_name]['Équipe'].values[0] if 'Équipe' in df.columns else ""
                with cols_header[idx + 1]:
                    st.markdown(f"<div style='background-color: #161b22; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #30363d; min-height: 68px; display: flex; flex-direction: column; justify-content: center;'><div style='font-size: 16px; font-weight: bold; color: #ffffff;'>{p_name.upper()}</div><div style='font-size: 11px; color: #8b949e;'>{p_club}</div></div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #30363d; margin: 10px 0;'>", unsafe_allow_html=True)
            
            cols_note = st.columns([2] + [2] * len(selected_players))
            with cols_note[0]:
                st.markdown("<div style='padding: 12px 0; font-size: 14px; font-weight: bold; color: #00BFFF;'>NOTE MOYENNE</div>", unsafe_allow_html=True)
            for idx, p_name in enumerate(selected_players):
                p_data = df[df[player_col] == p_name].iloc[0]
                val_note = p_data['Note_Moyenne_Stats']
                color_note, _ = get_colors(val_note)
                with cols_note[idx + 1]:
                    st.markdown(f"<div style='display: flex; justify-content: center; align-items: center; padding: 4px 0;'><div style='background-color: #0d1117; border: 2px solid {color_note}; padding: 6px 0; border-radius: 6px; width: 65px; text-align: center; font-weight: bold; font-size: 16px; color: {color_note} !important;'>{val_note}</div></div>", unsafe_allow_html=True)
                    
            st.markdown("<hr style='border-color: #30363d; opacity: 0.5; margin: 10px 0;'>", unsafe_allow_html=True)
            
            for c in stats_cols:
                cols_data = st.columns([2] + [2] * len(selected_players))
                label_clean = stats_mapping.get(c, c)
                
                with cols_data[0]:
                    st.markdown(f"<div style='padding: 12px 0;'><div style='font-size: 14px; font-weight: bold; color: #e6edf2;'>{label_clean}</div></div>", unsafe_allow_html=True)
                
                for idx, p_name in enumerate(selected_players):
                    p_data = df[df[player_col] == p_name].iloc[0]
                    val = p_data[f'{c} (Centile)']
                    color, _ = get_colors(val)
                    with cols_data[idx + 1]:
                        st.markdown(f"<div style='display: flex; justify-content: center; align-items: center; padding: 4px 0;'><div style='background-color: #0d1117; border: 2px solid {color}; padding: 6px 0; border-radius: 6px; width: 65px; text-align: center; font-weight: bold; font-size: 16px; color: {color} !important;'>{val}</div></div>", unsafe_allow_html=True)
        else:
            st.warning("Veuillez sélectionner au moins 2 joueurs.")

with tab4:
    st.subheader("📈 Nuage de Points Interactif - Analyse à 2 axes")
    
    reverse_mapping = {v: k for k, v in stats_mapping.items()}
    options_labels = list(stats_mapping.values())
    
    graph_col1, graph_col2 = st.columns(2)
    with graph_col1:
        x_label = st.selectbox("Axe X (Horizontal)", options_labels, index=3)
    with graph_col2:
        y_label = st.selectbox("Axe Y (Vertical)", options_labels, index=4)
        
    x_col = f"{reverse_mapping[x_label]} (Centile)"
    y_col = f"{reverse_mapping[y_label]} (Centile)"
    
    if len(filtered_df) > 0:
        plot_df = filtered_df.copy()
        plot_df['Équipe_Label'] = plot_df['Équipe'] if 'Équipe' in plot_df.columns else "Non définie"
        
        fig = px.scatter(
            plot_df, x=x_col, y=y_col, text=player_col, color='Note_Moyenne_Stats',
            color_continuous_scale='Turbo', labels={x_col: x_label, y_col: y_label, 'Note_Moyenne_Stats': 'Note Moyenne'},
            hover_name=player_col, hover_data={x_col: True, y_col: True, 'Note_Moyenne_Stats': ':.1f', 'Équipe_Label': True, 'Rôle Majeur': True, 'Âge': True}
        )
        fig.update_traces(textposition='top center', marker=dict(size=12, opacity=0.85, line=dict(width=1, color='White')))
        fig.update_layout(
            plot_bgcolor='#161b22', paper_bgcolor='#0d1117', font_color='#ffffff',
            xaxis=dict(gridcolor='#30363d', zerolinecolor='#30363d', range=[-5, 105]),
            yaxis=dict(gridcolor='#30363d', zerolinecolor='#30363d', range=[-5, 105]),
            height=650, margin=dict(l=40, r=40, t=20, b=40)
        )
        fig.add_shape(type="line", x0=50, y0=-5, x1=50, y1=105, line=dict(color="#8b949e", width=1, dash="dash"))
        fig.add_shape(type="line", x0=-5, y0=50, x1=105, y1=50, line=dict(color="#8b949e", width=1, dash="dash"))
        
        st.plotly_chart(fig, use_container_width=True)
