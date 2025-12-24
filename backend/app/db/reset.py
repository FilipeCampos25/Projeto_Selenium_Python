"""
Arquivo: reset.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

#!/usr/bin/env python3
"""
reset.py -- drop public schema and re-run migrations.

Usage:
  python reset.py [DATABASE_URL]
"""
import os
import subprocess
import sys
from pathlib import Path

db_url = None
if len(sys.argv) > 1:
    db_url = sys.argv[1]
if not db_url:
    db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not provided")
    sys.exit(2)

# Drop public schema and recreate (fast way to reset)
subprocess.check_call(['psql', db_url, '-c', 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'])

# Run build
build = Path(__file__).parent / 'build.py'
subprocess.check_call([sys.executable, str(build), db_url])
