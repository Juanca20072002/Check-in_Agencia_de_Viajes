from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from functools import wraps
from flask import abort
from flask_login import current_user
from flask_migrate import Migrate
import os
import smtplib
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# Configuración de la base de datos
# Usa variables de entorno para la base de datos
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PW = os.environ.get("POSTGRES_PW", "12345")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "reservasdb")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PW}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])  # <-- Agrega esta línea aquí
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configuración de correo (Gmail)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")  # tu correo gmail
SMTP_PASS = os.environ.get("SMTP_PASS", "")  # App Password de Gmail

# Serializer para tokens de recuperación
RESET_TOKEN_SALT = os.environ.get("RESET_TOKEN_SALT", "reset-password-salt")

def _get_serializer():
    return URLSafeTimedSerializer(app.secret_key)

def send_reset_email(usuario, reset_url):
    if not SMTP_USER or not SMTP_PASS:
        # Si no hay credenciales configuradas, no intentamos enviar
        print("SMTP_USER/SMTP_PASS no configurados; omitiendo envío de correo.")
        return False
    msg = EmailMessage()
    msg["Subject"] = "Restablecer tu contraseña"
    msg["From"] = SMTP_USER
    # Usamos username como email registrado
    msg["To"] = usuario.username
    texto = (
        f"Hola,\n\nPara restablecer tu contraseña, haz clic en el siguiente enlace:\n{reset_url}\n\n"
        "Si no solicitaste este cambio, ignora este correo.\n"
    )
    html = f"""
    <p>Hola,</p>
    <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
    <p><a href="{reset_url}">Restablecer contraseña</a></p>
    <p>Si no solicitaste este cambio, ignora este correo.</p>
    """
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Error enviando correo:", e)
        return False

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    mensaje = db.Column(db.Text, nullable=True)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viaje.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    viaje = db.relationship('Viaje', backref=db.backref('reservas', lazy=True))
    usuario = db.relationship('Usuario', backref='reservas')

# Modelo para viajes
class Viaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.String(20), nullable=True)
    precio = db.Column(db.Numeric(10,2), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)  # nombre de archivo de la imagen

# models.py o en tu app.py si tienes todo junto
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='usuario')  # 'usuario' o 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/viajes/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo_viaje():
    # solo admin
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
        return redirect(url_for("listar_viajes"))
    return render_template("viajes/nuevo.html")

@app.route("/viajes/<int:id>/editar", methods=["GET", "POST"])
@admin_required
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
        return redirect(url_for("listar_viajes"))
    return render_template("viajes/editar.html", viaje=viaje)

@app.route("/viajes/<int:id>/eliminar", methods=["POST"])
@admin_required
def eliminar_viaje(id):
    viaje = Viaje.query.get_or_404(id)
    db.session.delete(viaje)
    db.session.commit()
    flash("Viaje eliminado.")
    return redirect(url_for("listar_viajes"))

@app.route("/galeria")
def galeria():
    return render_template("galeria.html")

@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")

@app.route("/reservas")
@login_required
def listar_reservas():
    if current_user.rol == 'admin':
        reservas = Reserva.query.all()
    else:
        reservas = Reserva.query.filter_by(usuario_id=current_user.id).all()
    return render_template('reservas/listar.html', reservas=reservas)

@app.route('/reservas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_reserva():
    # solo usuario autenticado
    LIMITE_RESERVAS_POR_USUARIO = 7

    # Chequeo de límite antes de mostrar el formulario
    total_usuario = Reserva.query.filter_by(usuario_id=current_user.id).count()
    if total_usuario >= LIMITE_RESERVAS_POR_USUARIO:
        flash(f"Has alcanzado el límite de {LIMITE_RESERVAS_POR_USUARIO} reservas. Cancela alguna para crear una nueva.")
        return redirect(url_for("listar_reservas"))

    viajes = Viaje.query.all()
    if request.method == "POST":
        # Revalidar por seguridad antes de insertar
        total_usuario = Reserva.query.filter_by(usuario_id=current_user.id).count()
        if total_usuario >= LIMITE_RESERVAS_POR_USUARIO:
            flash(f"Has alcanzado el límite de {LIMITE_RESERVAS_POR_USUARIO} reservas. Cancela alguna para crear una nueva.")
            return redirect(url_for("listar_reservas"))

        nombre = request.form["nombre"]
        email = request.form["email"]
        viaje_id = int(request.form["viaje_id"])  # asegurar tipo entero para comparar
        fecha = request.form["fecha"]
        mensaje = request.form.get("mensaje")

        # Validación: el usuario no puede tener 2 reservas en la misma fecha
        duplicada = Reserva.query.filter_by(usuario_id=current_user.id, fecha=fecha).first()
        if duplicada:
            flash("Ya tienes una reserva para esa fecha. Elige otra fecha o edita la existente.")
            return redirect(url_for("listar_reservas"))

        # Validación adicional: mismo viaje en la misma fecha
        mismo_viaje_misma_fecha = Reserva.query.filter_by(
            usuario_id=current_user.id, viaje_id=viaje_id, fecha=fecha
        ).first()
        if mismo_viaje_misma_fecha:
            flash("Ya tienes una reserva para ese mismo viaje en esa fecha.")
            return redirect(url_for("listar_reservas"))
        reserva = Reserva(
            nombre=nombre,
            email=email,
            fecha=fecha,
            mensaje=mensaje,
            viaje_id=viaje_id,
            usuario_id=current_user.id
        )
        db.session.add(reserva)
        db.session.commit()
        flash("Reserva creada exitosamente.")
        return redirect(url_for("listar_reservas"))
    return render_template("reservas/nueva.html", viajes=viajes)

@app.route("/reservas/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    if reserva.usuario_id != current_user.id and current_user.rol != 'admin':
        abort(403)
    viajes = Viaje.query.all()
    if request.method == "POST":
        nuevo_nombre = request.form["nombre"]
        nuevo_email = request.form["email"]
        nuevo_viaje_id = int(request.form["viaje_id"])  # asegurar entero
        nueva_fecha = request.form["fecha"]
        nuevo_mensaje = request.form.get("mensaje")

        # Validación: evitar duplicar fecha con otra reserva del mismo usuario
        conflicto = (Reserva.query
                     .filter(Reserva.usuario_id == reserva.usuario_id,
                             Reserva.fecha == nueva_fecha,
                             Reserva.id != reserva.id)
                     .first())
        if conflicto:
            flash("Ya existe otra reserva tuya para esa fecha. Usa una fecha distinta.")
            return redirect(url_for("editar_reserva", id=reserva.id))

        # Validación adicional: mismo viaje + misma fecha en otra reserva
        conflicto_viaje_fecha = (Reserva.query
                                 .filter(Reserva.usuario_id == reserva.usuario_id,
                                         Reserva.viaje_id == nuevo_viaje_id,
                                         Reserva.fecha == nueva_fecha,
                                         Reserva.id != reserva.id)
                                 .first())
        if conflicto_viaje_fecha:
            flash("Ya tienes otra reserva para ese mismo viaje en esa fecha.")
            return redirect(url_for("editar_reserva", id=reserva.id))

        reserva.nombre = nuevo_nombre
        reserva.email = nuevo_email
        reserva.viaje_id = nuevo_viaje_id
        reserva.fecha = nueva_fecha
        reserva.mensaje = nuevo_mensaje
        db.session.commit()
        flash("Reserva actualizada.")
        return redirect(url_for("listar_reservas"))
    return render_template("reservas/editar.html", reserva=reserva, viajes=viajes)

@app.route("/reservas/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    if reserva.usuario_id != current_user.id and current_user.rol != 'admin':
        abort(403)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(username=request.form['username']).first()
        if usuario and usuario.check_password(request.form['password']):
            login_user(usuario)
            flash('Bienvenido, {}'.format(usuario.username))
            return redirect(url_for('dashboard' if usuario.rol == 'admin' else 'index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada')
    return redirect(url_for('index'))

@app.route('/dashboard')
@admin_required
def dashboard():
    total_viajes = Viaje.query.count()
    total_reservas = Reserva.query.count()
    total_usuarios = Usuario.query.count()
    ultimas_reservas = Reserva.query.order_by(Reserva.id.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_viajes=total_viajes,
                           total_reservas=total_reservas,
                           total_usuarios=total_usuarios,
                           ultimas_reservas=ultimas_reservas)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validaciones básicas
        if not username or not email or not password or not confirm_password:
            flash('Por favor completa todos los campos.')
            return render_template('register.html')
        if password != confirm_password:
            flash('Las contraseñas no coinciden.')
            return render_template('register.html')
        if Usuario.query.filter_by(username=username).first():
            flash('El usuario ya existe.')
            return render_template('register.html')

        # Crear usuario
        nuevo_usuario = Usuario(username=username, rol='usuario')
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        # En este sistema, el username es el correo registrado
        usuario = Usuario.query.filter_by(username=email).first()
        if usuario:
            s = _get_serializer()
            token = s.dumps({"uid": usuario.id}, salt=RESET_TOKEN_SALT)
            reset_url = url_for('reset_password', token=token, _external=True)
            send_reset_email(usuario, reset_url)
    # Mensaje flash neutro para no revelar si el correo existe o no
    flash('Si tu correo está registrado, te enviamos un enlace para restablecer tu contraseña.')
    # Mensaje/página genérica para no revelar existencia del correo
    return redirect(url_for('forgot_password_sent'))
    # GET: mostrar formulario para digitar correo
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = _get_serializer()
    try:
        data = s.loads(token, max_age=3600, salt=RESET_TOKEN_SALT)  # 1 hora
        user_id = data.get('uid')
    except (BadSignature, SignatureExpired):
        flash('El enlace de restablecimiento no es válido o ha expirado.')
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(user_id)
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not password or not confirm:
            flash('Completa ambos campos.')
            return render_template('reset_password.html')
        if password != confirm:
            flash('Las contraseñas no coinciden.')
            return render_template('reset_password.html')
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.')
            return render_template('reset_password.html')
        usuario.set_password(password)
        db.session.commit()
        flash('Tu contraseña ha sido restablecida. Ahora puedes iniciar sesión.')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/forgot-password/sent')
def forgot_password_sent():
    # Página simple de confirmación
    return render_template('forgot_password_sent.html')

@app.route('/usuarios')
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@app.route('/admin/viajes/<int:id>')
@admin_required
def admin_detalle_viaje(id):
    viaje = Viaje.query.get_or_404(id)
    return render_template('admin/viajes/detalle.html', viaje=viaje)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
