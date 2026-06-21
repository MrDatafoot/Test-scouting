import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import html
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Daniel Data - Analyse Football", initial_sidebar_state="expanded")

# --- CONVERTISSEUR DE PAYS EN EMOJI DRAPEAU ---
def get_flag_emoji(country_name):
    if not country_name or not isinstance(country_name, str):
        return "🏳️"
    mapping = {
        "MAROC": "🇲🇦", "FRANCE": "🇫🇷", "ESPAGNE": "🇪🇸", "ITALIE": "🇮🇹", 
        "PORTUGAL": "🇵🇹", "ANGLETERRE": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "ALLEMAGNE": "🇩🇪", "BELGIQUE": "🇧🇪"
    }
    return mapping.get(country_name.upper().strip(), "🏳️")

# --- COULEURS STYLE FOOTBALL MANAGER ---
def get_fm_color(score):
    if score >= 90: return "#00d2ff"  # Elite
    if score >= 75: return "#00ff66"  # Fort
    if score >= 55: return "#ffd60a"  # Correct
    if score >= 35: return "#ff9f0a"  # Fragile
    if score >= 15: return "#ff453a"  # Faible
    return "#bf5af2"                  # Critique

# --- SÉCURISATION DES VARIABLES COMPATIBLES (A AJUSTER SELON TON DATAFRAME) ---
# Simulation rapide de données si tes variables ne sont pas encore lues
if 'filtered_df' not in locals():
    filtered_df = pd.DataFrame([{
        "Joueur": "Ayoub Bouaddi", "Équipe": "Lille OSC", "Âge": 18, "Rôle Majeur": "Récupérateur",
        "Note_Moyenne_Stats": 74, "SL": 40, "BB": 65, "MN": 40, "ST": 48, "RC": 78, "Pays": "Maroc",
        "CONS (Centile)": 73, "CREA (Centile)": 59, "FINI (Centile)": 6, "PASS (Centile)": 34,
        "DRB (Centile)": 30, "DEF (Centile)": 81, "PHY (Centile)": 50, "VIT (Centile)": 92
    }])
    player_col = "Joueur"
    stats_cols = ["CONS", "CREA", "FINI", "PASS", "DRB", "DEF", "PHY", "VIT"]
    STATS_MAPPING = {
        "CONS": "Utilisation", "CREA": "Attaque", "FINI": "Finition", "PASS": "Création",
        "DRB": "Construction", "DEF": "Dribble", "PHY": "Percussion", "VIT": "Engagement"
    }

# --- STYLE CSS GLOBAL ET SIDEBAR CUSTOM (Rendu DA.jpg) ---
st.markdown("""
<style>
    /* Reset & Fond Global Dark de l'application */
    [data-testid="stAppViewContainer"] { background-color: #05070a !important; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    
    /* Design de la Sidebar de gauche */
    [data-testid="stSidebar"] {
        background-color: #0c1017 !important;
        border-right: 1px solid #1f242c !important;
        width: 260px !important;
    }
    
    /* Style du Titre Logo dans la Sidebar */
    .sidebar-logo { padding: 10px 0 20px 5px; border-bottom: 1px solid #21262d; margin-bottom: 25px; }
    .sidebar-logo h1 { color: #ffffff; font-size: 19px; font-weight: 900; letter-spacing: 0.5px; margin: 0; line-height: 1.2; }
    .sidebar-logo span { color: #8b949e; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
    
    /* Boutons de Navigation de la Sidebar */
    .nav-item {
        display: flex; align-items: center; gap: 14px; padding: 11px 16px;
        border-radius: 6px; margin-bottom: 8px; cursor: pointer; color: #8b949e;
        font-weight: 700; font-size: 14px; transition: all 0.2s ease;
    }
    .nav-item:hover { color: #ffffff; background-color: rgba(255,255,255,0.03); }
    .nav-active {
        color: #00d2ff !important; background-color: rgba(0, 210, 255, 0.08) !important;
        border-left: 3px solid #00d2ff; border-radius: 0 6px 6px 0; padding-left: 13px;
    }
    
    /* Éléments du bas de la Sidebar */
    .sidebar-footer { position: fixed; bottom: 20px; left: 20px; width: 220px; }

    /* --- CARDS DESIGN (DA.jpg) --- */
    .da-card { background-color: #0c1017; border: 1px solid #1f242c; border-radius: 8px;
               padding: 20px; height: 260px; color: #e6edf2; box-sizing: border-box; }
               
    /* Profil joueur (Carte 1) */
    .prof-layout { display: flex; align-items: center; gap: 24px; height: 100%; }
    .avatar-placeholder {
        width: 150px; height: 220px; background-color: #ffffff; border-radius: 6px;
        display: flex; align-items: flex-end; justify-content: center; overflow: hidden; flex-shrink: 0;
    }
    .silhouette {
        width: 100px; height: 160px; background-color: #0f141c;
        border-radius: 50% 50% 0 0 / 40% 40% 0 0; position: relative;
    }
    .silhouette::before {
        content: ''; position: absolute; width: 56px; height: 56px;
        background-color: #0f141c; border-radius: 50%; top: -65px; left: 22px;
    }
    
    .prof-details { display: flex; flex-direction: column; justify-content: center; }
    .prof-firstname { font-size: 18px; color: #ffffff; font-weight: 700; text-transform: uppercase; line-height: 1; }
    .prof-lastname { font-size: 32px; color: #00d2ff; font-weight: 900; text-transform: uppercase; line-height: 1.1; margin-bottom: 12px; font-family: 'Arial Black', sans-serif; }
    .prof-meta { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #ffffff; font-weight: 700; margin-bottom: 6px; text-transform: uppercase; }
    .prof-meta-lbl { color: #8b949e; font-size: 12px; margin-left: auto; }

    /* Grille Performance Profils (Carte 2) */
    .perf-title { font-size: 16px; font-weight: 800; color: #ffffff; text-transform: uppercase; margin-bottom: 16px; letter-spacing: 0.5px; }
    .perf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .perf-badge { display: flex; align-items: center; border: 1px solid #21262d; border-radius: 4px; background: #07090e; overflow: hidden; height: 36px; }
    .perf-score { width: 38px; height: 100%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; font-family: 'Arial Black', sans-serif; color: #05070a; }
    .perf-name { padding-left: 10px; font-size: 12px; font-weight: 700; color: #ffffff; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION VIA SIDEBAR STATE ---
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Profil joueur"

# Rendu HTML de la Sidebar customisée
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h1>⚽ DANIEL DATA</h1>
        <span>Analyse Football</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Boutons de navigation gérés via déclencheurs Streamlit camouflés
    pages = ["Data base", "Profil joueur", "Comparateur", "Points", "Explications"]
    icons = ["📊", "👤", "⚔️", "🎯", "ℹ️"]
    
    for p, idx in zip(pages, icons):
        active_class = "nav-active" if st.session_state['current_page'] == p else ""
        if st.markdown(f'<div class="nav-item {active_class}">{idx} {p}</div>', unsafe_allow_html=True):
            pass # L'affichage visuel est géré, l'interaction se fera via boutons transparents ci-dessous
            
    # Boutons invisibles pour intercepter les clics de manière native et fluide
    st.write("")
    for p in pages:
        if st.button(f"Aller sur {p}", key=f"btn_{p}", use_container_width=True):
            st.session_state['current_page'] = p
            st.rerun()

    st.markdown("""
    <div class="sidebar-footer">
        <div class="nav-item">⚙️ Paramètres</div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PAGE ACTIVE : PROFIL JOUEUR (Rendu DA.jpg)
# ==========================================
if st.session_state['current_page'] == "Profil joueur":
    
    # --- HEADER SUPERIEUR ---
    head_col1, head_col2, head_col3 = st.columns([1.5, 2.0, 1.5])
    with head_col1:
        st.button("📂 CLUBS TOP 5 UEFA", use_container_width=False)
    with head_col2:
        selected_player = st.selectbox("🔍 RECHERCHER JOUEUR", sorted(filtered_df[player_col].unique()), label_visibility="collapsed")
    with head_col3:
        st.markdown("<p style='text-align:right; color:#8b949e; font-size:12px; margin-top:8px;'>Source de données : Wyscout</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Récupération de la ligne data du joueur sélectionné
    p_data = filtered_df[filtered_df[player_col] == selected_player].iloc[0]
    
    p_fullname = str(p_data[player_col])
    parts = p_fullname.split(maxsplit=1)
    prenom = parts[0]
    nom = parts[1] if len(parts) > 1 else ""
    
    p_club = str(p_data['Équipe'])
    p_pays = str(p_data.get('Pays', 'Maroc'))
    p_drapeau = get_flag_emoji(p_pays)
    p_role = str(p_data['Rôle Majeur']).upper()
    p_age = f"{int(p_data['Âge'])} ANS"
    
    global_score = int(round(float(p_data['Note_Moyenne_Stats'])))
    g_color = get_fm_color(global_score)

    # --- STRUCTURE DES TROIS CARTES SUPERIEURES ---
    c1, c2, c3 = st.columns([2.3, 2.2, 1.5])

    # CARTE 1 : Bloc Profil Joueur
    with c1:
        st.markdown(f"""
        <div class="da-card">
            <div class="prof-layout">
                <div class="avatar-placeholder"><div class="silhouette"></div></div>
                <div class="prof-details">
                    <div class="prof-firstname">{html.escape(prenom)}</div>
                    <div class="prof-lastname">{html.escape(nom)}</div>
                    <div class="prof-meta"><span style="color:#ff453a;">🛡️</span> {html.escape(p_club).upper()}</div>
                    <div class="prof-meta"><span>{p_drapeau}</span> {html.escape(p_pays).upper()}</div>
                    <div class="prof-meta"><span style="color:#00ff66;">⚙️</span> {html.escape(p_role)}</div>
                    <div class="prof-meta"><span style="color:#ffd60a;">🎂</span> {p_age}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # CARTE 2 : Performance Profils (Badges adaptées à la DA)
    with c2:
        roles_list = [
            ("Seconde lame", int(p_data.get("SL", 0))),
            ("Box to Box", int(p_data.get("BB", 0))),
            ("Meneur", int(p_data.get("MN", 0))),
            ("Sentinelle", int(p_data.get("ST", 0))),
            ("Récupérateur", int(p_data.get("RC", 0)))
        ]
        
        badges_html = "".join([
            f'<div class="perf-badge">'
            f'<div class="perf-score" style="background-color:{get_fm_color(sc)};">{sc}</div>'
            f'<div class="perf-name">{name}</div>'
            f'</div>' for name, sc in roles_list
        ])
        
        st.markdown(f"""
        <div class="da-card">
            <div class="perf-title">Performance Profils</div>
            <div class="perf-grid">{badges_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # CARTE 3 : Note Globale en Donut Chart Circulaire
    with c3:
        fig_donut = go.Figure(data=[go.Pie(
            values=[global_score, 100 - global_score],
            hole=0.78,
            marker=dict(colors=[g_color, '#121824']),
            hoverinfo='none', textinfo='none'
        )])
        fig_donut.update_layout(
            showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=170,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            annotations=[
                dict(text=f"<span style='font-size:46px; font-family:Arial Black; font-weight:900; color:#ffffff;'>{global_score}</span><br><span style='font-size:13px; color:#8b949e; font-weight:bold;'>/100</span>",
                     x=0.5, y=0.45, showarrow=False, textangle=0, xanchor='center', yanchor='middle')
            ]
        )
        
        st.markdown('<div class="da-card" style="text-align:center;">'
                    '<div style="font-size:11px; font-weight:800; color:#8b949e; text-align:left; margin-bottom:5px; text-transform:uppercase;">NOTE GLOBALE</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)


    # --- GRAPHIQUE DES PERFORMANCES STATISTIQUES ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    categories = [STATS_MAPPING.get(c, c).upper() for c in stats_cols]
    values = [int(p_data.get(f"{c} (Centile)", 0)) for c in stats_cols]
    colors = [get_fm_color(v) for v in values]

    fig_bars = go.Figure()
    fig_bars.add_trace(go.Bar(
        x=categories, y=values,
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Score : %{y}/100<extra></extra>",
        width=0.55  # Épaisseur élégante des barres
    ))

    # Ajout des lignes horizontales repères en pointillés (DA.jpg style)
    for val_y, color_l in [(5, "#bf5af2"), (10, "#ff453a"), (20, "#ff453a"), (30, "#ff9f0a"), (40, "#ff9f0a"), (50, "#ffd60a"), (60, "#ffd60a"), (70, "#00ff66"), (80, "#00ff66"), (90, "#00d2ff"), (95, "#00d2ff"), (100, "#ffffff")]:
        fig_bars.add_shape(
            type="line", xref="paper", yref="y", x0=0, x1=1, y0=val_y, y1=val_y,
            line=dict(color=color_l, width=0.8, dash="dash" if val_y not in [50, 100] else "solid"), layer='below'
        )

    # Étiquettes textuelles à gauche du graphique (ELITE, FORT, CORRECT, etc.)
    annotations_list = [
        {"y": 96, "t": "ELITE", "sub": "TOP MONDIAL", "c": "#00d2ff"},
        {"y": 81, "t": "FORT", "sub": "SUR LA MOYENNE", "c": "#00ff66"},
        {"y": 61, "t": "CORRECT", "sub": "DANS LA MOYENNE", "c": "#ffd60a"},
        {"y": 41, "t": "FRAGILE", "sub": "SOUS LA MOYENNE", "c": "#ff9f0a"},
        {"y": 21, "t": "FAIBLE", "sub": "À AMÉLIORER", "c": "#ff453a"},
        {"y": 6,  "t": "CRITIQUE", "sub": "ALERTE DATA", "c": "#bf5af2"}
    ]
    for ann in annotations_list:
        fig_bars.add_annotation(
            xref="paper", yref="y", x=-0.02, y=ann["y"],
            text=f"<b style='color:{ann['c']}; font-size:11px;'>{ann['t']}</b><br><span style='color:#8b949e; font-size:8px;'>{ann['sub']}</span>",
            showarrow=False, xanchor="right", yanchor="middle"
        )

    fig_bars.update_layout(
        plot_bgcolor='#07090e', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=30, l=140, r=10), height=520, showlegend=False,
        xaxis=dict(tickfont=dict(color='#ffffff', size=11, family='Arial Black'), gridcolor='rgba(0,0,0,0)', fixedrange=True),
        yaxis=dict(range=[0, 105], gridcolor='rgba(0,0,0,0)',
                   tickvals=[0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
                   tickfont=dict(color='#8b949e', size=10), fixedrange=True, side="left"),
    )
    
    st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})

else:
    # Page de transition pour les autres onglets en attendant tes consignes
    st.title(f"Section : {st.session_state['current_page']}")
    st.info("Cette section va recevoir les éléments déplacés de ton ancienne sidebar. J'attends tes instructions pour les organiser !")
