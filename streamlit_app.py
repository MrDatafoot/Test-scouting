import html
import math
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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


# ===========================================================================
# COULEURS UNIFIÉES
# ===========================================================================
def get_fm_color(val: float) -> str:
    """Retourne la couleur FM associée à une valeur numérique sur 100."""
    try:
        val = float(val)
        if math.isnan(val):
            return '#4a5568'
        if val >= 90: return '#00d2ff'   # ELITE   (Cyan)
        elif val >= 70: return '#00ff66' # FORT    (Vert)
        elif val >= 50: return '#ffd60a' # CORRECT (Jaune)
        elif val >= 30: return '#ff9f0a' # FRAGILE (Orange)
        elif val >= 15: return '#ff453a' # FAIBLE  (Rouge)
        else: return '#bf5af2'           # CRITIQUE (Violet)
    except Exception:
        return '#4a5568'


# ===========================================================================
# CONSTANTES ET REFERENTIELS
# ===========================================================================
CLUBS_PREMIER_LEAGUE = {c.upper() for c in [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Burnley", "Chelsea",
    "Crystal Palace", "Everton", "Fulham", "Leeds United", "Liverpool", "Manchester City",
    "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland",
    "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers"
]}
CLUBS_LIGUE_1 = {c.upper() for c in [
    "Angers SCO", "Auxerre", "Brest", "Le Havre", "Lens", "Lille", "Lorient", "Metz",
    "Monaco", "Nantes", "Nice", "Olympique Lyonnais", "Olympique Marseille", "PSG",
    "Paris", "Rennes", "Strasbourg", "Toulouse"
]}
CLUBS_LIGA = {c.upper() for c in [
    "Athletic Bilbao", "Atlético Madrid", "Barcelona", "Celta de Vigo", "Deportivo Alavés",
    "Elche", "Espanyol", "Getafe", "Girona", "Levante", "Mallorca", "Osasuna", "Rayo Vallecano",
    "Real Betis", "Real Madrid", "Real Oviedo", "Real Sociedad", "Sevilla", "Valencia", "Villarreal"
]}
CLUBS_SERIE_A = {c.upper() for c in [
    "Atalanta", "Bologna", "Cagliari", "Como", "Cremonese", "Fiorentina", "Genoa",
    "Hellas Verona", "Internazionale", "Juventus", "Lazio", "Lecce", "Milan", "Napoli",
    "Parma", "Pisa", "Roma", "Sassuolo", "Torino", "Udinese"
]}
CLUBS_BUNDESLIGA = {c.upper() for c in [
    "Augsburg", "Bayer Leverkusen", "Bayern München", "Borussia Dortmund", "Borussia M'gladbach",
    "Eintracht Frankfurt", "Freiburg", "Hamburger SV", "Heidenheim", "Hoffenheim", "Köln",
    "Mainz 05", "RB Leipzig", "St. Pauli", "Stuttgart", "Union Berlin", "Werder Bremen", "Wolfsburg"
]}
CLUBS_LDC_QUART = {c.upper() for c in [
    "PSG", "Liverpool", "Real Madrid", "Bayern München", "Arsenal", "Atlético Madrid", "Barcelona"
]}

BAREME_CHAMPIONNATS = {
    "Premier League": 100,
    "La Liga": 95,
    "Serie A": 95,
    "Bundesliga": 94,
    "Ligue 1": 93,
    "Autre": 80,
}

ROLES_MAPPING = {
    'SL': 'Seconde Lame',
    'BB': 'Box to Box',
    'MN': 'Meneur',
    'ST': 'Sentinelle',
    'RC': 'Récupérateur',
}

STATS_MAPPING = {
    'UTIL': 'Utilisation', 'ATTA': 'Attaque',   'FINI': 'Finition',
    'CREA': 'Création',    'CONS': 'Construction','DRIB': 'Dribble',
    'PERC': 'Percussion',  'ENGA': 'Engagement', 'RECU': 'Récupération',
    'DEFE': 'Défense',     'ANTI': 'Anticipation','AERI': 'Aérien',
}


def attribuer_championnat(club: str) -> str:
    c = str(club).upper().strip()
    if c in CLUBS_PREMIER_LEAGUE: return "Premier League"
    if c in CLUBS_LIGUE_1:        return "Ligue 1"
    if c in CLUBS_LIGA:           return "La Liga"
    if c in CLUBS_SERIE_A:        return "Serie A"
    if c in CLUBS_BUNDESLIGA:     return "Bundesliga"
    return "Autre"


# --- CHARGEMENT ET TRAITEMENT DES DONNÉES ---
@st.cache_data
def load_and_process_data():
    df = pd.read_excel("MILIEUX.ods", engine="odf")
    df.columns = [str(c).strip() for c in df.columns]

    df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    df["Âge"] = pd.to_numeric(df["Âge"], errors='coerce').fillna(22).astype(int)

    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    df[player_col] = df[player_col].astype(str).str.upper().str.strip()

    if 'Équipe' in df.columns:
        team_col = 'Équipe'
    elif 'Equipe' in df.columns:
        df.rename(columns={'Equipe': 'Équipe'}, inplace=True)
        team_col = 'Équipe'
    else:
        team_col = None

    if team_col:
        df['Équipe'] = df['Équipe'].fillna("Sans club")
        df['Championnat']     = df['Équipe'].apply(attribuer_championnat)
        df['LDC_Quart_Etape'] = df['Équipe'].apply(lambda c: str(c).upper().strip() in CLUBS_LDC_QUART)
    else:
        df['Équipe']          = "Sans club"
        df['Championnat']     = "Autre"
        df['LDC_Quart_Etape'] = False

    role_cols = [c for c in ROLES_MAPPING.keys() if c in df.columns]

    for col in ['M'] + role_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Role_Code_Majeur'] = df[role_cols].idxmax(axis=1)
    df['Rôle Majeur']      = df['Role_Code_Majeur'].map(ROLES_MAPPING)
    df['Role_Valeur_Max']  = df[role_cols].max(axis=1)

    N = len(df)
    df['Score_M']    = df['M']
    df['Score_Role'] = df['Role_Valeur_Max']
    df['Rang_Global_M']    = df['M'].rank(ascending=False, method='min')

    if N > 1:
        df['Score_Rang_Global'] = ((df['Rang_Global_M'] / N) - 1) * -100
    else:
        df['Score_Rang_Global'] = 100.0

    df['Score_Rang_Role'] = df.groupby('Role_Code_Majeur')['Role_Valeur_Max'].transform(
        lambda x: ((x.rank(ascending=False, method='min') / len(x)) - 1) * -100
        if len(x) > 1 else pd.Series([100.0] * len(x), index=x.index)
    )

    df['Note_Championnat'] = df['Championnat'].map(BAREME_CHAMPIONNATS).fillna(80)

    def calculer_note(row):
        somme = (
            row['Score_M'] + row['Score_Role'] +
            row['Score_Rang_Global'] + row['Score_Rang_Role'] +
            row['Note_Championnat']
        )
        if row['LDC_Quart_Etape']:
            return round((somme + 97) / 6, 1)
        return round(somme / 5, 1)

    df['Note_Moyenne_Stats'] = df.apply(calculer_note, axis=1)

    stats_cols = [c for c in STATS_MAPPING.keys() if c in df.columns]
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[f'{col} (Centile)'] = df[col].round().astype(int)

    return df, player_col, stats_cols


try:
    df, player_col, stats_cols = load_and_process_data()
except Exception as e:
    st.error(f"Impossible de charger le fichier ou erreur de calcul : {e}")
    st.stop()


# ===========================================================================
# GENERATION DE TABLEAU VIA VECTORISATION
# ===========================================================================
def build_html_table(table_df: pd.DataFrame, player_col: str, stats_cols: list) -> str:
    headers = (
        "<th class='fm-th fm-th-left'>Joueur / Club</th>"
        "<th class='fm-th'>Âge</th>"
        "<th class='fm-th'>Rôle</th>"
        "<th class='fm-th'>Général</th>"
    ) + "".join(f"<th class='fm-th'>{STATS_MAPPING[c].upper()}</th>" for c in stats_cols)

    def build_row(row):
        p_name  = html.escape(str(row[player_col]).upper())
        p_club  = html.escape(str(row['Équipe']))
        p_role  = html.escape(str(row['Rôle Majeur']))
        p_age   = int(row["Âge"])
        p_note  = int(round(row['Note_Moyenne_Stats']))
        c_note  = get_fm_color(p_note)

        stat_cells = ""
        for c in stats_cols:
            val = row[f"{c} (Centile)"]
            color = get_fm_color(val)
            stat_cells += (
                f"<td class='fm-td'>"
                f"<span class='fm-badge' style='border:2px solid {color};color:{color} !important;'>"
                f"{val}</span></td>"
            )

        return (
            f"<tr class='fm-tr'>"
            f"<td class='fm-td fm-td-left'>"
            f"<div style='display:flex;align-items:center;gap:12px;'>"
            f"<div style='width:30px;height:30px;background:#0c1017;border:1px solid #21262d;"
            f"border-radius:50%;display:flex;align-items:center;justify-content:center;'>🏃‍♂️</div>"
            f"<div><div style='font-weight:700;color:#fff;'>{p_name}</div>"
            f"<div style='font-size:11px;color:#00d2ff;'>🛡️ {p_club}</div></div></div></td>"
            f"<td class='fm-td' style='font-weight:600;'>{p_age}</td>"
            f"<td class='fm-td'><span style='color:#8b949e;font-size:12px;font-weight:600;"
            f"background:#0c1017;padding:3px 8px;border-radius:4px;border:1px solid #21262d;'>"
            f"{p_role}</span></td>"
            f"<td class='fm-td'><span class='fm-badge' style='border:2px solid {c_note};"
            f"color:{c_note} !important;'>{p_note}</span></td>"
            f"{stat_cells}</tr>"
        )

    rows = "".join(table_df.apply(build_row, axis=1))
    return f"<table class='fm-table'><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>"


# --- INTERFACE SIDEBAR ---
st.sidebar.markdown("<h2 style='color:#00d2ff; margin-bottom:0;'>BIENVENUE !</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

search_query   = st.sidebar.text_input("🔍 Rechercher un joueur", "").strip().lower()
age_min, age_max = int(df["Âge"].min()), int(df["Âge"].max())
selected_age   = st.sidebar.slider("Tranche d'âge", age_min, age_max, (age_min, age_max))

available_clubs = sorted(df['Équipe'].dropna().unique())
selected_clubs  = st.sidebar.multiselect("Clubs / Équipes", options=available_clubs)

available_roles = sorted(df['Rôle Majeur'].dropna().unique())
selected_roles  = st.sidebar.multiselect("Rôles Tactiques", options=available_roles)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<h3 style='color:#00d2ff;font-size:14px;margin-bottom:5px;text-transform:uppercase;'>🎯 Compétences Minimales</h3>",
    unsafe_allow_html=True
)
st.sidebar.markdown(
    "<p style='font-size:11px;color:#8b949e;margin-bottom:15px;'>Fixer un seuil requis par domaine :</p>",
    unsafe_allow_html=True
)

with st.sidebar.form("form_skills"):
    min_skills = {c: st.slider(STATS_MAPPING[c], 0, 100, 0, step=5) for c in stats_cols}
    st.form_submit_button("Appliquer les filtres")


# --- APPLICATION DES FILTRES ---
filtered_df = df[(df["Âge"] >= selected_age[0]) & (df["Âge"] <= selected_age[1])].copy()

if search_query:
    filtered_df = filtered_df[filtered_df[player_col].str.lower().str.contains(search_query, na=False)]
if selected_clubs:
    filtered_df = filtered_df[filtered_df['Équipe'].isin(selected_clubs)]
if selected_roles:
    filtered_df = filtered_df[filtered_df['Rôle Majeur'].isin(selected_roles)]

for c in stats_cols:
    if min_skills[c] > 0:
        filtered_df = filtered_df[filtered_df[f"{c} (Centile)"] >= min_skills[c]]

display_df = filtered_df.sort_values(by='Note_Moyenne_Stats', ascending=False)


# --- NAVIGATION PRINCIPALE ---
st.title("SCOUTING DTFOOTBALL")

tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Base Globale",
    "👤 Fiche Profil Individuelle",
    "⚔️ Comparateur Face-à-Face",
    "📈 Analyse Quadrant",
])


# --- ONGLET 1 : BASE GLOBALE ---
with tab1:
    st.subheader("Base de Données des Joueurs")

    if len(display_df) > 0:
        col_sort1, col_sort2 = st.columns([2, 1])
        with col_sort1:
            sort_options = {"Note Générale": "Note_Moyenne_Stats", "Âge": "Âge"}
            sort_options.update({STATS_MAPPING[c]: f"{c} (Centile)" for c in stats_cols})
            selected_sort_label = st.selectbox("Trier la base par :", list(sort_options.keys()), index=0)
            sort_column = sort_options[selected_sort_label]
        with col_sort2:
            sort_order    = st.selectbox("Ordre :", ["Décroissant (Max → Min)", "Croissant (Min → Max)"], index=0)
            ascending_order = sort_order == "Croissant (Min → Max)"

        final_table_df = display_df.sort_values(by=sort_column, ascending=ascending_order)
        st.markdown(build_html_table(final_table_df, player_col, stats_cols), unsafe_allow_html=True)
    else:
        st.warning("Aucun joueur ne correspond aux critères filtrés.")


# --- ONGLET 2 : PROFIL INDIVIDUEL ---
with tab2:
    if len(filtered_df) > 0:
        player_list     = sorted(filtered_df[player_col].unique())
        selected_player = st.selectbox("Choisissez un joueur", player_list)
        p_data          = filtered_df[filtered_df[player_col] == selected_player].iloc[0]

        roles_alternatifs = {
            "SECONDE LAME": int(float(p_data["SL"])) if "SL" in p_data and pd.notna(p_data["SL"]) else 0,
            "BOX TO BOX":   int(float(p_data["BB"])) if "BB" in p_data and pd.notna(p_data["BB"]) else 0,
            "MENEUR":       int(float(p_data["MN"])) if "MN" in p_data and pd.notna(p_data["MN"]) else 0,
            "SENTINELLE":   int(float(p_data["ST"])) if "ST" in p_data and pd.notna(p_data["ST"]) else 0,
            "RÉCUPÉRATEUR": int(float(p_data["RC"])) if "RC" in p_data and pd.notna(p_data["RC"]) else 0,
        }

        p_fullname = str(p_data[player_col]).upper()
        parts      = p_fullname.split(maxsplit=1)
        nom_joueur = html.escape(parts[0])
        nom_famille = html.escape(parts[1]) if len(parts) > 1 else "&nbsp;"

        p_club_str = html.escape(str(p_data['Équipe']).upper())
        p_role_str = html.escape(str(p_data['Rôle Majeur']).upper())
        p_age      = f"{int(p_data['Âge'])} ANS"

        general_note     = int(round(float(p_data['Note_Moyenne_Stats'])))
        note_color       = get_fm_color(general_note)
        current_date_str = datetime.now().strftime("%d/%m/%Y")

        st.markdown("""
        <style>
            .dt-card { background-color:#0c1017; border:1px solid #21262d; border-radius:6px;
                       padding:16px; height:255px; display:flex; color:#e6edf2; box-sizing:border-box; }
            .profile-box { justify-content:flex-start; align-items:center; gap:20px; height:255px !important; }
            .data-box    { flex-direction:column; justify-content:space-between; height:255px !important; }
            .roles-box   { flex-direction:column; justify-content:flex-start; padding:18px 20px !important; height:255px !important; }
            .rating-box  { flex-direction:column; justify-content:center; align-items:center; text-align:center; height:255px !important; }
            
            .data-item-mini { display:flex; align-items:center; gap:8px; }
            .data-text-mini { display:flex; flex-direction:column; line-height:1.2; }
            .data-val-mini  { font-size:12px; font-weight:800; color:#ffffff; text-transform:uppercase; }
            .data-lbl-mini  { font-size:9px; color:#8b949e; text-transform:uppercase; font-weight:700; }
            
            .roles-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 14px;
                          margin-top:16px; width:100%; align-items:center; }
            .role-badge-item  { display:flex; align-items:center; gap:8px; }
            .role-score-badge { border:2px solid #fff; display:flex; align-items:center;
                                justify-content:center; width:40px; height:28px; border-radius:4px;
                                font-weight:900; font-size:0.95rem; font-family:'Arial Black',sans-serif;
                                text-align:center; flex-shrink:0; }
            .role-name-lbl    { font-size:0.85rem; font-weight:800; color:#ffffff;
                                text-transform:uppercase; white-space:nowrap; letter-spacing:0.2px; }
                                
            .rating-big-new   { font-size:80px; font-weight:900; line-height:0.9;
                                font-family:'Arial Black',sans-serif; }
            .rating-max-new   { font-size:20px; color:#8b949e; font-weight:bold; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2.2, 0.9, 2.5, 1.0])

        with col1:
            st.markdown(f"""
            <div class="dt-card profile-box">
                <div style="font-size:75px; background:#05070a; border:1px solid #21262d; border-radius:6px;
                            width:140px; height:215px; display:flex; align-items:center; justify-content:center;
                            flex-shrink:0;">👤</div>
                <div style="display:flex; flex-direction:column; justify-content:center; min-width:0;">
                    <div style="font-size:18px; color:#8b949e; font-weight:700; line-height:1; text-transform:uppercase;">{nom_joueur}</div>
                    <div style="font-size:28px; color:#ffffff; font-weight:900; line-height:1.1; margin-bottom:4px; text-transform:uppercase;">{nom_famille}</div>
                    <div style="font-size:14px; color:#ffffff; font-weight:800; text-transform:uppercase; margin-bottom:8px;">MILIEU DE TERRAIN</div>
                    <div style="color:#ff453a; font-size:14px; font-weight:800; margin-bottom:3px;">🛡️ {p_club_str}</div>
                    <div style="color:{note_color}; font-size:13px; font-weight:800; text-transform:uppercase; margin-bottom:8px;">🟢 {p_role_str}</div>
                    <div style="font-size:13px; color:#ffffff; font-weight:700;">🎂 {p_age}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="dt-card data-box" style="padding-top:14px; padding-bottom:14px;">
                <div class="data-item-mini">⚙️ <div class="data-text-mini"><span class="data-val-mini">DTFOOTBALL</span><span class="data-lbl-mini">Création &amp; Calculs</span></div></div>
                <div class="data-item-mini">⏳ <div class="data-text-mini"><span class="data-val-mini">2025/2026</span><span class="data-lbl-mini">Saison</span></div></div>
                <div class="data-item-mini">ℹ️ <div class="data-text-mini"><span class="data-val-mini">WYSCOUT</span><span class="data-lbl-mini">Source</span></div></div>
                <div class="data-item-mini">📅 <div class="data-text-mini"><span class="data-val-mini">{current_date_str}</span><span class="data-lbl-mini">Date du jour</span></div></div>
            </div>""", unsafe_allow_html=True)

        with col3:
            b_html = "".join(
                f'<div class="role-badge-item">'
                f'<div class="role-score-badge" style="border-color:{get_fm_color(score)}; color:{get_fm_color(score)};">{score}</div>'
                f'<div class="role-name-lbl">{html.escape(name)}</div></div>'
                for name, score in roles_alternatifs.items()
            )
            st.markdown(f"""
            <div class="dt-card roles-box">
                <div style="font-size:18px; font-weight:900; color:#ffffff; text-transform:uppercase; letter-spacing:0.6px;">PERFORMANCE PROFILS</div>
                <div class="roles-grid">{b_html}</div>
            </div>""", unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="dt-card rating-box">
                <div style="font-size:11px; font-weight:800; color:#8b949e; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">NOTE GÉNÉRALE</div>
                <div style="display:flex; align-items:flex-end; justify-content:center;">
                    <span class="rating-big-new" style="color:{note_color};">{general_note}</span>
                    <span class="rating-max-new" style="margin-bottom:4px;">/100</span>
                </div>
            </div>""", unsafe_allow_html=True)

        # --- BARRES STATISTIQUES ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='color:#ffffff; font-size:16px; font-weight:800; text-transform:uppercase;"
            "letter-spacing:0.5px; margin-bottom:15px;'>PERFORMANCES STATISTIQUES</h3>",
            unsafe_allow_html=True,
        )

        categories = [
            STATS_MAPPING[c].upper().replace(" ", "<br>") if STATS_MAPPING[c] != 'Défense' else "DÉFENSE"
            for c in stats_cols
        ]
        values = [
            int(float(p_data.get(f"{c} (Centile)", 0))) if pd.notna(p_data.get(f"{c} (Centile)")) else 0
            for c in stats_cols
        ]
        colors = [get_fm_color(v) for v in values]

        fig_bars = go.Figure()
        fig_bars.add_trace(go.Bar(
            x=categories, y=values,
            marker=dict(color=colors, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Score: %{y}/100<extra></extra>",
        ))

        for val_y, style_ligne, couleur_ligne in [
            (5,  "dot",   "#bf5af2"), (10, "solid", "#ff453a"), (20, "dot",   "#ff453a"),
            (30, "solid", "#ff9f0a"), (40, "dot",   "#ff9f0a"), (50, "solid", "#ffd60a"),
            (60, "dot",   "#ffd60a"), (70, "solid", "#00ff66"), (80, "dot",   "#00ff66"),
            (90, "solid", "#00d2ff"), (95, "dot",   "#00d2ff"), (100,"solid", "#ffffff"),
        ]:
            fig_bars.add_shape(
                type="line", xref="paper", yref="y",
                x0=0, x1=1, y0=val_y, y1=val_y,
                line=dict(color=couleur_ligne, width=1, dash=style_ligne if style_ligne == "dot" else None),
                layer='below',
            )

        for t in [
            {"y_text": 96, "title": "ELITE",    "sub": "TOP MONDIAL",      "color": "#00d2ff"},
            {"y_text": 81, "title": "FORT",     "sub": "AU DESSUS",        "color": "#00ff66"},
            {"y_text": 61, "title": "CORRECT",  "sub": "DANS LA MOYENNE",  "color": "#ffd60a"},
            {"y_text": 41, "title": "FRAGILE",  "sub": "SOUS MOYENNE",     "color": "#ff9f0a"},
            {"y_text": 21, "title": "FAIBLE",   "sub": "À AMÉLIORER",      "color": "#ff453a"},
            {"y_text": 6,  "title": "CRITIQUE", "sub": "ALERTE DATA",      "color": "#bf5af2"},
        ]:
            t_html = (
                f"<b style='color:{t['color']}; font-size:14px; font-family:\"Arial Black\",sans-serif;"
                f"font-weight:900; letter-spacing:1px;'>{t['title']}</b>"
                f"<br><span style='color:#8b949e; font-size:9px; font-weight:800; letter-spacing:0.5px;'>{t['sub']}</span>"
            )
            fig_bars.add_annotation(
                xref="paper", yref="y", x=-0.03, y=float(t["y_text"]),
                text=t_html, showarrow=False, xanchor="right", yanchor="middle",
            )

        fig_bars.update_layout(
            plot_bgcolor='#05070a', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=40, l=180, r=20),
            height=650, showlegend=False,
            xaxis=dict(tickfont=dict(color='#ffffff', size=11), gridcolor='rgba(0,0,0,0)', fixedrange=True),
            yaxis=dict(range=[0, 110], gridcolor='rgba(0,0,0,0)',
                       tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                       tickfont=dict(color='#8b949e', size=11), fixedrange=True),
        )
        st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("Aucun joueur trouvé.")


# --- ONGLET 3 : COMPARATEUR ---
with tab3:
    st.subheader("⚔️ Comparateur de Cartes Face-à-Face")

    all_players      = sorted(df[player_col].unique())
    selected_players = st.multiselect(
        "Choisissez les joueurs à comparer side-by-side",
        options=all_players,
        default=all_players[:2] if len(all_players) >= 2 else all_players,
    )

    if len(selected_players) >= 2:
        st.markdown("<br>", unsafe_allow_html=True)
        cols_header = st.columns([2.5] + [2] * len(selected_players))
        with cols_header[0]:
            st.markdown(
                "<div style='background-color:#0c1017;padding:15px;border-radius:6px;text-align:center;"
                "border:1px solid #21262d;min-height:75px;display:flex;align-items:center;justify-content:center;'>"
                "<div style='font-size:12px;font-weight:700;color:#8b949e;text-transform:uppercase;'>CARACTÉRISTIQUES</div></div>",
                unsafe_allow_html=True,
            )
        for idx, p_name in enumerate(selected_players):
            p_row  = df[df[player_col] == p_name].iloc[0]
            p_club = html.escape(str(p_row['Équipe']))
            p_role = html.escape(str(p_row['Rôle Majeur']))
            with cols_header[idx + 1]:
                st.markdown(
                    f"<div style='background-color:#0c1017;padding:10px;border-radius:6px;text-align:center;"
                    f"border:1px solid #21262d;min-height:75px;'>"
                    f"<div style='font-size:14px;font-weight:900;color:#fff;'>{html.escape(p_name.upper())}</div>"
                    f"<div style='font-size:11px;color:#00d2ff;font-weight:600;'>{p_role}</div>"
                    f"<div style='font-size:10px;color:#8b949e;'>🛡️ {p_club}</div></div>",
                    unsafe_allow_html=True,
                )

        cols_note = st.columns([2.5] + [2] * len(selected_players))
        with cols_note[0]:
            st.markdown(
                "<div style='padding:12px 10px;font-size:12px;font-weight:800;color:#00d2ff;text-transform:uppercase;'>"
                "NOTE GENERALE AJUSTÉE</div>",
                unsafe_allow_html=True,
            )
        for idx, p_name in enumerate(selected_players):
            val_note = int(round(df[df[player_col] == p_name].iloc[0]['Note_Moyenne_Stats']))
            c_note   = get_fm_color(val_note)
            with cols_note[idx + 1]:
                st.markdown(
                    f"<div style='display:flex;justify-content:center;padding:6px 0;'>"
                    f"<div style='border:2px solid {c_note};color:{c_note};padding:4px 0;border-radius:4px;"
                    f"width:44px;text-align:center;font-weight:800;font-size:13px;'>{val_note}</div></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<hr style='border-color:#21262d;margin:10px 0;'>", unsafe_allow_html=True)

        for c in stats_cols:
            cols_data = st.columns([2.5] + [2] * len(selected_players))
            with cols_data[0]:
                st.markdown(
                    f"<div style='padding:10px 10px;font-size:13px;font-weight:600;color:#c9d1d9;'>"
                    f"{STATS_MAPPING[c].upper()}</div>",
                    unsafe_allow_html=True,
                )
            for idx, p_name in enumerate(selected_players):
                val_raw = df[df[player_col] == p_name].iloc[0].get(f'{c} (Centile)', 0)
                val     = int(float(val_raw)) if pd.notna(val_raw) else 0
                c_val   = get_fm_color(val)
                with cols_data[idx + 1]:
                    st.markdown(
                        f"<div style='display:flex;justify-content:center;padding:4px 0;'>"
                        f"<div style='border:2px solid {c_val};color:{c_val};padding:4px 0;border-radius:4px;"
                        f"width:44px;text-align:center;font-weight:700;font-size:13px;'>{val}</div></div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.warning("Sélectionnez au moins 2 joueurs.")


# --- ONGLET 4 : ANALYSE QUADRANT ---
with tab4:
    st.markdown(
        "<h2 style='color:#ffffff;font-size:22px;font-weight:800;text-transform:uppercase;'>"
        "📊 Graphique d'Analyse à Deux Axes (Cross-Analyse)</h2>",
        unsafe_allow_html=True,
    )
 
    col_x, col_y = st.columns(2)
    with col_x:
        idx_x  = stats_cols.index("CONS") if "CONS" in stats_cols else 0
        axis_x = st.selectbox("Sélectionner l'Axe X (Horizontal)", stats_cols, index=idx_x,
                              format_func=lambda c: STATS_MAPPING.get(c, c))
    with col_y:
        idx_y  = stats_cols.index("CREA") if "CREA" in stats_cols else (1 if len(stats_cols) > 1 else 0)
        axis_y = st.selectbox("Sélectionner l'Axe Y (Vertical)", stats_cols, index=idx_y,
                              format_func=lambda c: STATS_MAPPING.get(c, c))
 
    st.markdown("---")
    st.markdown(
        "<h4 style='color:#ffffff;font-size:14px;font-weight:800;text-transform:uppercase;margin-bottom:10px;'>"
        "⚙️ Options d'affichage des labels</h4>",
        unsafe_allow_html=True,
    )
 
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.5, 2.0, 2.0])
    with c_ctrl1:
        mode_label = st.radio(
            "Affichage du texte sur le graphique",
            ["Masquer tous les noms", "Afficher tous les noms", "Sélection à la carte"],
            index=0,
        )
    with c_ctrl2:
        liste_equipes = sorted(filtered_df['Équipe'].dropna().unique()) if 'Équipe' in filtered_df.columns else []
        equipes_cibles = st.multiselect("Afficher les noms de l'équipe :", liste_equipes)
    with c_ctrl3:
        liste_joueurs = sorted(filtered_df[player_col].unique())
        joueurs_cibles = st.multiselect("Chercher et afficher un joueur spécifique :", liste_joueurs)
 
    # Fonction de traitement optimisée pour .apply()
    def compute_label(row):
        if mode_label == "Masquer tous les noms":
            return ""
        nom_j  = str(row[player_col])
        if mode_label == "Afficher tous les noms":
            return nom_j
        
        # Mode : Sélection à la carte
        club_j = str(row.get('Équipe', ''))
        if nom_j in joueurs_cibles or club_j in equipes_cibles:
            return nom_j
        return ""
 
    # Remplacement de iterrows() par une vectorisation .apply() beaucoup plus rapide
    plot_text = filtered_df.apply(compute_label, axis=1).tolist() if len(filtered_df) > 0 else []
 
    fig_quad = go.Figure()
    scores_couleurs = filtered_df['Note_Moyenne_Stats'] if 'Note_Moyenne_Stats' in filtered_df.columns else [50] * len(filtered_df)
 
    # Ciblage des colonnes Centiles pour correspondre aux axes 0-100
    col_graph_x = f"{axis_x} (Centile)"
    col_graph_y = f"{axis_y} (Centile)"

    if len(filtered_df) > 0:
        fig_quad.add_trace(go.Scatter(
            x=filtered_df[col_graph_x],
            y=filtered_df[col_graph_y],
            mode="markers+text",
            text=plot_text,
            textposition="top center",
            textfont=dict(color="#ffffff", size=10),
            marker=dict(
                size=11,
                color=scores_couleurs,
                colorscale=[
                    [0.0, '#bf5af2'], [0.3, '#ff453a'], [0.5, '#ff9f0a'],
                    [0.6, '#ffd60a'], [0.8, '#00ff66'], [1.0, '#00d2ff'],
                ],
                showscale=True,
                colorbar=dict(title="Note Moyenne", thickness=15, tickfont=dict(color='#8b949e')),
                line=dict(width=1, color='#0d1117'),
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "🛡️ Club : %{customdata[1]}<br>"
                f"⚡ {STATS_MAPPING.get(axis_x)} : %{{x}}/100<br>"
                f"🎯 {STATS_MAPPING.get(axis_y)} : %{{y}}/100<br>"
                "📈 Note Globale : %{customdata[2]}/100<extra></extra>"
            ),
            customdata=list(zip(
                filtered_df[player_col],
                filtered_df['Équipe'] if 'Équipe' in filtered_df.columns else ['Sans Club'] * len(filtered_df),
                filtered_df['Note_Moyenne_Stats'].round(1) if 'Note_Moyenne_Stats' in filtered_df.columns else [0] * len(filtered_df),
            )),
        ))
 
    # Lignes des quadrants à 50
    fig_quad.add_shape(type="line", x0=50, x1=50, y0=0,  y1=100, line=dict(color="#8b949e", width=1, dash="dash"))
    fig_quad.add_shape(type="line", x0=0,  x1=100, y0=50, y1=50,  line=dict(color="#8b949e", width=1, dash="dash"))
 
    fig_quad.update_layout(
        plot_bgcolor='#0c1017', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=50, l=60, r=20),
        height=680,
        xaxis=dict(
            title=dict(text=f"{STATS_MAPPING.get(axis_x, axis_x).upper()} (Score)", font=dict(color='#8b949e', size=12)),
            range=[-2, 102], gridcolor='#21262d', tickfont=dict(color='#8b949e'), fixedrange=True,
        ),
        yaxis=dict(
            title=dict(text=f"{STATS_MAPPING.get(axis_y, axis_y).upper()} (Score)", font=dict(color='#8b949e', size=12)),
            range=[-2, 102], gridcolor='#21262d', tickfont=dict(color='#8b949e'), fixedrange=True,
        ),
    )
    st.plotly_chart(fig_quad, use_container_width=True, config={'displayModeBar': True})
