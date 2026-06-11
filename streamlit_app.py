import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import math

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="DATA'Foot Scouting", layout="wide", initial_sidebar_state="expanded")

# --- INJECTION CSS & STYLE CHROME DARK ---
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/sorts/tablesort.number.min.js"></script>

    <style>
        .stApp {
            background-color: #05070a !important;
            color: #e6edf2 !important;
            font-family: 'Inter', Arial, sans-serif;
        }
        section[data-testid="stSidebar"] {
            background-color: #0c1017 !important;
            border-right: 1px solid #21262d !important;
        }
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
    df = pd.read_excel("MILIEUX.ods", engine="odf")
    df.columns = [str(c).strip() for c in df.columns]

    # Colonne A = Âge
    df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    df["Âge"] = pd.to_numeric(df["Âge"], errors='coerce').fillna(22).astype(int)

    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    df[player_col] = df[player_col].astype(str).str.upper().str.strip()

    # --- BASE DE DONNÉES DES CLUBS ET DES COMPÉTITIONS ---
    CLUBS_PREMIER_LEAGUE = [c.upper() for c in [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Burnley", "Chelsea", 
        "Crystal Palace", "Everton", "Fulham", "Leeds United", "Liverpool", "Manchester City", 
        "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland", 
        "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers"
    ]]

    CLUBS_LIGUE_1 = [c.upper() for c in [
        "Angers SCO", "Auxerre", "Brest", "Le Havre", "Lens", "Lille", "Lorient", "Metz", 
        "Monaco", "Nantes", "Nice", "Olympique Lyonnais", "Olympique Marseille", "PSG", 
        "Paris", "Rennes", "Strasbourg", "Toulouse"
    ]]

    CLUBS_LIGA = [c.upper() for c in [
        "Athletic Bilbao", "Atlético Madrid", "Barcelona", "Celta de Vigo", "Deportivo Alavés", 
        "Elche", "Espanyol", "Getafe", "Girona", "Levante", "Mallorca", "Osasuna", "Rayo Vallecano", 
        "Real Betis", "Real Madrid", "Real Oviedo", "Real Sociedad", "Sevilla", "Valencia", "Villarreal"
    ]]

    CLUBS_SERIE_A = [c.upper() for c in [
        "Atalanta", "Bologna", "Cagliari", "Como", "Cremonese", "Fiorentina", "Genoa", 
        "Hellas Verona", "Internazionale", "Juventus", "Lazio", "Lecce", "Milan", "Napoli", 
        "Parma", "Pisa", "Roma", "Sassuolo", "Torino", "Udinese"
    ]]

    CLUBS_BUNDESLIGA = [c.upper() for c in [
        "Augsburg", "Bayer Leverkusen", "Bayern München", "Borussia Dortmund", "Borussia M'gladbach", 
        "Eintracht Frankfurt", "Freiburg", "Hamburger SV", "Heidenheim", "Hoffenheim", "Köln", 
        "Mainz 05", "RB Leipzig", "St. Pauli", "Stuttgart", "Union Berlin", "Werder Bremen", "Wolfsburg"
    ]]

    CLUBS_LDC_QUART = [c.upper() for c in [
        "PSG", "Liverpool", "Real Madrid", "Bayern München", "Arsenal", "Atlético Madrid", "Barcelona"
    ]]

    # Détection automatique de l'écriture de la colonne Équipe
    team_col = 'Équipe' if 'Équipe' in df.columns else ('Equipe' if 'Equipe' in df.columns else None)

    def attribuer_championnat(club):
        club_clean = str(club).upper().strip()
        if club_clean in CLUBS_PREMIER_LEAGUE: return "Premier League"
        elif club_clean in CLUBS_LIGUE_1: return "Ligue 1"
        elif club_clean in CLUBS_LIGA: return "La Liga"
        elif club_clean in CLUBS_SERIE_A: return "Serie A"
        elif club_clean in CLUBS_BUNDESLIGA: return "Bundesliga"
        else: return "Autre"

    def verifier_ldc(club):
        club_clean = str(club).upper().strip()
        return club_clean in CLUBS_LDC_QUART

    # Assignation masquée des informations tactiques
    if team_col:
        df['Championnat'] = df[team_col].apply(attribuer_championnat)
        df['LDC_Quart_Etape'] = df[team_col].apply(verifier_ldc)
    else:
        df['Championnat'] = "Autre"
        df['LDC_Quart_Etape'] = False

    # --- RÔLES ---
    roles_mapping = {
        'SL': 'Seconde Lame',
        'BB': 'Box to Box',
        'MN': 'Meneur',
        'ST': 'Sentinelle',
        'RC': 'Récupérateur'
    }
    role_cols = [c for c in roles_mapping.keys() if c in df.columns]

    for col in ['M'] + role_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Rôle majeur = colonne avec la note la plus haute
    df['Role_Code_Majeur'] = df[role_cols].idxmax(axis=1)
    df['Rôle Majeur'] = df['Role_Code_Majeur'].map(roles_mapping)
    df['Role_Valeur_Max'] = df[role_cols].max(axis=1)

    # --- CALCUL DE LA NOTE GÉNÉRALE ---
    N = len(df) 

    # 1. Score M (déjà sur 100, valeur directe)
    df['Score_M'] = df['M']

    # 2. Meilleur rôle (déjà sur 100, valeur directe)
    df['Score_Role'] = df['Role_Valeur_Max']

    # 3. Position globale sur M → convertie sur 100
    df['Rang_Global_M'] = df['M'].rank(ascending=False, method='min')
    df['Score_Rang_Global'] = ((df['Rang_Global_M'] / N) - 1) * -100

    # 4. Position dans le meilleur rôle → convertie sur 100 par rapport au groupe de ce rôle
    df['Score_Rang_Role'] = df.groupby('Role_Code_Majeur')['Role_Valeur_Max'].transform(
        lambda x: ((x.rank(ascending=False, method='min') / len(x)) - 1) * -100
    )

    # 5. Application des valeurs par championnat
    bareme_championnats = {
        "Premier League": 100,
        "La Liga": 95,
        "Serie A": 95,
        "Bundesliga": 94,
        "Ligue 1": 93,
        "Autre": 80
    }
    df['Note_Championnat'] = df['Championnat'].map(bareme_championnats).fillna(80)

    # Note finale = moyenne simple intégrant la note Championnat et la note LDC si présente
    def calculer_Note_Moyenne_Stats(row):
        somme_notes = (
            row['Score_M'] +
            row['Score_Role'] +
            row['Score_Rang_Global'] +
            row['Score_Rang_Role'] +
            row['Note_Championnat']
        )
        
        if row['LDC_Quart_Etape']:
            return round((somme_notes + 97) / 6, 1)
        else:
            return round(somme_notes / 5, 1)

    df['Note_Moyenne_Stats'] = df.apply(calculer_Note_Moyenne_Stats, axis=1)

    # --- STATISTIQUES DE COMPÉTENCES ---
    stats_mapping = {
        'UTIL': 'Utilisation', 'ATTA': 'Attaque', 'FINI': 'Finition',
        'CREA': 'Création', 'CONS': 'Construction', 'DRIB': 'Dribble',
        'PERC': 'Percussion', 'ENGA': 'Engagement', 'RECU': 'Récupération',
        'DEFE': 'Défense', 'ANTI': 'Anticipation', 'AERI': 'Aérien'
    }
    stats_cols = [c for c in stats_mapping.keys() if c in df.columns]

    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[f'{col} (Centile)'] = df[col].round().astype(int)

    return df, player_col, stats_cols, stats_mapping


try:
    df, player_col, stats_cols, stats_mapping = load_and_process_data()
except Exception as e:
    st.error(f"Impossible de charger le fichier ou erreur de calcul : {e}")
    st.stop()


def get_fm_color(val):
    try:
        val = float(val)
        if math.isnan(val): return '#4a5568'
        if val >= 90: return '#00d2ff'     # ELITE (Cyan)
        elif val >= 70: return '#00ff66'   # FORT (Vert)
        elif val >= 50: return '#ffd60a'   # CORRECT (Jaune)
        elif val >= 30: return '#ff9f0a'   # FRAGILE (Orange)
        elif val >= 15: return '#ff453a'   # FAIBLE (Rouge)
        else: return '#bf5af2'             # CRITIQUE (Violet)
    except:
        return '#4a5568'


# --- INTERFACE SIDEBAR ---
st.sidebar.markdown("<h2 style='color:#00d2ff; margin-bottom:0;'>BIENVENUE !</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Filtres généraux
search_query = st.sidebar.text_input("🔍 Rechercher un joueur", "").strip().lower()

age_min, age_max = int(df["Âge"].min()), int(df["Âge"].max())
selected_age = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))

available_clubs = sorted(df['Équipe'].dropna().unique()) if 'Équipe' in df.columns else []
selected_clubs = st.sidebar.multiselect("Clubs / Équipes", options=available_clubs)

available_roles = sorted(df['Rôle Majeur'].dropna().unique())
selected_roles = st.sidebar.multiselect("Rôles Tactiques", options=available_roles)

# --- DIRECTEMENT AFFICHÉ : FILTRES DE COMPÉTENCES AVANCÉS ---
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#00d2ff; font-size:14px; margin-bottom:5px; text-transform:uppercase;'>🎯 Compétences Minimales</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:11px; color:#8b949e; margin-bottom:15px;'>Fixer un seuil requis par domaine :</p>", unsafe_allow_html=True)

min_skills = {}
for c in stats_cols:
    label = stats_mapping[c]
    # Les barres s'affichent directement les unes sous les autres dans la zone de gauche
    min_skills[c] = st.sidebar.slider(f"{label}", 0, 100, 0, step=5)


# --- APPLICATION DES FILTRES ---
filtered_df = df[(df["Âge"] >= selected_age[0]) & (df["Âge"] <= selected_age[1])]

if search_query:
    filtered_df = filtered_df[filtered_df[player_col].str.lower().str.contains(search_query, na=False)]
if selected_clubs:
    filtered_df = filtered_df[filtered_df['Équipe'].isin(selected_clubs)]
if selected_roles:
    filtered_df = filtered_df[filtered_df['Rôle Majeur'].isin(selected_roles)]

# Application dynamique des filtres de compétences minimales
for c in stats_cols:
    val_filtre = min_skills[c]
    if val_filtre > 0:
        filtered_df = filtered_df[filtered_df[f"{c} (Centile)"] >= val_filtre]

display_df = filtered_df.sort_values(by='Note_Moyenne_Stats', ascending=False)


# --- NAVIGATION PRINCIPALE ---
st.title("SCOUTING DTFOOTBALL")

tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Base Globale",
    "👤 Fiche Profil Individuelle",
    "⚔️ Comparateur Face-à-Face",
    "📈 Analyse Quadrant"
])


# --- ONGLET 1 : BASE GLOBALE ---
with tab1:
    st.subheader("Base de Données des Joueurs")
    
    if len(display_df) > 0:
        col_sort1, col_sort2 = st.columns([2, 1])
        with col_sort1:
            sort_options = {"Note Générale": "Note_Moyenne_Stats", "Âge": "Âge"}
            for c in stats_cols:
                sort_options[stats_mapping[c]] = f"{c} (Centile)"
            
            selected_sort_label = st.selectbox("Trier la base par :", list(sort_options.keys()), index=0)
            sort_column = sort_options[selected_sort_label]
            
        with col_sort2:
            sort_order = st.selectbox("Ordre :", ["Décroissant (Max → Min)", "Croissant (Min → Max)"], index=0)
            ascending_order = True if sort_order == "Croissant (Min → Max)" else False

        final_table_df = display_df.sort_values(by=sort_column, ascending=ascending_order)

        # --- GÉNÉRATION DU TABLEAU HTML ---
        html_table = "<table class='fm-table'><thead><tr>"
        html_table += "<th class='fm-th fm-th-left'>Joueur / Club</th><th class='fm-th'>Âge</th><th class='fm-th'>Rôle</th><th class='fm-th'>Général</th>"
        for c in stats_cols:
            html_table += f"<th class='fm-th'>{stats_mapping[c].upper()}</th>"
        html_table += "</tr></thead><tbody>"

        for _, row in final_table_df.iterrows():
            p_name = str(row[player_col]).upper()
            p_age = row["Âge"]
            p_club = row['Équipe'] if 'Équipe' in row and pd.notna(row['Équipe']) else "Sans club"
            p_role = row['Rôle Majeur']
            
            p_note_arrondie = int(round(row['Note_Moyenne_Stats']))
            c_note = get_fm_color(p_note_arrondie)

            html_table += f"<tr class='fm-tr'><td class='fm-td fm-td-left'><div style='display:flex; align-items:center; gap:12px;'><div style='width:30px; height:30px; background:#0c1017; border:1px solid #21262d; border-radius:50%; display:flex; align-items:center; justify-content:center;'>🏃‍♂️</div><div><div style='font-weight:700; color:#fff;'>{p_name}</div><div style='font-size:11px; color:#00d2ff;'>🛡️ {p_club}</div></div></div></td>"
            html_table += f"<td class='fm-td' style='font-weight:600;'>{p_age}</td>"
            html_table += f"<td class='fm-td'><span style='color:#8b949e; font-size:12px; font-weight:600; background:#0c1017; padding:3px 8px; border-radius:4px; border:1px solid #21262d;'>{p_role}</span></td>"
            html_table += f"<td class='fm-td'><span class='fm-badge' style='border:2px solid {c_note}; color:{c_note} !important;'>{p_note_arrondie}</span></td>"

            for c in stats_cols:
                val = row[f"{c} (Centile)"]
                c_val = get_fm_color(val)
                html_table += f"<td class='fm-td'><span class='fm-badge' style='border:2px solid {c_val}; color:{c_val} !important;'>{val}</span></td>"
            html_table += "</tr>"
        html_table += "</tbody></table>"

        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.warning("Aucun joueur ne correspond aux critères filtrés.")


# --- ONGLET 2 : PROFIL INDIVIDUEL ---
with tab2:
    if len(filtered_df) > 0:
        player_list = sorted(filtered_df[player_col].unique())
        selected_player = st.selectbox("Choisissez un joueur", player_list)

        p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]

        pied_fort = "DROIT"
        valeur_marchande = "N/A"
        taille_joueur = "1M80"

        p_fullname = str(p_data[player_col]).upper()
        if ' ' in p_fullname:
            nom_joueur = p_fullname.split()[0]
            nom_famille = p_fullname.replace(nom_joueur, "").strip()
        else:
            nom_joueur = p_fullname
            nom_famille = ""

        p_club_str = str(p_data['Équipe']).upper() if pd.notna(p_data['Équipe']) else 'SANS CLUB'
        p_role_str = str(p_data['Rôle Majeur']).upper()
        p_age = f"{int(p_data['Âge'])} ANS"
        
        general_note = int(round(float(p_data['Note_Moyenne_Stats'])))
        note_color = get_fm_color(general_note)
        current_date_str = datetime.now().strftime("%d/%m/%Y")

        st.markdown("""
        <style>
            .dt-card {
                background-color: #0c1017;
                border: 1px solid #21262d;
                border-radius: 6px;
                padding: 20px;
                height: 220px;
                display: flex;
                color: #e6edf2;
            }
            .profile-box { justify-content: flex-start; align-items: center; gap: 20px; }
            .data-box { flex-direction: column; justify-content: space-between; font-size: 13px; }
            .rating-box { flex-direction: column; justify-content: center; align-items: center; text-align: center; }
            
            .data-item { display: flex; align-items: center; gap: 10px; width: 48%; }
            .data-text { display: flex; flex-direction: column; }
            .data-val { font-weight: 700; color: #ffffff; text-transform: uppercase; }
            .data-lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; font-weight: 600; }
            
            .rating-big { font-size: 70px; font-weight: 900; line-height: 1; font-family: 'Arial Black', sans-serif; }
            .rating-max { font-size: 20px; color: #8b949e; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1.2, 1.5, 1])

        with col1:
            html_bloc1 = f"""
            <div class="dt-card profile-box">
                <div style="font-size: 40px; background: #05070a; border: 1px solid #21262d; border-radius: 6px; width: 75px; height: 95px; display: flex; align-items: center; justify-content: center;">👤</div>
                <div>
                    <div style="font-size: 16px; color: #8b949e; font-weight: 700; line-height: 1; text-transform: uppercase;">{nom_joueur}</div>
                    <div style="font-size: 24px; color: #ffffff; font-weight: 900; line-height: 1.1; margin-bottom: 8px; text-transform: uppercase;">{nom_famille if nom_famille else ' '}</div>
                    <div style="color: #ff453a; font-size: 13px; font-weight: 700; margin-bottom: 2px;">🛡️ {p_club_str}</div>
                    <div style="color: {note_color}; font-size: 12px; font-weight: 700; text-transform: uppercase;">🟢 RÔLE : {p_role_str}</div>
                </div>
            </div>
            """
            st.markdown(html_bloc1, unsafe_allow_html=True)

        with col2:
            html_bloc2 = f"""
            <div class="dt-card data-box">
                <div style="display: flex; justify-content: space-between; width: 100%;">
                    <div class="data-item">🎂 <div class="data-text"><span class="data-val">{p_age}</span><span class="data-lbl">Age</span></div></div>
                    <div class="data-item">⚙️ <div class="data-text"><span class="data-val">DTFOOTBALL</span><span class="data-lbl">Création & Calculs</span></div></div>
                </div>
                <div style="display: flex; justify-content: space-between; width: 100%;">
                    <div class="data-item">📏 <div class="data-text"><span class="data-val">{taille_joueur}</span><span class="data-lbl">Taille</span></div></div>
                    <div class="data-item">ℹ️ <div class="data-text"><span class="data-val">WYSCOUT</span><span class="data-lbl">Source</span></div></div>
                </div>
                <div style="display: flex; justify-content: space-between; width: 100%;">
                    <div class="data-item">👣 <div class="data-text"><span class="data-val">{pied_fort}</span><span class="data-lbl">Pied Fort</span></div></div>
                    <div class="data-item">⏳ <div class="data-text"><span class="data-val">2025/2026</span><span class="data-lbl">Saison</span></div></div>
                </div>
                <div style="display: flex; justify-content: space-between; width: 100%;">
                    <div class="data-item">€ <div class="data-text"><span class="data-val">{valeur_marchande}</span><span class="data-lbl">Valeur Marchande</span></div></div>
                    <div class="data-item">📅 <div class="data-text"><span class="data-val">{current_date_str}</span><span class="data-lbl">Date du Post</span></div></div>
                </div>
            </div>
            """
            st.markdown(html_bloc2, unsafe_allow_html=True)

        with col3:
            html_bloc3 = f"""
            <div class="dt-card rating-box">
                <div style="font-size: 12px; font-weight: 800; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">NOTE GÉNÉRALE</div>
                <div>
                    <span class="rating-big" style="color: {note_color}; text-shadow: 0 0 20px {note_color}30;">{general_note}</span>
                    <span class="rating-max">/100</span>
                </div>
            </div>
            """
            st.markdown(html_bloc3, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#ffffff; font-size:16px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:15px;'>PERFORMANCES STATISTIQUES</h3>", unsafe_allow_html=True)
        
        categories = [stats_mapping[c].upper().replace(" ", "<br>") if stats_mapping[c] != 'Défense' else "DÉFENSE" for c in stats_cols]

        values = []
        for c in stats_cols:
            raw_val = p_data.get(f"{c} (Centile)", 0)
            values.append(int(float(raw_val)) if pd.notna(raw_val) else 0)

        colors = [get_fm_color(v) for v in values]

        fig_bars = go.Figure()
        fig_bars.add_trace(go.Bar(
            x=categories, y=values,
            marker=dict(color=colors, line=dict(width=0)),
            text=None,
            hovertemplate="<b>%{x}</b><br>Score: %{y}/100<extra></extra>"
        ))

        for idx, cat_name in enumerate(categories):
            val_score = values[idx]
            col_score = colors[idx]
            fig_bars.add_annotation(
                x=cat_name, y=val_score,
                text=str(val_score),
                showarrow=False,
                yshift=10,
                font=dict(size=12, color=col_score, family='Inter, Arial, sans-serif', weight='bold')
            )

        tiers = [
            {"y0": 90, "y1": 100, "y_text": 95, "title": "ELITE", "sub": "", "color": "#00d2ff"},
            {"y0": 70, "y1": 90, "y_text": 80, "title": "FORT", "sub": "SUR LA MOYENNE", "color": "#00ff66"},
            {"y0": 50, "y1": 70, "y_text": 60, "title": "CORRECT", "sub": "DANS LA MOYENNE", "color": "#ffd60a"},
            {"y0": 30, "y1": 50, "y_text": 40, "title": "FRAGILE", "sub": "SOUS LA MOYENNE", "color": "#ff9f0a"},
            {"y0": 15, "y1": 30, "y_text": 22.5, "title": "FAIBLE", "sub": "À AMÉLIORER", "color": "#ff453a"},
            {"y0": 0, "y1": 15, "y_text": 7.5, "title": "CRITIQUE", "sub": "", "color": "#bf5af2"}
        ]

        for t in tiers:
            if t["y0"] > 0:
                fig_bars.add_shape(
                    type="line", xref="paper", yref="y",
                    x0=0, x1=1, y0=t["y0"], y1=t["y0"],
                    line=dict(color=t["color"], width=1, dash="dot"), layer='below'
                )

            t_html = f"<b style='color:{t['color']}; font-size:11px; font-family:\'Inter\', sans-serif;'>{t['title']}</b>"
            if t["sub"]:
                t_html += f"<br><span style='color:#8b949e; font-size:8px; font-weight:700;'>{t['sub']}</span>"

            fig_bars.add_annotation(
                xref="paper", yref="y",
                x=-0.02, y=float(t["y_text"]),
                text=t_html,
                showarrow=False, xanchor="right", yanchor="middle"
            )

        fig_bars.update_layout(
            plot_bgcolor='#05070a', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=40, l=125, r=20),
            height=630,
            showlegend=False,
            xaxis=dict(
                tickfont=dict(color='#ffffff', size=11, family='Inter, Arial, sans-serif', weight='bold'),
                gridcolor='rgba(0,0,0,0)', fixedrange=True
            ),
            yaxis=dict(
                range=[0, 110], gridcolor='#161b22',
                tickvals=[0, 15, 30, 50, 70, 90, 100],
                tickfont=dict(color='#8b949e', size=10, family='Inter, Arial, sans-serif'),
                fixedrange=True
            )
        )
        st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("Aucun joueur trouvé.")


# --- ONGLET 3 : COMPARATEUR ---
with tab3:
    st.subheader("⚔️ Comparateur de Cartes Face-à-Face")
    all_players = sorted(df[player_col].unique())
    selected_players = st.multiselect("Choisissez les joueurs à comparer side-by-side", options=all_players, default=all_players[:2])

    if len(selected_players) >= 2:
        st.markdown("<br>", unsafe_allow_html=True)
        cols_header = st.columns([2.5] + [2] * len(selected_players))
        with cols_header[0]:
            st.markdown("<div style='background-color:#0c1017; padding:15px; border-radius:6px; text-align:center; border:1px solid #21262d; min-height:75px; display:flex; align-items:center; justify-content:center;'><div style='font-size:12px; font-weight:700; color:#8b949e; text-transform:uppercase;'>CARACTÉRISTIQUES</div></div>", unsafe_allow_html=True)

        for idx, p_name in enumerate(selected_players):
            p_row = df[df[player_col] == p_name].iloc[0]
            p_club = p_row['Équipe'] if pd.notna(p_row['Équipe']) else "Sans club"
            p_role = p_row['Rôle Majeur']
            with cols_header[idx + 1]:
                st.markdown(f"<div style='background-color:#0c1017; padding:10px; border-radius:6px; text-align:center; border:1px solid #21262d; min-height:75px;'><div style='font-size:14px; font-weight:900; color:#fff;'>{p_name.upper()}</div><div style='font-size:11px; color:#00d2ff; font-weight:600;'>{p_role}</div><div style='font-size:10px; color:#8b949e;'>🛡️ {p_club}</div></div>", unsafe_allow_html=True)

        cols_note = st.columns([2.5] + [2] * len(selected_players))
        with cols_note[0]:
            st.markdown("<div style='padding:12px 10px; font-size:12px; font-weight:800; color:#00d2ff; text-transform:uppercase;'>NOTE GENERALE AJUSTÉE</div>", unsafe_allow_html=True)
        for idx, p_name in enumerate(selected_players):
            val_note_brute = df[df[player_col] == p_name].iloc[0]['Note_Moyenne_Stats']
            val_note = int(round(val_note_brute))
            c_note = get_fm_color(val_note)
            with cols_note[idx + 1]:
                st.markdown(f"<div style='display:flex; justify-content:center; padding:6px 0;'><div style='border:2px solid {c_note}; color:{c_note}; padding:4px 0; border-radius:4px; width:44px; text-align:center; font-weight:800; font-size:13px;'>{val_note}</div></div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#21262d; margin:10px 0;'>", unsafe_allow_html=True)

        for c in stats_cols:
            cols_data = st.columns([2.5] + [2] * len(selected_players))
            with cols_data[0]:
                st.markdown(f"<div style='padding:10px 10px; font-size:13px; font-weight:600; color:#c9d1d9;'>{stats_mapping[c].upper()}</div>", unsafe_allow_html=True)
            for idx, p_name in enumerate(selected_players):
                val_raw = df[df[player_col] == p_name].iloc[0][f'{c} (Centile)']
                try:
                    val = int(float(val_raw)) if pd.notna(val_raw) else 0
                except:
                    val = 0
                c_val = get_fm_color(val)
                with cols_data[idx + 1]:
                    st.markdown(f"<div style='display:flex; justify-content:center; padding:4px 0;'><div style='border:2px solid {c_val}; color:{c_val}; padding:4px 0; border-radius:4px; width:44px; text-align:center; font-weight:700; font-size:13px;'>{val}</div></div>", unsafe_allow_html=True)
    else:
        st.warning("Sélectionnez au moins 2 joueurs.")


# --- ONGLET 4 : ANALYSE QUADRANT ---
with tab4:
    st.subheader("📈 Graphique d'Analyse à Deux Axes (Cross-Analyse)")
    reverse_mapping = {v: k for k, v in stats_mapping.items()}
    options_labels = list(stats_mapping.values())

    graph_col1, graph_col2 = st.columns(2)
    with graph_col1: x_label = st.selectbox("Sélectionner l'Axe X (Horizontal)", options_labels, index=4)
    with graph_col2: y_label = st.selectbox("Sélectionner l'Axe Y (Vertical)", options_labels, index=3)

    x_col = f"{reverse_mapping[x_label]} (Centile)"
    y_col = f"{reverse_mapping[y_label]} (Centile)"

    if len(filtered_df) > 0:
        plot_df = filtered_df.copy()
        plot_df['Club_Label'] = plot_df['Équipe'].fillna("Sans club")

        plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors='coerce').fillna(0)
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors='coerce').fillna(0)

        fig = px.scatter(
            plot_df, x=x_col, y=y_col, text=player_col, color='Note_Moyenne_Stats',
            color_continuous_scale='Viridis', labels={x_col: f"{x_label.upper()} (Score)", y_col: f"{y_label.upper()} (Score)"}
        )
        fig.update_traces(textposition='top center', marker=dict(size=12, opacity=0.9, line=dict(width=1, color='#ffffff')))
        fig.update_layout(
            plot_bgcolor='#0c1017', paper_bgcolor='#05070a', font_color='#ffffff',
            xaxis=dict(gridcolor='#161b22', zerolinecolor='#21262d', range=[-5, 105]),
            yaxis=dict(gridcolor='#161b22', zerolinecolor='#21262d', range=[-5, 105]), height=580
        )
        fig.add_shape(type="line", x0=50, y0=-5, x1=50, y1=105, line=dict(color="#8b949e", width=1, dash="dash"))
        fig.add_shape(type="line", x0=-5, y0=50, x1=105, y1=50, line=dict(color="#8b949e", width=1, dash="dash"))
        st.plotly_chart(fig, use_container_width=True)
