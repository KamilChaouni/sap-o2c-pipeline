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

python -m pip install -r requirements.txt
```

## Avancement

- [x] 1. Mise en place du dépôt
- [ ] 2. Génération des données SAP simulées
- [ ] 3. Couche Bronze
- [ ] 4. dbt + couche Silver
- [ ] 5. Couche Gold
- [ ] 6. Tests de qualité et réconciliation
- [ ] 7. Tableau de bord
- [ ] 8. Automatisation (GitHub Actions)
