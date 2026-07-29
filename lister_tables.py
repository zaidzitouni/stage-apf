"""Liste les tables présentes dans la base SQLite du projet."""
import sqlite3
from pathlib import Path

CHEMIN_DB = Path(__file__).parent / "data" / "db" / "apf.db"

with sqlite3.connect(CHEMIN_DB) as conn:
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        print(row[0])
