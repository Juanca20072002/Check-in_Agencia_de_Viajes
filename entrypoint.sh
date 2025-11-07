#!/usr/bin/env sh
set -e

# Debug rápido de variables de entorno relacionadas con la base de datos
echo "DEBUG: DATABASE_URL='${DATABASE_URL}'" || true
echo "DEBUG: POSTGRES_USER='${POSTGRES_USER}' POSTGRES_PW='${POSTGRES_PW}' POSTGRES_DB='${POSTGRES_DB}' POSTGRES_HOST='${POSTGRES_HOST}' POSTGRES_PORT='${POSTGRES_PORT}'" || true

# Esperar a Postgres usando psycopg2
echo "Esperando a Postgres..."
python - <<'PY'
import os, time, sys
import psycopg2

url = os.environ.get('DATABASE_URL')
if not url:
    user = os.environ.get('POSTGRES_USER', 'postgres')
    pw = os.environ.get('POSTGRES_PW', '12345')
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    db = os.environ.get('POSTGRES_DB', 'reservasdb')
    url = f'postgresql://{user}:{pw}@{host}:{port}/{db}'

for i in range(60):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print('Postgres disponible')
        sys.exit(0)
    except Exception as e:
        print(f'Intento {i+1}/60: DB no lista aún: {e}')
        time.sleep(1)

print('Timeout esperando la base de datos')
sys.exit(1)
PY

# Aplicar migraciones (no fatales: si fallan, continuamos y dejamos que la app arranque)
echo "Aplicando migraciones Alembic..."
if flask db upgrade; then
    echo "Migraciones aplicadas"
else
    echo "Fallo al aplicar migraciones; continuando arranque (temporal)"
fi

# Iniciar Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn -w ${GUNICORN_WORKERS:-3} -b 0.0.0.0:${PORT:-5000} app:app
