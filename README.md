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

## Notas
- El formulario POST a /enviar-respuesta renderiza una página de "gracias" con los datos.
- La imagen local se sirve desde la carpeta `img` original usando la ruta `/img/<archivo>`.
- Para mover imágenes a la convención de Flask, puedes copiarlas a `static/img/` y en las plantillas usar `{{ url_for('static', filename='img/archivo.jpg') }}`.
