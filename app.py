import os
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app) # Permite que el frontend hable con el backend

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True)
    categoria = db.Column(db.String(50))
    estado = db.Column(db.String(50))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    hectareas = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

# --- RUTAS DE EMERGENCIA ---
@app.route('/')
def home():
    return "Backend Operativo v5.0"

@app.route('/reset')
def reset_db():
    try:
        db.drop_all()
        db.create_all()
        # Datos prueba
        db.session.add(Lote(nombre="Lote 1", cultivo="Soja", hectareas=100))
        for i in range(10):
            db.session.add(Animal(caravana=f"V-{i}", categoria="Vaca", estado="PREÑADA", lat=-26.7, lng=-60.8))
        db.session.commit()
        return "¡RESET EXITOSO! Base de datos regenerada."
    except Exception as e:
        return f"Error: {e}"

# --- API ---
@app.route('/api/resumen')
def resumen():
    return jsonify({
        "animales": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.filter_by(activo=True).count(),
        "finanzas": {"gastos": 0, "margen": 0}
    })

@app.route('/api/ganaderia')
def ganaderia():
    return jsonify([{"caravana": a.caravana, "categoria": a.categoria, "estado": a.estado} for a in Animal.query.all()])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=10000)