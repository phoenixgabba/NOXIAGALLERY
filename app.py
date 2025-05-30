from flask import Flask, render_template, request, redirect, url_for, session, flash 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText  # Importar MIMEText

# Configuración principal
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_secreta_segura')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///citas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'noxiagallery@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'kjkthihkpsahasvj')  # Usa un secreto real en producción

mail = Mail(app)
db = SQLAlchemy(app)

# ------------------------- MODELOS -------------------------

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)
    verificado = db.Column(db.Boolean, default=False)

class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100), nullable=False)
    zona = db.Column(db.String(100), nullable=False)
    tamano = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, nullable=True)
    dias = db.Column(db.String(100), nullable=False)
    horario = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    senal = db.Column(db.Float, nullable=False)
    archivos = db.Column(db.String(300), nullable=True)  # Se admiten múltiples archivos
    comentario = db.Column(db.String(500), nullable=True)

with app.app_context():
    db.create_all()

# ---------------------- FUNCIONES CORREO ----------------------

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=expiration)
    except Exception:
        return None
    return email

def send_verification_email(user_email, user_name, token):
    msg = Message('Bienvenido a NOXIA Gallery - Verifica tu correo',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user_email])

    # Enlace para verificar el correo
    link = url_for('verify_email', token=token, _external=True)
    
    # Cuerpo del mensaje HTML con las imágenes incrustadas
    html = f"""
    <div style='font-family: Arial, sans-serif; color: #eee; background-color: #111; padding: 30px;'>
        <div style='text-align: center;'>
            <img src="cid:logo" alt="NOXIA GALLERY" style="width: 100%; max-width: 600px; border-radius: 10px;">
        </div>
        <h2 style='color: gold; text-align: center;'>¡Bienvenid@ a NOXIA GALLERY, {user_name}!</h2>
        <p style='text-align: center;'>Tu espacio exclusivo para diseños únicos y experiencias inolvidables en tatuaje.</p>
        <div style='text-align: center; margin: 40px 0;'>
            <a href='{link}' style='background: gold; color: black; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;'>CONFIRMAR MI CUENTA</a>
        </div>
        <h3 style='color: gold;'>🎁 Tatuajes flash en oferta esta semana:</h3>
        <div style='display: flex; gap: 20px; justify-content: center;'>
            <img src="cid:oferta1" alt='Flash 1' style='width: 48%; border-radius: 10px;'>
            <img src="cid:oferta2" alt='Flash 2' style='width: 48%; border-radius: 10px;'>
        </div>
        <p style='text-align: center; margin-top: 40px;'>Gracias por unirte. Te esperamos para crear arte juntos.<br> - El equipo de NOXIA</p>
    </div>
    """

    msg.html = html

    # Adjuntamos las imágenes
    with open('static/images/logo.png', 'rb') as f:
        logo_image = MIMEImage(f.read())
        logo_image.add_header('Content-ID', '<logo>')
        msg.attach(logo_image)

    with open('static/images/oferta1.jpg', 'rb') as f:
        oferta1_image = MIMEImage(f.read())
        oferta1_image.add_header('Content-ID', '<oferta1>')
        msg.attach(oferta1_image)

    with open('static/images/oferta2.jpg', 'rb') as f:
        oferta2_image = MIMEImage(f.read())
        oferta2_image.add_header('Content-ID', '<oferta2>')
        msg.attach(oferta2_image)

    mail.send(msg)

# ------------------------ RUTAS ------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/panel')
def panel():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    usuario = Usuario.query.get(session['usuario_id'])
    if usuario and not usuario.verificado:
        flash('Por favor, verifica tu correo electrónico para activar tu cuenta.', 'warning')
        return redirect(url_for('login'))
    citas = Cita.query.all()
    return render_template("panel.html", citas=citas)

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('index'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        if Usuario.query.filter_by(correo=correo).first():
            flash('Este correo ya está registrado.', 'danger')
            return redirect(url_for('registro'))

        contrasena_hash = generate_password_hash(contrasena)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, contrasena=contrasena_hash)
        db.session.add(nuevo_usuario)
        db.session.commit()

        token = generate_verification_token(correo)
        send_verification_email(correo, nombre, token)

        flash('Registro exitoso. Revisa tu correo para verificar tu cuenta.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario and check_password_hash(usuario.contrasena, contrasena):
            if not usuario.verificado:
                flash('Por favor, verifica tu correo electrónico para activar tu cuenta.', 'warning')
                return redirect(url_for('login'))
            session['usuario_id'] = usuario.id
            return redirect(url_for('panel'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/verify/<token>')
def verify_email(token):
    email = confirm_verification_token(token)
    if email:
        usuario = Usuario.query.filter_by(correo=email).first()
        if usuario and not usuario.verificado:
            usuario.verificado = True
            db.session.commit()
            flash('Tu correo ha sido verificado exitosamente. Ahora puedes iniciar sesión.', 'success')
        else:
            flash('Este enlace de verificación ya ha sido usado o es inválido.', 'danger')
    else:
        flash('El enlace de verificación ha expirado o es inválido.', 'danger')
    return redirect(url_for('login'))

@app.route('/sobre_mi')
def sobre_mi():
    return render_template('sobre_mi.html')

@app.route('/galeria')
def galeria():
    # Aquí podrías cargar imágenes de la galería o algún contenido relacionado
    return render_template('galeria.html')

@app.route('/nueva-cita', methods=['GET', 'POST'])
def nueva_cita():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        zona = request.form['zona']
        tamano = request.form['tamano']
        fecha = request.form.get('fecha')
        dias = request.form['dias']
        horario = request.form['horario']
        precio = float(request.form['precio'])
        senal = float(request.form['senal'])
        comentario = request.form['comentario']

        archivos_guardados = []
        for archivo in request.files.getlist('archivo'):
            if archivo:
                nombre_archivo = archivo.filename
                ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                archivo.save(ruta_guardado)
                archivos_guardados.append(nombre_archivo)

        nueva_cita = Cita(
            nombre=nombre,
            contacto=contacto,
            zona=zona,
            tamano=tamano,
            fecha=datetime.strptime(fecha, '%Y-%m-%d') if fecha else None,
            dias=dias,
            horario=horario,
            precio=precio,
            senal=senal,
            archivos=",".join(archivos_guardados),
            comentario=comentario
        )

        db.session.add(nueva_cita)
        db.session.commit()
        flash('Cita registrada correctamente.', 'success')
        return redirect(url_for('panel'))

    return render_template('nueva_cita.html')

if __name__ == '__main__':
    app.run(debug=True)
