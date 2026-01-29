import os
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_final.db')
db = SQLAlchemy(app)

# --- MODELOS INTEGRADOS (ADMIN + CAMPO) ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True) # ID Digital
    categoria = db.Column(db.String(50)) # Cría, Recría, Engorde
    raza = db.Column(db.String(50), default='Braford') #
    peso = db.Column(db.Float, default=0.0) #
    estado = db.Column(db.String(50), default='VACIA') #
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    hectareas = db.Column(db.Float)
    condicion = db.Column(db.String(50)) # Propio/Alquilado
    activo = db.Column(db.Boolean, default=True)

class Transaccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20)) # INGRESO / EGRESO
    monto = db.Column(db.Float)
    categoria = db.Column(db.String(50)) # Venta Hacienda, Insumos
    fecha = db.Column(db.DateTime, server_default=func.now())

# --- RUTAS DE GESTIÓN ---
@app.route('/api/dashboard')
def dashboard():
    # Centraliza visión financiera y operativa
    ingresos = db.session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == 'INGRESO').scalar() or 0
    egresos = db.session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == 'EGRESO').scalar() or 0
    return jsonify({
        "finanzas": {"caja": ingresos - egresos, "egresos": egresos},
        "produccion": {
            "animales": Animal.query.filter_by(activo=True).count(),
            "lotes": Lote.query.filter_by(activo=True).count()
        }
    })

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    # Semilla para Los Frentones
    db.session.add(Lote(nombre="Lote Norte", cultivo="Soja", hectareas=100, condicion="Propio"))
    for i in range(1, 11):
        db.session.add(Animal(caravana=f"BF-{100+i}", categoria="Vaca", peso=450, lat=-26.42+(i/1000), lng=-61.41+(i/1000)))
    db.session.commit()
    return "SISTEMA INTEGRADO V9 ONLINE"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)