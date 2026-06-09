import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FM Scouting Pro - Milieux", layout="wide", initial_sidebar_state="expanded")

# --- INJECTION CSS & JAVASCRIPT STYLE FOOTBALL MANAGER (NEW GEN) ---
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/sorts/tablesort.number.min.js"></script>

    <style>
        /* Thème sombre Premium */
        .stApp {
            background-color: #0c1017 !important;
            color: #e6edf2 !important;
            font-family: 'Inter', sans-serif;
        }
        
        /* Personnalisation de la barre latérale */
        section[data-testid="stSidebar"] {
            background-color: #151b23 !important;
            border-right: 1px solid #30363d !important;
        }
        
        /* Onglets style FM */
        .stTabs [data-baseweb="tab"] {
            color: #8b949e !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            padding: 12px 20px !important;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #00f0ff !important;
            border-bottom-color: #00f0ff !important;
            background-color: #151b23 !important;
            border-radius: 6px 6px 0 0;
        }

        /* Table de données immersive */
        .fm-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 15px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #30363d;
        }
        .fm-th {
            background-color: #151b23;
            color: #8b949e;
            text-transform: uppercase;
            font-size: 11px;
            font-weight: 700;
            padding: 14px 10px;
            text-align: center;
            border-bottom: 2px solid #30363d;
            cursor: pointer;
            user-select: none;
        }
        .fm-th:hover {
            color: #ffffff;
            background-color: #21262d;
        }
        .fm-th-left { text-align: left; padding-left: 15px; }
        
        .fm-tr {
            background-color: #0c1017;
            transition: background-color 0.15s ease;
        }
        .fm-tr:hover {
            background-color: #1c212c;
        }
        .fm-td {
            padding: 12px 10px;
            vertical-align: middle;
            text-align: center;
            color: #c9d1d9;
            font-size: 14px;
            border-bottom: 1px solid #21262d;
        }
        .fm-td-left { text-align: left; padding-left: 15px; }

        /* Flèches de tri */
        .fm-th[aria-sort="ascending"]::after { content: " ▲"; color: #00f0ff; font-size: 10px; }
        .fm-th[aria-sort="descending"]::after { content: " ▼"; color: #00f0ff; font-size: 10px; }

        /* Badges de Notes Dynamiques */
        .fm-badge {
            display: inline-block;
            font-weight: 700;
            font-size: 13px;
            padding: 5px 0;
            width: 40px;
            border-radius: 6px;
            text-align: center;
            color: #ffffff !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Conteneurs de fiches joueur */
        .player-card-bg {
            background-color: #151b23;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 25px;
        }
    </style>
""", unsafe_allow_html=True)


# --- 1. CHARGEMENT ET TRAITEMENT DES DONNÉES ---
@st.cache_data
def load_and_process_data():
    # Chargement du fichier
    df = pd.read_excel("MILIEUX.ods")
    df.columns = [str(c).strip() for c in df.columns]
    
    # Nettoyage et affectation de la colonne Âge (colonne A)
    df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    df["Âge"] = pd.to_numeric(df["Âge"], errors='coerce').fillna(22).astype(int)
    
    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    
    # Configuration des Rôles (la note la plus basse = son rôle majeur)
    roles_mapping = {
        'SL': 'Seconde Lame',
        'BB': 'Box to Box',
        'MN': 'Meneur',
        'ST': 'Sentinelle',
        'RC': 'Récupérateur'
    }
    actual_role_cols = [c for c in roles_mapping.keys() if c in df.columns]
    
    if actual_role_cols:
        for r_col in actual_role_cols:
            df[r_col] = pd.to_numeric(df[r_col], errors='coerce').fillna(999)
        # Trouve la colonne avec la valeur minimale pour chaque ligne
        df['Rôle Majeur'] = df[actual_role_cols].idxmin(axis=1).map(roles_mapping)
    else:
        df['Rôle Majeur'] = "Milieu"

    # Lexique des caractéristiques (en excluant volontairement 'CENT')
    stats_mapping = {
        'UTIL': 'Utilisation', 'ATTA': 'Attaque', 'FINI': 'Finition', 
        'CREA': 'Création', 'CONS': 'Construction', 'DRIB': 'Dribble', 
        'PERC': 'Percussion', 'ENGA': 'Engagement', 'RECU': 'Récupération', 
        'DEFE': 'Un contre un', 'ANTI': 'Anticipation', 'AERI': 'Aérien'
    }
    stats_cols = [c for c in stats_mapping.keys() if c in df.columns]
    
    # Conversion en Centiles (0 à 100). Formule : Rangs inversés car la note la plus basse est la meilleure.
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].max() + 1)
        df[f'{col} (Centile)'] = (df[col].rank(ascending=False, pct=True) * 100).round().astype(int)
        
    # Calcul de la Note Moyenne Générale basée sur les nouveaux centiles calculés
    centile_cols_generated = [f'{col} (Centile)' for col in stats_cols]
    if centile_cols_generated:
        df['Note_Moyenne_Stats'] = df[centile_cols_generated].mean(axis=1).round(1)
    else:
        df['Note_Moyenne_Stats'] = 0
        
    return df, player_col, stats_cols, stats_mapping


try:
    df, player_col, stats_cols, stats_mapping = load_and_process_data()
except Exception as e:
    st.error(f"Impossible de charger ou traiter le fichier 'MILIEUX.ods' : {e}")
    st.stop()


# --- FONCTION COULEURS PROFESSIONNELLES (STYLE DEGRADE FM) ---
def get_fm_color(val):
    try:
        val = float(val)
        if 80 <= val <= 100: return '#00f0ff'  # Elite - Cyan Éclatant
        elif 65 <= val < 80: return '#00ff66'  # Excellent - Vert Fluo
        elif 50 <= val < 65: return '#ffcc00'  # Bon - Jaune Or
        elif 30 <= val < 50: return '#ff6600'  # Moyen - Orange
        else: return '#4a5568'                 # Faible - Gris Foncé
    except:
        return '#4a5568'


# --- INTERFACE UTILISATEUR SIDEBAR (FILTRES AVANCÉS) ---
st.sidebar.markdown("<h2 style='color:#00f0ff; margin-bottom:0;'>⚽ FM SCOUTING</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#8b949e; font-size:12px; margin-top:0;'>Filtres de recrutement avancés</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Recherche textuelle directe
search_query = st.sidebar.text_input("🔍 Rechercher un joueur", "").strip().lower()

# Curseur d'âge dynamique
age_min, age_max = int(df["Âge"].min()), int(df["Âge"].max())
selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))

# Sélections multiples (Clubs & Rôles)
available_clubs = sorted(df['Équipe'].dropna().unique()) if 'Équipe' in df.columns else []
selected_clubs = st.sidebar.multiselect("Clubs / Équipes", options=available_clubs)

available_roles = sorted(df['Rôle Majeur'].dropna().unique())
selected_roles = st.sidebar.multiselect("Rôles Majeurs tactiques", options=available_roles)

# Application globale des filtres
filtered_df = df[(df["Âge"] >= selected_age[0]) & (df["Âge"] <= selected_age[1])]
if search_query:
    filtered_df = filtered_df[filtered_df[player_col].str.lower().str.contains(search_query, na=False)]
if selected_clubs:
    filtered_df = filtered_df[filtered_df['Équipe'].isin(selected_clubs)]
if selected_roles:
    filtered_df = filtered_df[filtered_df['Rôle Majeur'].isin(selected_roles)]

display_df = filtered_df.sort_values(by='Note_Moyenne_Stats', ascending=False)


# --- DESIGN PRINCIPAL ET ONGLETS ---
st.title("📊 Dashboard de Scouting Premium")
st.markdown(f"**{len(display_df)}** milieux de terrain correspondent à vos critères actuels.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Base Globale", 
    "👤 Fiche Profil Individuelle", 
    "⚔️ Comparateur Face-à-Face", 
    "📈 Analyse Quadrant"
])


# --- ONGLET 1 : BASE GLOBALE ---
with tab1:
    st.subheader("Base de Données des Joueurs (Notes en Centiles)")
    st.caption("💡 Cliquez sur l'en-tête de n'importe quelle colonne pour trier instantanément la liste.")
    
    if len(display_df) > 0:
        html_table = "<table class='fm-table' id='fmin-table'>"
        html_table += "<thead><tr>"
        html_table += "<th class='fm-th fm-th-left'>Joueur / Club</th>"
        html_table += "<th class='fm-th'>Âge</th>"
        html_table += "<th class='fm-th'>Rôle Majeur</th>"
        html_table += "<th class='fm-th'>Général</th>"
        
        for c in stats_cols:
            html_table += f"<th class='fm-th'>{stats_mapping[c]}</th>"
        html_table += "</tr></thead><tbody>"
        
        for _, row in display_df.iterrows():
            p_name = str(row[player_col]).upper()
            p_age = row["Âge"]
            p_club = row['Équipe'] if 'Équipe' in row and pd.notna(row['Équipe']) else "Sans club"
            p_role = row['Rôle Majeur']
            p_note = row['Note_Moyenne_Stats']
            
            c_note = get_fm_color(p_note)
            
            html_table += "<tr class='fm-tr'>"
            html_table += f"""
            <td class='fm-td fm-td-left' data-sort='{p_name}'>
                <div style='display: flex; align-items: center; gap: 12px;'>
                    <div style='width: 32px; height: 32px; background-color: #151b23; border: 1px solid #30363d; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 15px;'>🏃‍♂️</div>
                    <div>
                        <div style='font-weight: 700; color: #ffffff;'>{p_name}</div>
                        <div style='font-size: 11px; color: #8b949e;'>⚽ {p_club}</div>
                    </div>
                </div>
            </td>
            """
            html_table += f"<td class='fm-td' style='font-weight: 600;'>{p_age}</td>"
            html_table += f"<td class='fm-td'><span style='color:#8b949e; font-size:12px; font-weight:600; background:#151b23; padding:3px 8px; border-radius:4px; border:1px solid #30363d;'>{p_role}</span></td>"
            html_table += f"<td class='fm-td' data-sort='{p_note}'><span class='fm-badge' style='background-color: {c_note};'>{int(round(p_note))}</span></td>"
            
            for c in stats_cols:
                val = row[f"{c} (Centile)"]
                c_val = get_fm_color(val)
                html_table += f"<td class='fm-td' data-sort='{val}'><span class='fm-badge' style='background-color: {c_val};'>{val}</span></td>"
                
            html_table += "</tr>"
            
        html_table += "</tbody></table>"
        
        js_script = """
        <script>
            setTimeout(function() {
                new Tablesort(document.getElementById('fmin-table'), { descending: true });
            }, 300);
        </script>
        """
        st.markdown(html_table + js_script, unsafe_allow_html=True)
    else:
        st.warning("Aucun joueur ne correspond à vos filtres actuels.")


# --- ONGLET 2 : PROFIL INDIVIDUEL ---
with tab2:
    if len(filtered_df) > 0:
        player_list = sorted(filtered_df[player_col].unique())
        selected_player = st.selectbox("🎯 Sélectionner un joueur pour analyser son profil", player_list)
        
        p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Structure de la fiche d'identité
        prof_col1, prof_col2 = st.columns([1.2, 2])
        
        with prof_col1:
            st.markdown(f"""
                <div class='player-card-bg' style='text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='width: 90px; height: 90px; border-radius: 50%; background-color: #0c1017; border: 2px solid #00f0ff; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto;'>
                        <span style='font-size: 45px;'>🏃‍♂️</span>
                    </div>
                    <div style='font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;'>{str(p_data[player_col]).upper()}</div>
                    <div style='font-size: 15px; font-weight: 600; color: #00f0ff; margin: 5px 0 15px 0;'>⚽ {p_data['Équipe'] if pd.notna(p_data['Équipe']) else 'Sans Club'}</div>
                    <div>
                        <span style='background-color: #21262d; border: 1px solid #30363d; padding: 6px 16px; border-radius: 20px; font-size: 13px; color: #00ff66; font-weight: 700; text-transform: uppercase;'>
                            {p_data['Rôle Majeur']}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with prof_col2:
            # Graphique Radar dynamique (Signature Wyscout / FM)
            categories = [stats_mapping[c] for c in stats_cols]
            values = [p_data[f"{c} (Centile)"] for c in stats_cols]
            
            # Fermer la boucle du radar
            categories.append(categories[0])
            values.append(values[0])
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                fillcolor='rgba(0, 240, 255, 0.15)',
                line=dict(color='#00f0ff', width=2),
                name=selected_player
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="#30363d", tickfont=dict(color="#8b949e")),
                    angularaxis=dict(gridcolor="#30363d", tickfont=dict(color="#ffffff", size=11))
                ),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                margin=dict(t=20, b=20, l=40, r=40)
            )
            st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})

        # Affichage en grille moderne des caractéristiques du joueur
        st.markdown("<h4 style='color:#ffffff; margin-top:30px; margin-bottom:15px;'>📊 Détail des Caractéristiques (Score Centile)</h4>", unsafe_allow_html=True)
        
        stat_grid_cols = st.columns(4)
        for idx, c in enumerate(stats_cols):
            val_centile = p_data[f"{c} (Centile)"]
            color_badge = get_fm_color(val_centile)
            label_clean = stats_mapping[c]
            
            target_col = stat_grid_cols[idx % 4]
            with target_col:
                st.markdown(f"""
                    <div style='background-color: #151b23; border: 1px solid #30363d; padding: 12px 15px; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;'>
                        <div style='font-weight: 600; color: #c9d1d9; font-size: 14px;'>{label_clean}</div>
                        <div style='background-color: {color_badge}; padding: 4px 10px; border-radius: 5px; font-weight: 800; font-size: 15px; color: #ffffff;'>
                            {val_centile}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("Aucun joueur trouvé.")


# --- ONGLET 3 : COMPARATEUR ---
with tab3:
    st.subheader("⚔️ Comparateur de Cartes Face-à-Face")
    all_players = sorted(df[player_col].unique())
    
    selected_players = st.multiselect("Choisissez entre 2 et 4 joueurs à comparer side-by-side", options=all_players, default=all_players[:2])
    
    if len(selected_players) >= 2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # En-têtes des joueurs configurés dynamiquement
        cols_header = st.columns([2.5] + [2] * len(selected_players))
        with cols_header[0]:
            st.markdown("<div style='background-color: #151b23; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #30363d; min-height: 75px; display: flex; align-items: center; justify-content: center;'><div style='font-size: 14px; font-weight: 700; color: #8b949e;'>CARACTÉRISTIQUES</div></div>", unsafe_allow_html=True)
            
        for idx, p_name in enumerate(selected_players):
            p_row = df[df[player_col] == p_name].iloc[0]
            p_club = p_row['Équipe'] if pd.notna(p_row['Équipe']) else "Sans club"
            p_role = p_row['Rôle Majeur']
            with cols_header[idx + 1]:
                st.markdown(f"""
                    <div style='background-color: #151b23; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #30363d; min-height: 75px;'>
                        <div style='font-size: 15px; font-weight: 800; color: #ffffff;'>{p_name.upper()}</div>
                        <div style='font-size: 11px; color: #00f0ff; font-weight:600;'>{p_role}</div>
                        <div style='font-size: 10px; color: #8b949e;'>⚽ {p_club}</div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Ligne Note Globale Moyenne
        cols_note = st.columns([2.5] + [2] * len(selected_players))
        with cols_note[0]:
            st.markdown("<div style='padding: 12px 10px; font-size: 13px; font-weight: 700; color: #00f0ff; letter-spacing:0.5px;'>NOTE GLOBALE MOYENNE</div>", unsafe_allow_html=True)
        for idx, p_name in enumerate(selected_players):
            val_note = df[df[player_col] == p_name].iloc[0]['Note_Moyenne_Stats']
            c_note = get_fm_color(val_note)
            with cols_note[idx + 1]:
                st.markdown(f"<div style='display: flex; justify-content: center; padding: 6px 0;'><div style='background-color: {c_note}; padding: 6px 0; border-radius: 6px; width: 55px; text-align: center; font-weight: 800; font-size: 15px; color: white;'>{int(round(val_note))}</div></div>", unsafe_allow_html=True)
                
        st.markdown("<hr style='border-color: #30363d; margin: 10px 0;'>", unsafe_allow_html=True)
        
        # Génération dynamique des lignes de caractéristiques
        for c in stats_cols:
            cols_data = st.columns([2.5] + [2] * len(selected_players))
            label_clean = stats_mapping[c]
            
            with cols_data[0]:
                st.markdown(f"<div style='padding: 10px 10px; font-size: 14px; font-weight: 600; color: #c9d1d9;'>{label_clean}</div>", unsafe_allow_html=True)
            
            for idx, p_name in enumerate(selected_players):
                val = df[df[player_col] == p_name].iloc[0][f'{c} (Centile)']
                c_val = get_fm_color(val)
                with cols_data[idx + 1]:
                    st.markdown(f"<div style='display: flex; justify-content: center; padding: 4px 0;'><div style='background-color: {c_val}; padding: 5px 0; border-radius: 6px; width: 55px; text-align: center; font-weight: 700; font-size: 14px; color: white;'>{val}</div></div>", unsafe_allow_html=True)
    else:
        st.warning("Veuillez sélectionner au moins 2 joueurs pour pouvoir comparer.")


# --- ONGLET 4 : ANALYSE GRAPHIQUE ---
with tab4:
    st.subheader("📈 Graphique d'Analyse à Deux Axes (Cross-Analyse)")
    st.caption("Utile pour trouver des anomalies statistiques ou des pépites sous-cotées.")
    
    # Inversion du dictionnaire pour retrouver la clé brute à partir du label propre
    reverse_mapping = {v: k for k, v in stats_mapping.items()}
    options_labels = list(stats_mapping.values())
    
    graph_col1, graph_col2 = st.columns(2)
    with graph_col1:
        x_label = st.selectbox("Sélectionner l'Axe X (Horizontal)", options_labels, index=4) # Par défaut : Construction
    with graph_col2:
        y_label = st.selectbox("Sélectionner l'Axe Y (Vertical)", options_labels, index=3)  # Par défaut : Création
        
    x_col = f"{reverse_mapping[x_label]} (Centile)"
    y_col = f"{reverse_mapping[y_label]} (Centile)"
    
    if len(filtered_df) > 0:
        plot_df = filtered_df.copy()
        plot_df['Club_Label'] = plot_df['Équipe'].fillna("Sans club")
        
        fig = px.scatter(
            plot_df, x=x_col, y=y_col, text=player_col, color='Note_Moyenne_Stats',
            color_continuous_scale='Viridis', 
            labels={x_col: f"{x_label} (Score Centile)", y_col: f"{y_label} (Score Centile)", 'Note_Moyenne_Stats': 'Note Générale'},
            hover_name=player_col, 
            hover_data={'Âge': True, 'Rôle Majeur': True, 'Club_Label': True, x_col: True, y_col: True, 'Note_Moyenne_Stats': ':.1f'}
        )
        
        fig.update_traces(
            textposition='top center', 
            marker=dict(size=13, opacity=0.9, line=dict(width=1, color='White'))
        )
        
        fig.update_layout(
            plot_bgcolor='#151b23', 
            paper_bgcolor='#0c1017', 
            font_color='#ffffff',
            xaxis=dict(gridcolor='#30363d', zerolinecolor='#30363d', range=[-5, 105]),
            yaxis=dict(gridcolor='#30363d', zerolinecolor='#30363d', range=[-5, 105]),
            height=600, 
            margin=dict(l=40, r=40, t=20, b=40)
        )
        
        # Lignes de démarcation médianes (Moyenne théorique des centiles à 50)
        fig.add_shape(type="line", x0=50, y0=-5, x1=50, y1=105, line=dict(color="#8b949e", width=1, dash="dash"))
        fig.add_shape(type="line", x0=-5, y0=50, x1=105, y1=50, line=dict(color="#8b949e", width=1, dash="dash"))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucun joueur disponible pour générer l'analyse graphique.")
