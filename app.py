# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# CONFIG GLOBALE
# ---------------------------
st.set_page_config(
    page_title="Tableau de bord – Crédits automobiles",
    layout="wide"
)

st.title("Tableau de bord – Crédits automobiles")
st.markdown("Analyse interactive du portefeuille de financements auto.")

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


df = load_data("donnees_nettoyees.xlsx.xlsx")

# ---------------------------
# SIDEBAR – FILTRES
# ---------------------------
st.sidebar.header("Filtres")

types_pret = sorted(df["type_pret"].dropna().unique())
types_veh = sorted(df["type_vehicule"].dropna().unique())
classes_score = sorted(df["classe_de_score"].dropna().unique())
annees = sorted(df["annee_demande"].dropna().unique())
etats = sorted(df["etat_demande"].dropna().unique())

type_pret_sel = st.sidebar.multiselect(
    "Type de prêt",
    options=types_pret,
    default=types_pret
)

type_veh_sel = st.sidebar.multiselect(
    "Type de véhicule",
    options=types_veh,
    default=types_veh
)

classe_sel = st.sidebar.multiselect(
    "Classe de score",
    options=classes_score,
    default=classes_score
)

annee_sel = st.sidebar.multiselect(
    "Année de demande",
    options=annees,
    default=annees
)

etat_sel = st.sidebar.multiselect(
    "Décision de la banque",
    options=etats,
    default=etats
)

# Filtrage
df_filtre = df[
    df["type_pret"].isin(type_pret_sel)
    & df["type_vehicule"].isin(type_veh_sel)
    & df["classe_de_score"].isin(classe_sel)
    & df["annee_demande"].isin(annee_sel)
    & df["etat_demande"].isin(etat_sel)
]

st.markdown(f"**Nombre d'observations après filtrage :** {len(df_filtre):,}".replace(",", " "))

# ---------------------------
# KPI – INDICATEURS CLÉS
# ---------------------------
col1, col2, col3, col4, col5 = st.columns(5)

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

st.markdown("---")

# ---------------------------
# LIGNE 1 – STRUCTURE DU PORTEFEUILLE
# ---------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Répartition par type de prêt")
    if not df_filtre.empty:
        dist_pret = df_filtre["type_pret"].value_counts().reset_index()
        dist_pret.columns = ["type_pret", "nombre"]
        fig_pret = px.bar(
            dist_pret,
            x="type_pret",
            y="nombre",
            labels={"type_pret": "Type de prêt", "nombre": "Nombre de demandes"},
        )
        st.plotly_chart(fig_pret, use_container_width=True)
    else:
        st.info("Aucune donnée pour les filtres sélectionnés.")

with c2:
    st.subheader("Répartition par classe de score")
    if not df_filtre.empty:
        dist_score = df_filtre["classe_de_score"].value_counts().sort_index().reset_index()
        dist_score.columns = ["classe_de_score", "nombre"]
        fig_score = px.bar(
            dist_score,
            x="classe_de_score",
            y="nombre",
            labels={"classe_de_score": "Classe de score", "nombre": "Nombre de demandes"},
        )
        st.plotly_chart(fig_score, use_container_width=True)
    else:
        st.info("Aucune donnée pour les filtres sélectionnés.")

st.markdown("---")

# ---------------------------
# LIGNE 2 – ANALYSE TEMPORELLE & RISQUE
# ---------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Évolution mensuelle du nombre de demandes")
    if not df_filtre["date_demande"].isna().all():
        ts = (
            df_filtre
            .dropna(subset=["date_demande"])
            .groupby("date_demande")
            .size()
            .reset_index(name="nombre")
        )
        fig_ts = px.line(
            ts,
            x="date_demande",
            y="nombre",
            labels={"date_demande": "Date de demande", "nombre": "Nombre de demandes"},
        )
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("Dates de demande manquantes ou invalides.")

with c4:
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
        )
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("Aucune donnée pour les filtres sélectionnés.")

st.markdown("---")

# ---------------------------
# LIGNE 3 – DIMENSION GÉOGRAPHIQUE
# ---------------------------
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
    )
    fig_dep.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_dep, use_container_width=True)
else:
    st.info("Aucune donnée pour les filtres sélectionnés.")

st.markdown("---")

# ---------------------------
# TABLE + TÉLÉCHARGEMENT
# ---------------------------
st.subheader("Données détaillées (échantillon filtré)")

st.dataframe(
    df_filtre.head(500),
    use_container_width=True
)

csv = df_filtre.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Télécharger les données filtrées (CSV)",
    data=csv,
    file_name="donnees_filtrees_credits_auto.csv",
    mime="text/csv"
)

