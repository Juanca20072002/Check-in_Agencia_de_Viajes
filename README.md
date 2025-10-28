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

## Notas
- El formulario POST a /enviar-respuesta renderiza una página de "gracias" con los datos.
- La imagen local se sirve desde la carpeta `img` original usando la ruta `/img/<archivo>`.
- Para mover imágenes a la convención de Flask, puedes copiarlas a `static/img/` y en las plantillas usar `{{ url_for('static', filename='img/archivo.jpg') }}`.
