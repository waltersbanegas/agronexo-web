import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_v11.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True)
    raza = db.Column(db.String(50), default='Braford')
    peso = db.Column(db.Float)
    estado = db.Column(db.String(50)) 
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    hectareas = db.Column(db.Float)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mm = db.Column(db.Float)
    fecha = db.Column(db.DateTime, server_default=func.now())

class Finanzas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float)
    tipo = db.Column(db.String(20)) 
    concepto = db.Column(db.String(100))

# --- ENDPOINTS ---
@app.route('/api/resumen')
def resumen():
    # Centraliza los datos del Dashboard
    return jsonify({
        "hacienda": Animal.query.count(),
        "lotes": Lote.query.count(),
        "lluvias": db.session.query(func.sum(Lluvia.mm)).scalar() or 0,
        "caja": (db.session.query(func.sum(Finanzas.monto)).filter(Finanzas.tipo=='INGRESO').scalar() or 0) - 
                (db.session.query(func.sum(Finanzas.monto)).filter(Finanzas.tipo=='EGRESO').scalar() or 0)
    })

@app.route('/api/ganaderia', methods=['GET'])
def get_ganaderia():
    return jsonify([{"caravana":a.caravana, "raza":a.raza, "peso":a.peso, "estado":a.estado} for a in Animal.query.all()])

@app.route('/api/lotes', methods=['GET'])
def get_lotes():
    return jsonify([{"nombre":l.nombre, "cultivo":l.cultivo, "has":l.hectareas} for l in Lote.query.all()])

@app.route('/api/lluvias', methods=['GET'])
def get_lluvias():
    return jsonify([{"fecha": str(l.fecha)[:10], "mm": l.mm} for l in Lluvia.query.all()])

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    # Datos iniciales para que la app no arranque vacía
    db.session.add(Lote(nombre="Lote Norte", cultivo="Soja", hectareas=120))
    db.session.add(Animal(caravana="RP-101", raza="Braford", peso=450, estado="PREÑADA", lat=-26.42, lng=-61.41))
    db.session.add(Lluvia(mm=15))
    db.session.commit()
    return "SISTEMA V11 REINICIADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)