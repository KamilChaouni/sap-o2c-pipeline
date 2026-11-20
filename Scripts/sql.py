"""
Petite console SQL pour explorer data/warehouse.duckdb sans outil externe.

Utilisation :
    python scripts/sql.py                                   # mode interactif
    python scripts/sql.py "SELECT * FROM bronze.vbak LIMIT 5"  # une seule requête

En mode interactif : tapez une requête terminée par ';' (elle peut tenir sur
plusieurs lignes), puis Entrée. Tapez 'exit' pour quitter.
"""

import sys

import duckdb

DB = "data/warehouse.duckdb"


def executer(con, requete: str) -> None:
    try:
        con.sql(requete).show(max_rows=50, max_width=200)
    except duckdb.Error as e:
        print(f"Erreur : {e}")
    except AttributeError:
        print("OK")  # requête sans résultat (CREATE, etc.)


def main() -> None:
    con = duckdb.connect(DB, read_only=True)

    if len(sys.argv) > 1:
        executer(con, " ".join(sys.argv[1:]))
        return

    print(f"Connecté à {DB} (lecture seule). Terminez vos requêtes par ';'. 'exit' pour quitter.")
    print("Astuce : SHOW ALL TABLES;  ou  DESCRIBE bronze.vbak;")
    tampon = []
    while True:
        try:
            ligne = input("sql> " if not tampon else "...> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not tampon and ligne.strip().lower() in {"exit", "quit"}:
            break
        tampon.append(ligne)
        if ligne.rstrip().endswith(";"):
            executer(con, "\n".join(tampon))
            tampon = []
    con.close()


if __name__ == "__main__":
    main()
