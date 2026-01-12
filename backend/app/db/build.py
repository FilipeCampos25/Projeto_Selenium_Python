"""
Arquivo: build.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

#!/usr/bin/env python3
"""
build.py -- apply SQL migrations to the target Postgres instance.

Usage:
  python build.py [DATABASE_URL]

Looks for DATABASE_URL env var or passes argument.
"""
import os
import subprocess
import sys
from pathlib import Path

# Allow passing DATABASE_URL as first arg or via env var
db_url = None
if len(sys.argv) > 1:
    db_url = sys.argv[1]
if not db_url:
    db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not provided (arg or env).")
    sys.exit(2)

migrations_dir = Path(__file__).parent / "migrations"
sql_files = sorted(migrations_dir.glob("*.sql"))

# Excluir arquivos de teste (ex.: 003_test_data.sql) para evitar aplicação automática
apply_files = [f for f in sql_files if "test" not in f.name.lower()]
skipped = [f for f in sql_files if f not in apply_files]

for sql in apply_files:
    print(f"Applying {sql}")
    subprocess.check_call(["psql", db_url, "-f", str(sql)])

if skipped:
    print("Skipped test migrations:")
    for s in skipped:
        print(f" - {s}")

print("Migrations applied.")
