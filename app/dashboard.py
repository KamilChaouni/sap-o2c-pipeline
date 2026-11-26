"""
Tableau de bord Order-to-Cash (Streamlit).

Lit les fichiers Parquet de data/gold/ produits par scripts/export_gold.py.
On ne se connecte pas à warehouse.duckdb : le tableau de bord peut rester
ouvert pendant que dbt tourne, sans verrouiller la base.

Lancement (depuis la racine du projet) :
    streamlit run app/dashboard.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DOSSIER_GOLD = Path(__file__).resolve().parent.parent / "data" / "gold"

# ---------------------------------------------------------------------------
# Couleurs (palette validée : bleu / orange distinguables, y compris daltonisme)
# ---------------------------------------------------------------------------
BLEU = "#257de0"
ORANGE = "#f47230"
ENCRE = "#191919"
ENCRE_2 = "#666666"
GRILLE = "#e7e7e7"
AXE = "#c2c2c2"

MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
               "juil.", "août", "sept.", "oct.", "nov.", "déc."]

st.set_page_config(page_title="Order-to-Cash SAP", page_icon="📦", layout="wide")


# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------
@st.cache_data
def charger(_version: float) -> dict[str, pd.DataFrame]:
    """_version = date de modification des fichiers : le cache se vide quand on réexporte."""
    tables = {}
    for nom in ["fait_ventes", "dim_client", "dim_article", "dim_date", "qualite_resume"]:
        tables[nom] = pd.read_parquet(DOSSIER_GOLD / f"{nom}.parquet")
    return tables


def version_fichiers() -> float:
    return max(f.stat().st_mtime for f in DOSSIER_GOLD.glob("*.parquet"))


if not (DOSSIER_GOLD / "fait_ventes.parquet").exists():
    st.error("Aucune donnée Gold trouvée. Lancez d'abord : `python scripts/export_gold.py`")
    st.stop()

data = charger(version_fichiers())
ventes = (
    data["fait_ventes"]
    .merge(data["dim_client"][["client_id", "nom_client_maitre", "code_pays"]], on="client_id", how="left")
    .merge(data["dim_article"][["article_id", "groupe_marchandises", "est_inconnu"]], on="article_id", how="left")
)
for col in ["date_commande", "date_livraison", "date_facture"]:
    ventes[col] = pd.to_datetime(ventes[col])
for col in ["montant_commande", "montant_facture", "prix_unitaire_net",
            "quantite_commandee", "quantite_livree", "quantite_facturee"]:
    ventes[col] = ventes[col].astype(float)
ventes["annee"] = ventes["date_commande"].dt.year


# ---------------------------------------------------------------------------
# Mise en forme
# ---------------------------------------------------------------------------
def euros(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"{x / 1_000_000:,.2f} M€".replace(",", " ").replace(".", ",")
    if abs(x) >= 1_000:
        return f"{x / 1_000:,.0f} k€".replace(",", " ")
    return f"{x:,.0f} €".replace(",", " ")


def pourcent(x: float) -> str:
    return f"{x:.1%}".replace(".", ",")


def style(fig: go.Figure, hauteur: int = 360) -> go.Figure:
    fig.update_layout(
        height=hauteur,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=ENCRE_2, size=13),
        separators=", ",  # virgule décimale, espace pour les milliers
        hoverlabel=dict(bgcolor="white", font_color=ENCRE, bordercolor=GRILLE),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color=ENCRE_2)),
        barcornerradius=4,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXE, ticks="")
    fig.update_yaxes(gridcolor=GRILLE, zeroline=False, linecolor=AXE)
    return fig


def afficher(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# En-tête et filtres (une seule ligne, au-dessus des graphiques)
# ---------------------------------------------------------------------------
st.title("Order-to-Cash")
st.caption("Données SAP simulées · commandes (VBAK/VBAP), livraisons (LIKP/LIPS), factures (VBRK/VBRP)")

f1, f2, f3 = st.columns(3)
annees = sorted(ventes["annee"].dropna().unique())
choix_annees = f1.multiselect("Année de commande", annees, default=annees)
pays = sorted(ventes["code_pays"].dropna().unique())
choix_pays = f2.multiselect("Pays du client", pays, default=pays)
groupes = sorted(ventes["groupe_marchandises"].dropna().unique())
choix_groupes = f3.multiselect("Groupe d'articles", groupes, default=groupes)

v = ventes[
    ventes["annee"].isin(choix_annees)
    & ventes["code_pays"].isin(choix_pays)
    & ventes["groupe_marchandises"].isin(choix_groupes)
]
if v.empty:
    st.warning("Aucune vente pour ces filtres.")
    st.stop()

onglet1, onglet2, onglet3 = st.tabs(["Vue d'ensemble", "Suivi Order-to-Cash", "Qualité des données"])


# ---------------------------------------------------------------------------
# Onglet 1 : vue d'ensemble
# ---------------------------------------------------------------------------
with onglet1:
    ca_commande = v["montant_commande"].sum()
    ca_facture = v["montant_facture"].sum()
    livre_non_facture = v.loc[v["statut"] == "Livré non facturé", "montant_commande"].sum()
    nb_commandes = v["commande_id"].nunique()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("CA commandé", euros(ca_commande))
    k2.metric("CA facturé", euros(ca_facture))
    k3.metric("Taux de facturation", pourcent(ca_facture / ca_commande if ca_commande else 0))
    k4.metric("Livré non facturé", euros(livre_non_facture))
    k5.metric("Commandes", f"{nb_commandes:,}".replace(",", " "))

    st.subheader("CA par mois")
    par_mois_cmd = v.groupby(v["date_commande"].dt.to_period("M"))["montant_commande"].sum()
    fact = v.dropna(subset=["date_facture"])
    par_mois_fac = fact.groupby(fact["date_facture"].dt.to_period("M"))["montant_facture"].sum()
    mensuel = pd.concat([par_mois_cmd.rename("commandé"), par_mois_fac.rename("facturé")], axis=1).fillna(0).sort_index()
    # le dernier mois facturé est souvent incomplet : on s'arrête au dernier mois de commande
    mensuel = mensuel[mensuel.index <= par_mois_cmd.index.max()]
    x = [f"{MOIS_COURTS[p.month - 1]} {p.year}" for p in mensuel.index]

    fig = go.Figure()
    for col, couleur, nom in [("commandé", BLEU, "CA commandé (date de commande)"),
                              ("facturé", ORANGE, "CA facturé (date de facture)")]:
        fig.add_trace(go.Scatter(
            x=x, y=mensuel[col], name=nom, mode="lines",
            line=dict(color=couleur, width=2),
            hovertemplate="%{y:,.0f} €<extra>" + nom.split(" (")[0] + "</extra>",
        ))
        # étiquette directe en fin de courbe
        fig.add_annotation(x=x[-1], y=mensuel[col].iloc[-1], text=euros(mensuel[col].iloc[-1]),
                           showarrow=False, xanchor="left", xshift=6, font=dict(color=ENCRE, size=12))
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix=" €", tickformat=",.0f", rangemode="tozero")
    afficher(style(fig))

    with st.expander("Voir les données mensuelles"):
        st.dataframe(mensuel.set_axis(x).style.format("{:,.0f} €"), width="stretch")

    st.subheader("CA commandé par groupe d'articles")
    par_groupe = v.groupby("groupe_marchandises")["montant_commande"].sum().sort_values()
    fig = go.Figure(go.Bar(
        x=par_groupe.values, y=par_groupe.index, orientation="h",
        marker_color=BLEU, text=[euros(x) for x in par_groupe.values],
        textposition="outside", textfont=dict(color=ENCRE),
        hovertemplate="%{y} : %{x:,.0f} €<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[0, par_groupe.max() * 1.15])
    fig.update_yaxes(showgrid=False)
    afficher(style(fig, 320))


# ---------------------------------------------------------------------------
# Onglet 2 : suivi Order-to-Cash
# ---------------------------------------------------------------------------
with onglet2:
    d1, d2 = st.columns(2)
    d1.metric("Délai moyen commande → livraison", f"{v['delai_livraison_jours'].mean():.1f} jours".replace(".", ","))
    d2.metric("Délai moyen commande → facture", f"{v['delai_facturation_jours'].mean():.1f} jours".replace(".", ","))

    gauche, droite = st.columns(2)

    with gauche:
        st.subheader("Montant commandé par statut")
        ordre = ["Facturé", "Facturé partiellement", "Livré non facturé", "Non livré", "Refusé"]
        par_statut = v.groupby("statut")["montant_commande"].sum().reindex(ordre).fillna(0)
        fig = go.Figure(go.Bar(
            x=par_statut.index, y=par_statut.values, marker_color=BLEU,
            text=[euros(x) for x in par_statut.values], textposition="outside",
            textfont=dict(color=ENCRE),
            hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
        ))
        fig.update_yaxes(visible=False, range=[0, par_statut.max() * 1.15])
        afficher(style(fig))

    with droite:
        st.subheader("Top 10 clients : livré non facturé")
        top = (v[v["statut"] == "Livré non facturé"]
               .groupby("nom_client_maitre")["montant_commande"].sum()
               .nlargest(10).sort_values())
        fig = go.Figure(go.Bar(
            x=top.values, y=top.index, orientation="h", marker_color=BLEU,
            text=[euros(x) for x in top.values], textposition="outside",
            textfont=dict(color=ENCRE),
            hovertemplate="%{y} : %{x:,.0f} €<extra></extra>",
        ))
        fig.update_xaxes(visible=False, range=[0, top.max() * 1.25 if len(top) else 1])
        fig.update_yaxes(showgrid=False)
        afficher(style(fig))

    st.subheader("Répartition des délais de facturation")
    delais = v["delai_facturation_jours"].dropna()
    fig = go.Figure(go.Histogram(
        x=delais, xbins=dict(size=1), marker_color=BLEU,
        marker_line=dict(color="white", width=2),  # espace entre les barres
        hovertemplate="%{x} jours : %{y} postes<extra></extra>",
    ))
    fig.update_xaxes(title="Jours entre commande et facture", title_font=dict(color=ENCRE_2))
    fig.update_yaxes(title="Postes", title_font=dict(color=ENCRE_2))
    afficher(style(fig, 300))

    with st.expander("Détail des postes livrés non facturés"):
        detail = v[v["statut"] == "Livré non facturé"][
            ["commande_id", "poste", "nom_client_maitre", "date_commande", "date_livraison", "montant_commande"]
        ].sort_values("montant_commande", ascending=False)
        st.dataframe(detail, width="stretch", hide_index=True)
        st.download_button("Télécharger en CSV", detail.to_csv(index=False).encode("utf-8"),
                           "livre_non_facture.csv", "text/csv")


# ---------------------------------------------------------------------------
# Onglet 3 : qualité des données
# ---------------------------------------------------------------------------
with onglet3:
    q = data["qualite_resume"].copy()
    bloquantes = q.loc[q["niveau"] == "Bloquant", "nb_lignes_en_erreur"].fillna(0).sum()

    if bloquantes > 0:
        st.error(f"❌ {int(bloquantes)} ligne(s) en erreur sur des contrôles bloquants : les chiffres ne sont pas fiables.")
    else:
        st.success("✅ Aucun contrôle bloquant en erreur : les chiffres du tableau de bord sont fiables.")

    def etat(ligne) -> str:
        if pd.isna(ligne["nb_lignes_en_erreur"]):
            return "❔ Non exécuté"
        if ligne["nb_lignes_en_erreur"] == 0:
            return "✅ OK"
        return "❌ Erreur" if ligne["niveau"] == "Bloquant" else "⚠️ À corriger dans SAP"

    q["État"] = q.apply(etat, axis=1)
    q["date_controle"] = pd.to_datetime(q["date_controle"]).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(
        q[["État", "controle", "niveau", "nb_lignes_en_erreur", "date_controle"]].rename(columns={
            "controle": "Contrôle", "niveau": "Niveau",
            "nb_lignes_en_erreur": "Lignes en erreur", "date_controle": "Date du contrôle",
        }),
        width="stretch", hide_index=True,
    )

    ca_inconnu = v.loc[v["est_inconnu"] == True, "montant_commande"].sum()  # noqa: E712
    st.metric("CA rattaché à un article inconnu", euros(ca_inconnu),
              help="Postes dont l'article n'existe pas dans MARA (rattachés à 'INCONNU').")
    st.caption("Le détail des lignes en erreur se trouve dans le schéma `audit` de la base DuckDB.")
