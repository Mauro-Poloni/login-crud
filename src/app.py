from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from config import config
# Entities:
from models.entities.User import User
# Models:
from models.ModelUser import ModelUser
# Permitirle a Flask acceder a carpetas
from flask import send_from_directory
# importar fotos
from datetime import datetime
# Poder borrar y actualizar foto
import os

# Vinculacion con FLASK
app = Flask(__name__)

# Login

csrf = CSRFProtect()
db = MySQL(app)

# Referencia a carpeta de fotos

CARPETA = os.path.join("uploads")
app.config['CARPETA'] = CARPETA

# Mostrar fotos en el index

@app.route('/uploads/<nombreFoto>')
def uploads(nombreFoto):
    return send_from_directory(app.config['CARPETA'], nombreFoto)

login_manager_app = LoginManager(app)


@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print(request.form['username'])
        print(request.form['password'])
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Invalid password...")
                return render_template('auth/login.html')
        else:
            flash("User not found...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# Crud



# Mostrar datos : Show

@app.route('/home')
@login_required
def home():
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM `productos`")
    productos = cursor.fetchall()
    db.connection.commit()
    cursor.close()

    return render_template('crud/index.html', productos = productos)

# Eliminar datos

@app.route('/home/destroy/<string:id>', methods = ['GET'])
@login_required
def destroy(id):

    cursor = db.connection.cursor()

    # Borrar foto al eliminar

    cursor.execute("SELECT foto FROM productos WHERE id = %s", (id))
    fila = cursor.fetchall()
    os.remove(os.path.join("src/uploads", fila[0][0]))
    cursor.execute("DELETE FROM productos WHERE id=%s",(id))
    db.connection.commit()
    return redirect("/home")

# Editar datos

@app.route('/home/edit/<string:id>', methods = ['GET'])
@login_required
def edit(id):

    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = %s", (id))
    productos = cursor.fetchall()
    db.connection.commit()
    return render_template('crud/edit.html', productos = productos)

# Actualizar datos

@app.route('/update', methods=['POST'])
@login_required
def update():
    # Guardar en variables los datos del form
    _nombre = request.form['txtNombre']
    _precio = request.form['txtPrecio']
    _foto = request.files['txtFoto']
    id = request.form['txtID']

    # Modifico solo nombre y precio
    cursor = db.connection.cursor()
    cursor.execute("UPDATE `productos` SET `nombre` = %s,`precio` = %s WHERE id = %s;", (_nombre, _precio, id))

    # Traer datos del form

    datos = (_nombre,_precio,id)

        # Modificar foto para poder actualizarla #

    now = datetime.now()
    tiempo = now.strftime("%Y%H%M%S")
    if _foto.filename != '' :
        nuevoNombreFoto = tiempo + _foto.filename
        _foto.save("src/uploads/" + nuevoNombreFoto)

    # Traer esa foto

    cursor.execute("SELECT foto FROM productos WHERE id = %s", id)
    fila = cursor.fetchall()

    # Remover la foto

    os.remove(os.path.join('src/uploads', fila[0][0]))

    # actualizar con nueva foto
    cursor.execute("UPDATE productos SET foto = %s WHERE id = %s", (nuevoNombreFoto, id))

    # Ejecutar actualizacion completa de datos
    db.connection.commit()
    
    return redirect('/home')

# Crear datos del CRUD

@app.route('/home/create')
@login_required

def create():
    return render_template('crud/create.html')

# Guardar los datos del crud
# txtNombre - txtPrecio - txtFoto

@app.route('/store', methods=['POST'])
@login_required
def storage():

    # Guardar en variables los datos del form
    _nombre = request.form['txtNombre']
    _precio = request.form['txtPrecio']
    _foto = request.files['txtFoto']

    # Validaciones

    if _nombre == '' or _precio == '' or _foto == '' :
        flash('recuerda llenar los datos de los campos')
        return redirect(url_for('create'))

    # Guardar fotos en la carpeta uploads

    now = datetime.now()
    tiempo = now.strftime("%Y%H%M%S")

    if _foto.filename != '' :
        nuevoNombreFoto = tiempo + _foto.filename
        _foto.save("src/uploads/" + nuevoNombreFoto)

    # Consulta de insertar
    cur = db.connection.cursor()
    cur.execute("INSERT INTO `productos` (`id`, `nombre`, `precio`, `foto`) VALUES (NULL, %s, %s, %s)", (_nombre, _precio, nuevoNombreFoto))
    db.connection.commit()

    return redirect('/home')


@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()





