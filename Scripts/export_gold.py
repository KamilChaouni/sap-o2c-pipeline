"""
Exporte la couche Gold en fichiers Parquet pour le tableau de bord.

Le tableau de bord lit ces fichiers : pas de pilote à installer, et pas de
verrou sur warehouse.duckdb pendant qu'il est ouvert.

Sorties (data/gold/) :
    fait_ventes.parquet, dim_client.parquet, dim_article.parquet, dim_date.parquet
    qualite_resume.parquet : nombre de lignes en erreur par test dbt (schéma audit)

Utilisation (après dbt build) :
    python scripts/export_gold.py
"""

import argparse
from pathlib import Path

import duckdb

TABLES_GOLD = ["fait_ventes", "dim_client", "dim_article", "dim_date"]

# Tests dbt à afficher dans l'onglet "Qualité" du tableau de bord
TESTS_QUALITE = {
    "assert_reconciliation_bronze_gold": ("Réconciliation Bronze / Gold", "Bloquant"),
    "assert_facture_sans_livraison": ("Facturé plus que livré", "Bloquant"),
    "assert_entete_commande_egale_somme_postes": ("Écart en-tête / postes de commande", "Avertissement"),
    "assert_articles_orphelins": ("Articles absents de MARA", "Avertissement"),
    "assert_livraisons_sans_date_sortie": ("Livraisons sans date de sortie", "Avertissement"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export de la couche Gold en Parquet.")
    parser.add_argument("--db", type=Path, default=Path("data/warehouse.duckdb"))
    parser.add_argument("--out", type=Path, default=Path("data/gold"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.db), read_only=True)

    print("Export Gold -> Parquet")
    for table in TABLES_GOLD:
        chemin = args.out / f"{table}.parquet"
        con.execute(f"COPY gold.{table} TO '{chemin.as_posix()}' (FORMAT parquet)")
        nb = con.execute(f"SELECT count(*) FROM gold.{table}").fetchone()[0]
        print(f"  {table:<15} {nb:>8} lignes -> {chemin}")

    # Résumé qualité : une ligne par test
    tables_audit = {
        r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'audit'"
        ).fetchall()
    }
    lignes = []
    for test, (libelle, niveau) in TESTS_QUALITE.items():
        nb = (con.execute(f"SELECT count(*) FROM audit.{test}").fetchone()[0]
              if test in tables_audit else None)
        lignes.append(f"('{test}', '{libelle}', '{niveau}', {nb if nb is not None else 'NULL'})")

    chemin = args.out / "qualite_resume.parquet"
    con.execute(f"""
        COPY (
            SELECT *, current_timestamp AS date_controle
            FROM (VALUES {", ".join(lignes)}) AS t(test, controle, niveau, nb_lignes_en_erreur)
        ) TO '{chemin.as_posix()}' (FORMAT parquet)
    """)
    print(f"  {'qualite_resume':<15} {len(lignes):>8} lignes -> {chemin}")

    con.close()
    print("Terminé.")


if __name__ == "__main__":
    main()
