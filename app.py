import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------
# CONFIG GLOBALE
# ---------------------------
st.set_page_config(
    page_title="Tableau de bord – Crédits automobiles",
    layout="wide"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.4rem;
        color: #2c3e50;
        border-left: 4px solid #3498db;
        padding-left: 10px;
        margin: 2rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🚗 Tableau de bord – Crédits automobiles</div>', unsafe_allow_html=True)
st.markdown("**Analyse interactive du portefeuille de financements auto**")

# ---------------------------
# CHARGEMENT & NETTOYAGE
# ---------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Nettoyage cohérent avec le rapport
    df = df.copy()
    # Taux d'endettement : valeurs présentes et entre 0 et 100
    df = df[df["taux_endettement"].notna()]
    df = df[(df["taux_endettement"] >= 0) & (df["taux_endettement"] <= 100)]
    
    # Suppression des emprunteurs mineurs (âge < 18 ans)
    df["age"] = df["annee_demande"] - df["annee_naissance"]
    df = df[df["age"] >= 18]

    # Code postal en string, création d'un département (2 premiers chiffres)
    df["code_postal"] = df["code_postal"].astype(str).str.zfill(5)
    df["departement"] = df["code_postal"].str[:2]

    # Construction d'une date "année-mois" pour les courbes temporelles
    df["date_demande"] = pd.to_datetime({
        "year": df["annee_demande"].astype(int),
        "month": df["mois_demande"].astype(int),
        "day": 1
    }, errors="coerce")

    return df

df = load_data("donnees_nettoyees.xlsx")

# ---------------------------
# SIDEBAR – FILTRES
# ---------------------------
st.sidebar.header("🔧 Filtres interactifs")

# Ajout des filtres manquants du rapport
objets_veh = sorted(df["objet_vehicule"].dropna().unique())
types_pret = sorted(df["type_pret"].dropna().unique())
types_veh = sorted(df["type_vehicule"].dropna().unique())
classes_score = sorted(df["classe_de_score"].dropna().unique())
annees = sorted(df["annee_demande"].dropna().unique())
etats = sorted(df["etat_demande"].dropna().unique())
decisions_client = sorted(df["decision_client"].dropna().unique())

# Nouveaux filtres
objet_veh_sel = st.sidebar.multiselect(
    "🎯 Objet du véhicule",
    options=objets_veh,
    default=objets_veh
)

type_pret_sel = st.sidebar.multiselect(
    "📄 Type de prêt",
    options=types_pret,
    default=types_pret
)

type_veh_sel = st.sidebar.multiselect(
    "🚙 Type de véhicule",
    options=types_veh,
    default=types_veh
)

classe_sel = st.sidebar.multiselect(
    "📊 Classe de score",
    options=classes_score,
    default=classes_score
)

annee_sel = st.sidebar.multiselect(
    "📅 Année de demande",
    options=annees,
    default=annees
)

etat_sel = st.sidebar.multiselect(
    "🏦 Décision de la banque",
    options=etats,
    default=etats
)

decision_client_sel = st.sidebar.multiselect(
    "👤 Décision du client",
    options=decisions_client,
    default=decisions_client
)

# Filtrage avec tous les nouveaux critères
df_filtre = df[
    df["objet_vehicule"].isin(objet_veh_sel)
    & df["type_pret"].isin(type_pret_sel)
    & df["type_vehicule"].isin(type_veh_sel)
    & df["classe_de_score"].isin(classe_sel)
    & df["annee_demande"].isin(annee_sel)
    & df["etat_demande"].isin(etat_sel)
    & df["decision_client"].isin(decision_client_sel)
]

st.markdown(f"**📈 Nombre d'observations après filtrage :** {len(df_filtre):,}".replace(",", " "))

# ---------------------------
# KPI – INDICATEURS CLÉS AMÉLIORÉS
# ---------------------------
st.markdown("## 📊 Indicateurs clés de performance")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Nombre de demandes", f"{len(df_filtre):,}".replace(",", " "))

with col2:
    montant_total = df_filtre["montant_pret"].sum()
    st.metric("Montant total financé", f"{montant_total:,.0f} €".replace(",", " "))

with col3:
    montant_moyen = df_filtre["montant_pret"].mean()
    st.metric("Montant moyen du prêt", f"{montant_moyen:,.0f} €".replace(",", " "))

with col4:
    if len(df_filtre) > 0:
        taux_octroi = (df_filtre["etat_demande"].eq("Octroyé").mean()) * 100
        st.metric("Taux d'octroi", f"{taux_octroi:.1f} %")
    else:
        st.metric("Taux d'octroi", "NA")

with col5:
    taux_end_moy = df_filtre["taux_endettement"].mean()
    st.metric("Taux d'endettement moyen", f"{taux_end_moy:.1f} %")

with col6:
    age_moyen = df_filtre["age"].mean()
    st.metric("Âge moyen", f"{age_moyen:.1f} ans")

st.markdown("---")

# ---------------------------
# NOUVELLE SECTION : ANALYSE DES DÉCISIONS
# ---------------------------
st.markdown('<div class="section-header">🎯 Analyse des décisions</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    st.subheader("Décision de la banque")
    if not df_filtre.empty:
        decision_banque = df_filtre["etat_demande"].value_counts()
        fig_banque = px.pie(
            values=decision_banque.values,
            names=decision_banque.index,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_banque.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_banque, use_container_width=True)

with c2:
    st.subheader("Décision du client")
    if not df_filtre.empty:
        decision_client = df_filtre["decision_client"].value_counts()
        fig_client = px.pie(
            values=decision_client.values,
            names=decision_client.index,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_client.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_client, use_container_width=True)

# ---------------------------
# LIGNE 1 – STRUCTURE DU PORTEFEUILLE AMÉLIORÉE
# ---------------------------
st.markdown('<div class="section-header">📈 Structure du portefeuille</div>', unsafe_allow_html=True)

c3, c4, c5 = st.columns(3)

with c3:
    st.subheader("Répartition par type de prêt")
    if not df_filtre.empty:
        dist_pret = df_filtre["type_pret"].value_counts().reset_index()
        dist_pret.columns = ["type_pret", "nombre"]
        fig_pret = px.bar(
            dist_pret,
            x="type_pret",
            y="nombre",
            labels={"type_pret": "Type de prêt", "nombre": "Nombre de demandes"},
            color="type_pret",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_pret, use_container_width=True)

with c4:
    st.subheader("Objet du véhicule")
    if not df_filtre.empty:
        dist_objet = df_filtre["objet_vehicule"].value_counts().reset_index()
        dist_objet.columns = ["objet_vehicule", "nombre"]
        fig_objet = px.pie(
            dist_objet,
            values="nombre",
            names="objet_vehicule",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_objet.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_objet, use_container_width=True)

with c5:
    st.subheader("Type de véhicule")
    if not df_filtre.empty:
        dist_type_veh = df_filtre["type_vehicule"].value_counts().reset_index()
        dist_type_veh.columns = ["type_vehicule", "nombre"]
        fig_type_veh = px.bar(
            dist_type_veh,
            x="type_vehicule",
            y="nombre",
            labels={"type_vehicule": "Type de véhicule", "nombre": "Nombre de demandes"},
            color="type_vehicule",
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        st.plotly_chart(fig_type_veh, use_container_width=True)

# ---------------------------
# LIGNE 2 – ANALYSE DES SCORES ET RISQUES
# ---------------------------
st.markdown('<div class="section-header">⚖️ Analyse des scores et risques</div>', unsafe_allow_html=True)

c6, c7 = st.columns(2)

with c6:
    st.subheader("Répartition par classe de score")
    if not df_filtre.empty:
        dist_score = df_filtre["classe_de_score"].value_counts().sort_index().reset_index()
        dist_score.columns = ["classe_de_score", "nombre"]
        fig_score = px.bar(
            dist_score,
            x="classe_de_score",
            y="nombre",
            labels={"classe_de_score": "Classe de score", "nombre": "Nombre de demandes"},
            color="nombre",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_score, use_container_width=True)

with c7:
    st.subheader("Taux d'endettement par classe de score")
    if not df_filtre.empty:
        fig_box = px.box(
            df_filtre,
            x="classe_de_score",
            y="taux_endettement",
            labels={
                "classe_de_score": "Classe de score",
                "taux_endettement": "Taux d'endettement (%)"
            },
            color="classe_de_score"
        )
        st.plotly_chart(fig_box, use_container_width=True)

# ---------------------------
# NOUVELLE SECTION : ANALYSE FINANCIÈRE
# ---------------------------
st.markdown('<div class="section-header">💰 Analyse financière</div>', unsafe_allow_html=True)

c8, c9 = st.columns(2)

with c8:
    st.subheader("Distribution du prix d'achat")
    if not df_filtre.empty:
        fig_prix = px.histogram(
            df_filtre,
            x="prix_achat",
            nbins=50,
            labels={"prix_achat": "Prix d'achat (€)", "count": "Nombre de demandes"},
            color_discrete_sequence=['#2E86AB']
        )
        fig_prix.update_layout(bargap=0.1)
        st.plotly_chart(fig_prix, use_container_width=True)

with c9:
    st.subheader("Distribution des taux d'intérêt")
    if not df_filtre.empty:
        fig_taux = px.histogram(
            df_filtre,
            x="taux_interet",
            nbins=30,
            labels={"taux_interet": "Taux d'intérêt (%)", "count": "Nombre de demandes"},
            color_discrete_sequence=['#A23B72']
        )
        st.plotly_chart(fig_taux, use_container_width=True)

# ---------------------------
# LIGNE 3 – ANALYSE TEMPORELLE
# ---------------------------
st.markdown('<div class="section-header">📅 Analyse temporelle</div>', unsafe_allow_html=True)

c10, c11 = st.columns(2)

with c10:
    st.subheader("Évolution mensuelle des demandes")
    if not df_filtre["date_demande"].isna().all():
        ts = (
            df_filtre
            .dropna(subset=["date_demande"])
            .groupby("date_demande")
            .size()
            .reset_index(name="nombre")
        )
        fig_ts = px.area(
            ts,
            x="date_demande",
            y="nombre",
            labels={"date_demande": "Date de demande", "nombre": "Nombre de demandes"},
            color_discrete_sequence=['#3498db']
        )
        st.plotly_chart(fig_ts, use_container_width=True)

with c11:
    st.subheader("Distribution des durées de prêt")
    if not df_filtre.empty:
        fig_duree = px.histogram(
            df_filtre,
            x="duree_pret",
            nbins=20,
            labels={"duree_pret": "Durée du prêt (mois)", "count": "Nombre de demandes"},
            color_discrete_sequence=['#F18F01']
        )
        st.plotly_chart(fig_duree, use_container_width=True)

# ---------------------------
# LIGNE 4 – DIMENSION GÉOGRAPHIQUE
# ---------------------------
st.markdown('<div class="section-header">🗺️ Analyse géographique</div>', unsafe_allow_html=True)

st.subheader("Top 15 des départements par nombre de demandes")

if not df_filtre.empty:
    top_dep = (
        df_filtre
        .groupby("departement")
        .size()
        .reset_index(name="nombre")
        .sort_values("nombre", ascending=False)
        .head(15)
    )
    
    fig_dep = px.bar(
        top_dep,
        x="nombre",
        y="departement",
        orientation="h",
        labels={"departement": "Département", "nombre": "Nombre de demandes"},
        color="nombre",
        color_continuous_scale="blues",
        text="nombre"
    )
    
    fig_dep.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=500,
        showlegend=False,
        xaxis_title="Nombre de demandes",
        yaxis_title="Département",
        plot_bgcolor='white'
    )
    
    fig_dep.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        marker_line_color='darkblue',
        marker_line_width=1
    )
    
    st.plotly_chart(fig_dep, use_container_width=True)

# ---------------------------
# TABLE + TÉLÉCHARGEMENT
# ---------------------------
st.markdown('<div class="section-header">📋 Données détaillées</div>', unsafe_allow_html=True)

st.subheader("Échantillon des données filtrées")

if not df_filtre.empty:
    st.dataframe(
        df_filtre.head(500),
        use_container_width=True,
        height=400
    )
    
    st.info(f"📊 Affichage de 500 lignes sur {len(df_filtre):,} au total. Utilisez le bouton de téléchargement pour obtenir toutes les données.")
    
    # Statistiques résumées
    with st.expander("📈 Statistiques descriptives des données filtrées"):
        st.dataframe(df_filtre[['montant_pret', 'prix_achat', 'taux_endettement', 'taux_interet', 'duree_pret', 'age']].describe())
    
    csv = df_filtre.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Télécharger les données filtrées (CSV)",
        data=csv,
        file_name="donnees_filtrees_credits_auto.csv",
        mime="text/csv",
        use_container_width=True
    )

# ---------------------------
# FOOTER INFORMATIF
# ---------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #7f8c8d; font-size: 0.9rem;'>"
    "📊 Tableau de bord créé avec Streamlit • Données issues de l'analyse descriptive de 100 384 demandes de crédit auto"
    "</div>", 
    unsafe_allow_html=True
)
