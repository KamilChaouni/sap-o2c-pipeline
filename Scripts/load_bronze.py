"""
Charge les CSV SAP (data/raw/) dans la couche Bronze.

Principe de la couche Bronze : on garde les données EXACTEMENT comme la source,
sans rien corriger. Toutes les colonnes restent en texte (VARCHAR), pour ne pas
perdre les zéros devant les numéros SAP ni planter sur une date '00000000'.
On ajoute seulement deux colonnes techniques :
    _loaded_at   : date et heure du chargement
    _source_file : fichier d'origine

Sorties :
    data/bronze/<table>.parquet       : copie brute au format Parquet
    data/warehouse.duckdb             : base DuckDB, schéma "bronze"

Utilisation :
    python scripts/load_bronze.py
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import duckdb

TABLES = ["KNA1", "MARA", "MAKT", "VBAK", "VBAP", "LIKP", "LIPS", "VBRK", "VBRP"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Chargement de la couche Bronze.")
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--bronze", type=Path, default=Path("data/bronze"))
    parser.add_argument("--db", type=Path, default=Path("data/warehouse.duckdb"))
    args = parser.parse_args()

    args.bronze.mkdir(parents=True, exist_ok=True)
    loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    con = duckdb.connect(str(args.db))
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    print(f"Chargement Bronze ({loaded_at} UTC)")
    for table in TABLES:
        csv_path = args.raw / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"{csv_path} introuvable : lancez d'abord scripts/generate_sap_data.py"
            )

        parquet_path = args.bronze / f"{table.lower()}.parquet"

        # all_varchar = true : tout en texte, comme la source
        select_brut = f"""
            SELECT
                *,
                TIMESTAMP '{loaded_at}' AS _loaded_at,
                '{csv_path.name}'       AS _source_file
            FROM read_csv('{csv_path.as_posix()}', header = true, all_varchar = true)
        """

        # 1. Copie Parquet
        con.execute(f"COPY ({select_brut}) TO '{parquet_path.as_posix()}' (FORMAT parquet)")

        # 2. Table DuckDB (rechargement complet à chaque exécution)
        con.execute(f"""
            CREATE OR REPLACE TABLE bronze.{table.lower()} AS
            SELECT * FROM read_parquet('{parquet_path.as_posix()}')
        """)

        nb = con.execute(f"SELECT count(*) FROM bronze.{table.lower()}").fetchone()[0]
        print(f"  bronze.{table.lower():<5} {nb:>8} lignes")

    con.close()
    print(f"Terminé. Base : {args.db}")


if __name__ == "__main__":
    main()
