from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///citas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Modelo de usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)

# Modelo de cita
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
    archivos = db.Column(db.String(100), nullable=True)
    comentario = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para el panel de citas
@app.route("/panel")
def panel():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    return render_template("panel.html")

# Función para eliminar una cita
@app.route('/eliminar_cita/<int:cita_id>', methods=['POST'])
def eliminar_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    if cita.archivos:
        archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], cita.archivos)
        if os.path.exists(archivo_path):
            os.remove(archivo_path)
    db.session.delete(cita)
    db.session.commit()
    flash('Cita eliminada correctamente.', 'success')
    return redirect(url_for('panel'))

# Función para mostrar el formulario de nueva cita
@app.route('/nueva-cita', methods=['GET', 'POST'])
def nueva_cita():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        zona = request.form['zona']
        tamano = request.form['tamano']
        fecha = request.form['fecha'] if request.form['fecha'] else None
        dias = request.form['dias']
        horario = request.form['horario']
        precio = float(request.form['precio'])
        senal = float(request.form['senal'])
        comentario = request.form['comentario']
        
        archivo = request.files.get('archivo')
        archivo_nombre = None
        if archivo:
            archivo_nombre = archivo.filename
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo_nombre))
        
        nueva_cita = Cita(nombre=nombre, contacto=contacto, zona=zona, tamano=tamano, 
                          fecha=datetime.strptime(fecha, '%Y-%m-%d') if fecha else None, 
                          dias=dias, horario=horario, precio=precio, senal=senal, 
                          archivos=archivo_nombre, comentario=comentario)
        db.session.add(nueva_cita)
        db.session.commit()
        flash('Cita registrada correctamente.', 'success')
        return redirect(url_for('panel'))
    
    return render_template('formulario_cita.html')

# Función de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario and check_password_hash(usuario.contrasena, contrasena):
            session['usuario_id'] = usuario.id
            return redirect(url_for('panel'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('login.html')

# Función de cierre de sesión
@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('index'))

# Ruta para la galería
@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

#Ruta ver disponibles
@app.route('/disponibles')
def ver_disponibles():
    carpeta = os.path.join('static', 'uploads_disponibles')
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    imagenes = [img for img in os.listdir(carpeta) if img.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    return render_template('disponibles.html', imagenes=imagenes)


# Ruta registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        # Verifica si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('Este correo ya está registrado.', 'danger')
            return redirect(url_for('registro'))

        # Crear nuevo usuario
        contrasena_hash = generate_password_hash(contrasena)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, contrasena=contrasena_hash)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

#Ruta ofertas
@app.route('/ofertas')
def ofertas():
    return render_template('ofertas.html')

# Ruta sobre mí
@app.route('/sobre-mi')
def sobre_mi():
    return render_template('sobre_mi.html')

if __name__ == '__main__':
    app.run(debug=True)
