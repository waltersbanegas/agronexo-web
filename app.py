import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_master_v4.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELO INTEGRAL
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    raza = db.Column(db.String(50))
    sexo = db.Column(db.String(10))
    edad = db.Column(db.Integer)
    estado = db.Column(db.String(50))
    madre = db.Column(db.String(100))
    padre = db.Column(db.String(100))
    codigo = db.Column(db.String(50))
    observaciones = db.Column(db.Text)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    has = db.Column(db.Float)
    geometria = db.Column(db.Text, nullable=True)

# --- ENDPOINTS ---
@app.route('/api/animales', methods=['GET', 'POST'])
def handle_animales():
    if request.method == 'POST':
        d = request.json
        # Guardado profesional con todos los campos
        nuevo = Animal(nombre=d['nombre'], raza=d['raza'], sexo=d['sexo'], edad=d['edad'], 
                       estado=d['estado'], madre=d['madre'], padre=d['padre'], 
                       codigo=d['codigo'], observaciones=d['obs'])
        db.session.add(nuevo); db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"nombre": a.nombre, "raza": a.raza, "estado": a.estado} for a in Animal.query.all()])

@app.route('/api/lotes', methods=['GET', 'POST'])
def handle_lotes():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], has=d['has'], geometria=d.get('geometria')))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"nombre": l.nombre, "cultivo": l.cultivo, "has": l.has} for l in Lote.query.all()])

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA V4 REESTABLECIDO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)