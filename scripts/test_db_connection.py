#!/usr/bin/env python
import os
import sys
import psycopg2

url = os.getenv("DATABASE_URL")
if not url:
    print("DATABASE_URL no está definida. Define la variable antes de ejecutar.")
    sys.exit(1)

print("Probando conexión a:", url)
try:
    conn = psycopg2.connect(url)
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        print("Conectado. Postgres:", cur.fetchone()[0])
    conn.close()
    print("OK")
except Exception as e:
    print("Error de conexión:", e)
    sys.exit(2)
