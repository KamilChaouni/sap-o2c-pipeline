# Pipeline SAP Order-to-Cash

Projet d'autoformation : une pipeline data complète, de données SAP jusqu'à un tableau de bord, avec uniquement des outils gratuits.

## Objectif

Simuler une entreprise sous SAP et construire la chaîne :

```
Données SAP simulées (CSV)
  → Bronze : données brutes (Parquet / DuckDB)
  → Silver : données nettoyées (dbt)
  → Gold   : modèle en étoile (dbt)
  → Tableau de bord (Power BI Desktop)
```

Le tout est automatisé avec GitHub Actions (exécution planifiée, tests de qualité, alertes).

## Tables SAP simulées

| Table | Contenu |
|---|---|
| KNA1 | Clients |
| MARA / MAKT | Articles et désignations |
| VBAK / VBAP | Commandes de vente (en-têtes / postes) |
| LIKP / LIPS | Livraisons (en-têtes / postes) |
| VBRK / VBRP | Factures (en-têtes / postes) |

## Stack

- Python (Faker, pandas, pyarrow)
- DuckDB
- dbt-core + dbt-duckdb
- Power BI Desktop
- GitHub Actions

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Générer les données

```bash
python scripts/generate_sap_data.py                 # 5 000 commandes (par défaut)
python scripts/generate_sap_data.py --orders 50000  # plus de volume
```

Les CSV sont écrits dans `data/raw/` (non versionné : on les régénère à volonté).

Défauts de qualité injectés volontairement : doublons clients, villes manquantes,
articles inexistants dans MARA, commandes non livrées, livraisons non facturées,
dates de sortie vides (`00000000`), écarts entre en-tête et postes de commande.

## Charger la couche Bronze

```bash
python scripts/load_bronze.py
```

Les CSV sont copiés tels quels (toutes les colonnes en texte) dans :
- `data/bronze/*.parquet`
- la base `data/warehouse.duckdb`, schéma `bronze`

Deux colonnes techniques sont ajoutées : `_loaded_at` (date du chargement) et `_source_file`.

## Transformer avec dbt (Silver)

```bash
cd dbt
dbt debug    # vérifie la connexion à DuckDB
dbt build    # crée les modèles et lance les tests
```

Couche Silver (schéma `silver`) :

| Modèle | Source SAP | Ce qui est fait |
|---|---|---|
| stg_clients | KNA1 | Renommage, ville vide → NULL, repérage des doublons et client maître |
| stg_articles | MARA + MAKT | Désignation française, libellé du type d'article |
| stg_commandes_entetes | VBAK | Dates SAP → dates, montants → décimaux |
| stg_commandes_postes | VBAP | Clé commande-poste, indicateur de refus |
| stg_livraisons_entetes | LIKP | Date de sortie `00000000` → NULL |
| stg_livraisons_postes | LIPS | Lien vers le poste de commande |
| stg_factures_entetes | VBRK | Indicateur d'annulation |
| stg_factures_postes | VBRP | Liens vers la livraison et la commande |

Macros utiles : `sap_date()` (AAAAMMJJ → date) et `sap_flag()` ('X' → vrai).

## Avancement

- [x] 1. Mise en place du dépôt
- [x] 2. Génération des données SAP simulées
- [x] 3. Couche Bronze
- [x] 4. dbt + couche Silver
- [ ] 5. Couche Gold
- [ ] 6. Tests de qualité et réconciliation
- [ ] 7. Tableau de bord
- [ ] 8. Automatisation (GitHub Actions)
