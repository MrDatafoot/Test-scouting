import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Configuration de la page
st.set_page_config(page_title="Scouting Milieux", layout="wide")

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    df = pd.read_excel("MILIEUX.ods")
    # Nettoyage colonnes
    df.columns = [str(c).strip() for c in df.columns]
    if "Unnamed" in df.columns[0] or df.columns[0] == "A":
        df.rename(columns={df.columns[0]: "Âge"}, inplace=True)
    
    # Statistiques
    player_col = "Joueur" if "Joueur" in df.columns else df.columns[1]
    stats_mapping = {'UTIL': 'MINUTES', 'ATTA': 'ATTAQUE', 'FINI': 'FINITION', 'CREA': 'CRÉATION', 'CONS': 'CONSTRUCTION', 'DRIB': 'DRIBBLES', 'PERC': 'PERCUSSION', 'ENGA': 'ENGAGEMENT', 'RECU': 'RÉCUPÉRATION', 'DEFE': 'UN CONTRE UN', 'ANTI': 'ANTICIPATION', 'AERI': 'AÉRIEN'}
    stats_cols = [c for c in stats_mapping.keys() if c in df.columns]
    
    for col in stats_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Note_Moyenne_Stats'] = df[stats_cols].mean(axis=1).round(1)
    return df, player_col, stats_cols, stats_mapping

df, player_col, stats_cols, stats_mapping = load_data()

# --- INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Base de données", "👤 Profil Joueur", "⚔️ Comparateur", "📈 Analyse"])

# 1. BASE DE DONNÉES (Ag-Grid)
with tab1:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filter=True)
    AgGrid(df, gridOptions=gb.build(), theme='alpine', height=500)

# 2. PROFIL JOUEUR
with tab2:
    selected = st.selectbox("Choisir un joueur", df[player_col].unique())
    p_data = df[df[player_col] == selected].iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"### {selected}")
        st.write(f"**Club :** {p_data.get('Équipe', 'N/A')}")
    with c2:
        st.metric("Note Moyenne", p_data['Note_Moyenne_Stats'])
    # Affichage des stats en barres simples
    for stat in stats_cols:
        st.write(f"{stats_mapping[stat]} : {p_data[stat]}")
        st.progress(p_data[stat] / 100)

# 3. COMPARATEUR
with tab3:
    players = st.multiselect("Sélectionnez 2-3 joueurs", df[player_col].unique(), default=df[player_col].iloc[:2])
    if players:
        # Création du tableau de comparaison
        comp_df = df[df[player_col].isin(players)].set_index(player_col)
        st.dataframe(comp_df[['Note_Moyenne_Stats'] + stats_cols])

# 4. ANALYSE
with tab4:
    x = st.selectbox("Axe X", stats_cols, index=0)
    y = st.selectbox("Axe Y", stats_cols, index=1)
    fig = px.scatter(df, x=x, y=y, color="Note_Moyenne_Stats", hover_name=player_col)
    st.plotly_chart(fig, use_container_width=True)
