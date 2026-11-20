"""
Génère des données SAP Order-to-Cash simulées, au format des vraies tables SAP.

Tables produites (CSV dans data/raw/) :
    KNA1  : clients
    MARA  : articles
    MAKT  : désignations des articles
    VBAK  : commandes de vente (en-têtes)
    VBAP  : commandes de vente (postes)
    LIKP  : livraisons (en-têtes)
    LIPS  : livraisons (postes)
    VBRK  : factures (en-têtes)
    VBRP  : factures (postes)

Comme dans un vrai SAP :
    - les identifiants sont des textes avec des zéros devant (KUNNR = '0000100001')
    - les dates sont au format AAAAMMJJ ('20250314'), '00000000' = date vide
    - les postes sont numérotés de 10 en 10 ('000010', '000020'...)

Des défauts de qualité sont injectés volontairement (doublons clients, villes
manquantes, articles inexistants, dates vides...) pour les tests dbt.

Utilisation :
    python scripts/generate_sap_data.py
    python scripts/generate_sap_data.py --orders 20000 --seed 7
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------
DATE_DEBUT = date(2024, 11, 1)
DATE_FIN = date(2026, 10, 31)

VKORG = "1000"   # organisation commerciale
VTWEG = "10"     # canal de distribution
SPART = "00"     # division
WAERK = "EUR"    # devise

# Taux de défauts injectés
TAUX_DOUBLON_CLIENT = 0.02        # client créé deux fois sous deux numéros
TAUX_VILLE_MANQUANTE = 0.03       # ORT01 vide
TAUX_ARTICLE_ORPHELIN = 0.005     # poste de commande avec un article inexistant
TAUX_NON_LIVREE = 0.08            # commande jamais livrée
TAUX_NON_FACTUREE = 0.06          # livraison jamais facturée
TAUX_DATE_SORTIE_VIDE = 0.01      # WADAT_IST = '00000000'
TAUX_ECART_ENTETE = 0.01          # VBAK.NETWR différent de la somme des postes

GROUPES_ARTICLES = {
    "ELEC01": ("Câble électrique", 4.5, 25.0),
    "ELEC02": ("Disjoncteur", 15.0, 120.0),
    "OUTI01": ("Perceuse", 60.0, 350.0),
    "OUTI02": ("Visseuse", 45.0, 220.0),
    "QUIN01": ("Lot de vis", 3.0, 18.0),
    "QUIN02": ("Lot de chevilles", 2.5, 12.0),
    "PEIN01": ("Peinture acrylique", 12.0, 80.0),
    "PLOM01": ("Raccord cuivre", 1.5, 9.0),
}
QUALIFICATIFS = ["standard", "pro", "premium", "compact", "XL", "industriel"]


def fmt_date(d: date | None) -> str:
    """Date Python -> format SAP AAAAMMJJ."""
    return d.strftime("%Y%m%d") if d else "00000000"


def date_aleatoire(debut: date, fin: date) -> date:
    return debut + timedelta(days=random.randint(0, (fin - debut).days))


def ecrire_csv(dossier: Path, nom: str, lignes: list[dict]) -> None:
    chemin = dossier / f"{nom}.csv"
    with chemin.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        writer.writeheader()
        writer.writerows(lignes)
    print(f"  {nom:<5} {len(lignes):>8} lignes -> {chemin}")


# ---------------------------------------------------------------------------
# Données de référence
# ---------------------------------------------------------------------------
def generer_clients(fake: Faker, nb: int) -> list[dict]:
    clients = []
    for i in range(nb):
        clients.append({
            "MANDT": "100",
            "KUNNR": f"{100001 + i:010d}",
            "NAME1": fake.company(),
            "LAND1": random.choices(["FR", "BE", "CH", "LU", "DE"], [80, 8, 5, 3, 4])[0],
            "ORT01": "" if random.random() < TAUX_VILLE_MANQUANTE else fake.city(),
            "PSTLZ": fake.postcode(),
            "STRAS": fake.street_address(),
            "KTOKD": random.choice(["KUNA", "KUNA", "KUNA", "KUNB"]),
            "ERDAT": fmt_date(date_aleatoire(date(2015, 1, 1), DATE_DEBUT)),
            "LOEVM": "X" if random.random() < 0.01 else "",  # marqué pour suppression
        })

    # Doublons : même société et même ville, mais un nouveau numéro client
    nb_doublons = int(nb * TAUX_DOUBLON_CLIENT)
    for j, original in enumerate(random.sample(clients, nb_doublons)):
        doublon = dict(original)
        doublon["KUNNR"] = f"{100001 + nb + j:010d}"
        doublon["NAME1"] = original["NAME1"].upper()  # saisie légèrement différente
        doublon["ERDAT"] = fmt_date(date_aleatoire(date(2020, 1, 1), DATE_DEBUT))
        clients.append(doublon)
    return clients


def generer_articles(nb: int) -> tuple[list[dict], list[dict], dict]:
    mara, makt, prix = [], [], {}
    for i in range(nb):
        matnr = f"{1000001 + i:018d}"
        matkl = random.choice(list(GROUPES_ARTICLES))
        libelle, pmin, pmax = GROUPES_ARTICLES[matkl]
        prix[matnr] = round(random.uniform(pmin, pmax), 2)
        mara.append({
            "MANDT": "100",
            "MATNR": matnr,
            "MTART": random.choice(["FERT", "HAWA", "HAWA"]),  # produit fini / marchandise
            "MATKL": matkl,
            "MEINS": "PC" if not matkl.startswith("QUIN") else "BOX",
            "BRGEW": round(random.uniform(0.1, 8.0), 3),
            "GEWEI": "KG",
            "ERSDA": fmt_date(date_aleatoire(date(2015, 1, 1), DATE_DEBUT)),
        })
        qualif = random.choice(QUALIFICATIFS)
        makt.append({"MANDT": "100", "MATNR": matnr, "SPRAS": "F",
                     "MAKTX": f"{libelle} {qualif} {i + 1}"})
        makt.append({"MANDT": "100", "MATNR": matnr, "SPRAS": "E",
                     "MAKTX": f"Item {matkl} {qualif} {i + 1}"})
    return mara, makt, prix


# ---------------------------------------------------------------------------
# Flux Order-to-Cash : commande -> livraison -> facture
# ---------------------------------------------------------------------------
def generer_flux(nb_commandes: int, clients: list[dict], prix: dict) -> dict:
    vbak, vbap, likp, lips, vbrk, vbrp = [], [], [], [], [], []
    articles = list(prix)
    clients_actifs = [c["KUNNR"] for c in clients if c["LOEVM"] != "X"]

    no_livraison = 80000001
    no_facture = 90000001

    for i in range(nb_commandes):
        vbeln = f"{1000001 + i:010d}"
        kunnr = random.choice(clients_actifs)
        erdat = date_aleatoire(DATE_DEBUT, DATE_FIN)

        # --- Postes de commande (VBAP)
        postes = []
        for p in range(random.randint(1, 5)):
            posnr = f"{(p + 1) * 10:06d}"
            if random.random() < TAUX_ARTICLE_ORPHELIN:
                matnr = f"{9999000 + random.randint(1, 999):018d}"  # n'existe pas dans MARA
                netpr = round(random.uniform(5, 50), 2)
            else:
                matnr = random.choice(articles)
                netpr = round(prix[matnr] * random.uniform(0.9, 1.05), 2)  # remise ou hausse
            qte = random.randint(1, 50)
            postes.append({
                "MANDT": "100", "VBELN": vbeln, "POSNR": posnr, "MATNR": matnr,
                "KWMENG": qte, "VRKME": "PC", "NETPR": netpr,
                "NETWR": round(qte * netpr, 2), "WAERK": WAERK,
                "ABGRU": "",  # motif de refus
            })

        # Quelques postes refusés : ils ne seront pas livrés
        if len(postes) > 1 and random.random() < 0.03:
            postes[-1]["ABGRU"] = "Z1"
        vbap.extend(postes)

        total = round(sum(p["NETWR"] for p in postes if not p["ABGRU"]), 2)
        if random.random() < TAUX_ECART_ENTETE:
            total = round(total * random.uniform(0.8, 1.2), 2)  # incohérence volontaire

        vbak.append({
            "MANDT": "100", "VBELN": vbeln, "ERDAT": fmt_date(erdat),
            "AUART": random.choices(["TA", "TA", "TA", "SO"], k=1)[0],  # standard / urgente
            "VKORG": VKORG, "VTWEG": VTWEG, "SPART": SPART,
            "KUNNR": kunnr, "NETWR": total, "WAERK": WAERK,
            "VDATU": fmt_date(erdat + timedelta(days=random.randint(2, 15))),
        })

        # --- Livraison (LIKP / LIPS)
        if random.random() < TAUX_NON_LIVREE or erdat > DATE_FIN - timedelta(days=3):
            continue
        no_liv = f"{no_livraison:010d}"
        no_livraison += 1
        date_liv = erdat + timedelta(days=random.randint(1, 20))
        date_sortie = None if random.random() < TAUX_DATE_SORTIE_VIDE else date_liv
        likp.append({
            "MANDT": "100", "VBELN": no_liv, "ERDAT": fmt_date(date_liv),
            "LFART": "LF", "KUNNR": kunnr, "WADAT_IST": fmt_date(date_sortie),
            "VSTEL": random.choice(["1000", "1100"]),  # point d'expédition
        })
        postes_livres = []
        for p in postes:
            if p["ABGRU"]:
                continue
            # parfois livraison partielle
            lfimg = p["KWMENG"] if random.random() > 0.05 else max(1, p["KWMENG"] - random.randint(1, 5))
            ligne = {
                "MANDT": "100", "VBELN": no_liv, "POSNR": p["POSNR"], "MATNR": p["MATNR"],
                "LFIMG": lfimg, "VRKME": "PC", "VGBEL": vbeln, "VGPOS": p["POSNR"],
            }
            lips.append(ligne)
            postes_livres.append((p, lfimg))

        # --- Facture (VBRK / VBRP)
        if random.random() < TAUX_NON_FACTUREE or date_liv > DATE_FIN - timedelta(days=2):
            continue
        no_fac = f"{no_facture:010d}"
        no_facture += 1
        fkdat = date_liv + timedelta(days=random.randint(0, 10))
        total_fac = 0.0
        for p, qte in postes_livres:
            netwr = round(qte * p["NETPR"], 2)
            total_fac += netwr
            vbrp.append({
                "MANDT": "100", "VBELN": no_fac, "POSNR": p["POSNR"], "MATNR": p["MATNR"],
                "FKIMG": qte, "VRKME": "PC", "NETWR": netwr,
                "VGBEL": no_liv, "VGPOS": p["POSNR"],   # référence livraison
                "AUBEL": vbeln, "AUPOS": p["POSNR"],    # référence commande
            })
        vbrk.append({
            "MANDT": "100", "VBELN": no_fac, "FKART": "F2", "FKDAT": fmt_date(fkdat),
            "KUNRG": kunnr, "NETWR": round(total_fac, 2), "WAERK": WAERK,
            "FKSTO": "",  # 'X' = facture annulée
        })

    # Quelques factures annulées
    for f in random.sample(vbrk, max(1, len(vbrk) // 200)):
        f["FKSTO"] = "X"

    return {"VBAK": vbak, "VBAP": vbap, "LIKP": likp, "LIPS": lips,
            "VBRK": vbrk, "VBRP": vbrp}


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Génère des données SAP O2C simulées.")
    parser.add_argument("--orders", type=int, default=5000, help="nombre de commandes")
    parser.add_argument("--customers", type=int, default=500, help="nombre de clients")
    parser.add_argument("--materials", type=int, default=200, help="nombre d'articles")
    parser.add_argument("--seed", type=int, default=42, help="graine (mêmes données à chaque fois)")
    parser.add_argument("--out", type=Path, default=Path("data/raw"), help="dossier de sortie")
    args = parser.parse_args()

    random.seed(args.seed)
    fake = Faker("fr_FR")
    Faker.seed(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"Génération de {args.orders} commandes (seed={args.seed})...")
    clients = generer_clients(fake, args.customers)
    mara, makt, prix = generer_articles(args.materials)
    flux = generer_flux(args.orders, clients, prix)

    ecrire_csv(args.out, "KNA1", clients)
    ecrire_csv(args.out, "MARA", mara)
    ecrire_csv(args.out, "MAKT", makt)
    for nom, lignes in flux.items():
        ecrire_csv(args.out, nom, lignes)
    print("Terminé.")


if __name__ == "__main__":
    main()
