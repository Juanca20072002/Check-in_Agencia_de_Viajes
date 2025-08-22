from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# Configuración de la base de datos
POSTGRES_USER = "postgres"
POSTGRES_PW = "12345"
POSTGRES_DB = "reservasdb"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PW}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    mensaje = db.Column(db.Text, nullable=True)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viaje.id'), nullable=False)
    viaje = db.relationship('Viaje', backref=db.backref('reservas', lazy=True))

# Modelo para viajes
class Viaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.String(20), nullable=True)
    precio = db.Column(db.Numeric(10,2), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)  # nombre de archivo de la imagen

# Ruta para la página principal
@app.route("/")
def index():
    return render_template("index.html")

# Ruta para manejar el formulario
@app.route("/enviar-respuesta", methods=["POST"]) 
def enviar_respuesta():
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    experiencias = request.form.getlist("experiencia")

    if not nombre or not email:
        flash("Por favor completa nombre y correo.")
        return redirect(url_for("index"))

    return render_template("gracias.html", nombre=nombre, email=email, experiencias=experiencias)

# Servir archivos desde la carpeta 'img' existente en la raíz del proyecto
@app.route('/img/<path:filename>')
def img(filename):
    img_dir = os.path.join(app.root_path, 'img')
    return send_from_directory(img_dir, filename)


# CRUD de viajes
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'img')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/viajes")
def listar_viajes():
    viajes = Viaje.query.all()
    return render_template("viajes/listar.html", viajes=viajes)

@app.route("/viajes/nuevo", methods=["GET", "POST"])
def nuevo_viaje():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        fecha = request.form.get("fecha")
        precio = request.form.get("precio")
        imagen = request.files.get("imagen")
        imagen_filename = None
        if imagen and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.root_path, UPLOAD_FOLDER, filename))
            imagen_filename = filename
        viaje = Viaje(nombre=nombre, descripcion=descripcion, fecha=fecha, precio=precio, imagen=imagen_filename)
        db.session.add(viaje)
        db.session.commit()
        flash("Viaje creado exitosamente.")
        return redirect(url_for("viajes"))
    return render_template("viajes/nuevo.html")

@app.route("/viajes/<int:id>/editar", methods=["GET", "POST"])
def editar_viaje(id):
    viaje = Viaje.query.get_or_404(id)
    if request.method == "POST":
        viaje.nombre = request.form["nombre"]
        viaje.descripcion = request.form["descripcion"]
        viaje.fecha = request.form.get("fecha")
        viaje.precio = request.form.get("precio")
        imagen = request.files.get("imagen")
        if imagen and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.root_path, UPLOAD_FOLDER, filename))
            viaje.imagen = filename
        db.session.commit()
        flash("Viaje actualizado.")
        return redirect(url_for("viajes"))
    return render_template("viajes/editar.html", viaje=viaje)

@app.route("/viajes/<int:id>/eliminar", methods=["POST"])
def eliminar_viaje(id):
    viaje = Viaje.query.get_or_404(id)
    db.session.delete(viaje)
    db.session.commit()
    flash("Viaje eliminado.")
    return redirect(url_for("viajes"))

@app.route("/galeria")
def galeria():
    return render_template("galeria.html")

@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")

@app.route("/reservas")
def listar_reservas():
    reservas = Reserva.query.all()
    return render_template("reservas/listar.html", reservas=reservas)

@app.route("/reservas/nueva", methods=["GET", "POST"])
def nueva_reserva():
    viajes = Viaje.query.all()
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        viaje_id = request.form["viaje_id"]
        fecha = request.form["fecha"]
        mensaje = request.form.get("mensaje")
        reserva = Reserva(nombre=nombre, email=email, fecha=fecha, mensaje=mensaje, viaje_id=viaje_id)
        db.session.add(reserva)
        db.session.commit()
        flash("Reserva creada exitosamente.")
        return redirect(url_for("listar_reservas"))
    return render_template("reservas/nueva.html", viajes=viajes)

@app.route("/reservas/<int:id>/editar", methods=["GET", "POST"])
def editar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    viajes = Viaje.query.all()
    if request.method == "POST":
        reserva.nombre = request.form["nombre"]
        reserva.email = request.form["email"]
        reserva.viaje_id = request.form["viaje_id"]
        reserva.fecha = request.form["fecha"]
        reserva.mensaje = request.form.get("mensaje")
        db.session.commit()
        flash("Reserva actualizada.")
        return redirect(url_for("listar_reservas"))
    return render_template("reservas/editar.html", reserva=reserva, viajes=viajes)

@app.route("/reservas/<int:id>/eliminar", methods=["POST"])
def eliminar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    db.session.delete(reserva)
    db.session.commit()
    flash("Reserva eliminada.")
    return redirect(url_for("listar_reservas"))

@app.route("/viajes/<int:id>")
def detalle_viaje(id):
    viaje = Viaje.query.get_or_404(id)
    return render_template("viajes/detalle.html", viaje=viaje)

@app.route("/prueba")
def prueba():
    return render_template("prueba.html")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Permite ejecutar directamente con: python app.py
    app.run(debug=True)
