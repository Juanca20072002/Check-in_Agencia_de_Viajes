#!/usr/bin/env python
import os
import sys

# Asegura que el directorio raíz del repo esté en sys.path para poder importar app.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app import app, db, Usuario

username = os.environ.get("ADMIN_EMAIL") or os.environ.get("ADMIN_USERNAME")
password = os.environ.get("ADMIN_PASSWORD")
if not username or not password:
    print("Define ADMIN_EMAIL (o ADMIN_USERNAME) y ADMIN_PASSWORD antes de ejecutar.")
    sys.exit(1)

with app.app_context():
    existing = Usuario.query.filter_by(username=username).first()
    if existing:
        print("El usuario ya existe (rol: {} ).".format(existing.rol))
    else:
        admin = Usuario(username=username, rol='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado: {}".format(username))
