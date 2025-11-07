# Proyecto Flask - Viajes Tolima

Estructura básica de Flask creada a partir de tu HTML/CSS existentes.

## Estructura

- app.py
- templates/
  - index.html
  - gracias.html
- static/
  - style.css
- img/ (tus imágenes originales siguen aquí; se sirven vía ruta /img/<archivo>)
- requirements.txt

## Ejecutar en local (Windows PowerShell)

1. Crear y activar entorno (opcional pero recomendado):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Ejecutar Flask:

```powershell
$env:FLASK_APP = "app.py"; $env:FLASK_ENV = "development"; python app.py
```

Luego abre http://127.0.0.1:5000/

## Ejecutar con Docker

Requisitos previos:

- Docker Desktop instalado y en ejecución (modo Linux). Abre Docker Desktop antes de continuar.

### TL;DR

```powershell
docker compose up --build -d
```

Esto construirá la imagen de la app, levantará Postgres y aplicará migraciones automáticamente. La app quedará disponible en http://localhost:5000

### Detalles

1. (Opcional) Crear un `.env` desde el ejemplo y ajustar valores:

```powershell
Copy-Item .env.example .env
# edita .env si quieres definir SMTP o cambiar claves
```

2. Construir y levantar en segundo plano:

```powershell
docker compose up --build -d
```

3. Ver logs (útil la primera vez para ver migraciones):

```powershell
docker compose logs -f web
```

4. Parar y borrar contenedores (conservar datos de la DB y de imágenes subidas):

```powershell
docker compose down
```

5. Reiniciar solo la app tras cambios de código (requiere rebuild):

```powershell
docker compose build web; docker compose up -d web
```

6. Ejecutar migraciones manualmente (si agregas nuevos modelos/cambios):

```powershell
# Generar una nueva migración
docker compose exec web flask db migrate -m "mensaje"

# Aplicar migraciones
docker compose exec web flask db upgrade
```

### Variables de entorno

El servicio `web` usa `DATABASE_URL` apuntando al servicio `db`. Puedes ajustar valores en `docker-compose.yml` o sobreescribirlos con `.env`. Para SMTP (correo de recuperación) define `SMTP_USER` y `SMTP_PASS` si quieres enviar correos reales.

### Persistencia de imágenes

Las imágenes subidas (carpeta `static/img`) se montan en el volumen `uploads` para que no se pierdan al reconstruir la imagen.

### Estructura creada para Docker

- `Dockerfile`: Imagen de la app (Python + Gunicorn)
- `docker-compose.yml`: Orquesta `web` y `db` (Postgres), con healthcheck y volumen de datos
- `entrypoint.sh`: Espera la DB, aplica migraciones Alembic y lanza Gunicorn
- `.dockerignore`: Reduce el contexto de build

## Despliegue a Internet

Tienes dos caminos: CI a Docker Hub + VPS, o push manual.

### A) CI/CD a Docker Hub (recomendado)

1. Crea un repositorio en Docker Hub con nombre `check-in-agencia` (o el que prefieras).
2. En GitHub, ve a Settings > Secrets and variables > Actions y crea:
  - `DOCKERHUB_USERNAME`: tu usuario de Docker Hub
  - `DOCKERHUB_TOKEN`: un Access Token de Docker Hub
3. Haz push a `main`. El workflow `.github/workflows/docker-publish.yml` construirá y publicará la imagen con tags `latest` y `sha`.
4. En tu servidor (VPS) con Docker y Docker Compose instalado:

```bash
git clone <tu-repo>
cd Check-in_Agencia_de_Viajes
cp .env.example .env
# Edita .env (al menos FLASK_SECRET_KEY)

# Exporta tu usuario de Docker Hub si no usas .env para DOCKERHUB_USERNAME
export DOCKERHUB_USERNAME=<tu_usuario>

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Esto mapea el puerto 80 del servidor a la app (5000 en el contenedor). Añade un proxy con TLS (Caddy/Traefik) si quieres HTTPS automático.

### B) Push manual desde tu PC

```powershell
# Inicia sesión (se recomienda usar Access Token)
docker login

# Etiqueta y sube
$user = "<tu_usuario>"
docker tag check-in_agencia_de_viajes-web:latest $user/check-in-agencia:latest
docker push $user/check-in-agencia:latest

# En el servidor (VPS)
# usa docker-compose.prod.yml como en la opción A
```

Notas:
- En producción, los volúmenes `pgdata` y `uploads` preservan datos y archivos subidos.
- Si tienes dominio y correo, considera Caddy/Traefik para HTTPS con Let’s Encrypt.

## Despliegue gratuito sin Render (Koyeb / Fly.io + Neon Postgres)

Si ya no puedes usar Render, una alternativa free estable es:

- App (contenedor Docker) en Koyeb o Fly.io.
- Base de datos Postgres serverless en Neon (también puedes usar Supabase o Railway Postgres).

La app ya está lista para producción con Gunicorn y hace `flask db upgrade` al arrancar. Solo necesitas definir `DATABASE_URL` y `FLASK_SECRET_KEY` en el proveedor.

### 1) Crear Postgres en Neon

1. Ve a https://neon.tech/ y crea un proyecto Postgres gratuito.
2. Copia el connection string en formato SQLAlchemy:
  - Formato: `postgresql://<user>:<password>@<host>:<port>/<db>`
  - Ejemplo: `postgresql://neondb_owner:xxxxx@ep-abc-123.us-east-2.aws.neon.tech/neondb`
3. Importar el respaldo inicial (opcional):
  - Opción simple: en el panel de Neon, abre el SQL Editor y pega el contenido de `reservasdb.sql`.
  - Opción con Docker (sin instalar psql local):

```powershell
# 1) Entra a la carpeta del proyecto donde está reservasdb.sql
cd <ruta_del_repo>

# 2) Define tu cadena de conexión de Neon (incluye sslmode=require)
$env:PGURL = "postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require"

# 3) Ejecuta psql dentro de un contenedor y aplica el SQL del respaldo
docker run --rm -v ${PWD}:/work postgres:16-alpine \
  sh -lc "psql -d '$PGURL' -f /work/reservasdb.sql"
```

Si falla por SSL, asegúrate de tener `?sslmode=require` en la URL de conexión.

### 2) Desplegar en Koyeb (simple y rápido)

1. Ve a https://www.koyeb.com/ y crea una App nueva conectando este repo de GitHub, o elige "Dockerfile" si subes desde Git directamente.
2. Parámetros clave:
  - Runtime/Build: usa el Dockerfile del repo.
  - Puerto interno: 5000 (la app expone 5000). Koyeb publicará un URL HTTPS.
  - Variables de entorno:
    - `FLASK_SECRET_KEY`: una cadena aleatoria larga.
    - `PORT`: `5000`.
    - `DATABASE_URL`: Pega el connection string de Neon.
    - (Opcional) `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`.
3. Health check: apunta a `/health` (ya agregado) o al puerto 5000.
4. Deploy. Koyeb construirá la imagen y arrancará el servicio. En los logs verás "Aplicando migraciones Alembic..." y luego Gunicorn escuchando.

### 3) Desplegar en Fly.io (opción alternativa)

1. Instala la CLI: https://fly.io/docs/hands-on/install/
2. En este repo, ejecuta `fly launch` y responde:
  - Usa el Dockerfile.
  - App name único.
  - Puerto interno: 5000.
3. Configura variables en Fly (Dashboard o CLI):
  - `FLASK_SECRET_KEY`: cadena aleatoria.
  - `PORT`: `5000`.
  - `DATABASE_URL`: tu cadena de Neon.
4. `fly deploy` para construir y publicar.

Nota: Puedes usar también Railway para alojar la app y su Postgres gratis, pero sus cuotas free suelen agotarse rápido.

### Migraciones y datos

- La app corre `flask db upgrade` automáticamente al iniciar (ver `entrypoint.sh`).
- Para ejecutar comandos manuales en Koyeb/Fly, usa una shell/exec del proveedor y corre:

```bash
flask db migrate -m "tu_cambio" && flask db upgrade
```

### Variables de entorno mínimas en producción

- `FLASK_SECRET_KEY`: obligatorio (si falta, la app no arranca en producción).
- `DATABASE_URL`: obligatorio en los proveedores (Neon/Supabase/Railway).
- `PORT`: `5000` (algunos proveedores te la fijan automáticamente; respétala si es así).
- SMTP (opcional) si usarás recuperación de contraseña real.

### Endpoints útiles

- `GET /health` -> Responde `{"status": "ok"}` para health checks.
- App pública en `/` y resto de rutas.

### Bootstrap de usuario administrador

Para crear rápidamente un usuario admin en cualquier entorno (local, Koyeb, Fly, VPS):

1. Establece variables de entorno:

```powershell
$env:ADMIN_EMAIL="admin@tu-dominio.com"
$env:ADMIN_PASSWORD="UnaContraseñaSegura123"  # mínimo 6 caracteres
```

2. Ejecuta el script dentro del contenedor o entorno donde corre la app:

```powershell
python scripts/seed_admin.py
```

Con Docker Compose:

```powershell
docker compose exec web bash -c "export ADMIN_EMAIL=admin@tu-dominio.com ADMIN_PASSWORD=UnaContraseñaSegura123; python scripts/seed_admin.py"
```

El script no sobrescribe usuarios existentes; si ya hay un usuario con ese correo mostrará un mensaje y no hará cambios.

### Generar `FLASK_SECRET_KEY`

Puedes generar una clave aleatoria robusta con:

```powershell
python scripts/generate_secret.py
```

Luego toma la salida y ponla en `FLASK_SECRET_KEY` en tu panel de variables del proveedor.

## Notas
- El formulario POST a /enviar-respuesta renderiza una página de "gracias" con los datos.
- La imagen local se sirve desde la carpeta `img` original usando la ruta `/img/<archivo>`.
- Para mover imágenes a la convención de Flask, puedes copiarlas a `static/img/` y en las plantillas usar `{{ url_for('static', filename='img/archivo.jpg') }}`.
