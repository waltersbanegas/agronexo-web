import os
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

# --- MODELOS INTEGRADOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True) # Identidad Digital
    categoria = db.Column(db.String(50)) # Cría, Recría, Engorde
    raza = db.Column(db.String(50), default='Braford') #
    peso_actual = db.Column(db.Float, default=0.0) #
    estado_repro = db.Column(db.String(50), default='VACIA') #
    fecha_carencia = db.Column(db.DateTime) # Inocuidad
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
    tipo = db.Column(db.String(20)) # INGRESO/EGRESO
    monto = db.Column(db.Float)
    categoria = db.Column(db.String(50)) # Venta Hacienda, Insumos
    fecha = db.Column(db.DateTime, server_default=func.now())

class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    stock = db.Column(db.Float)
    unidad = db.Column(db.String(20))
    punto_reposicion = db.Column(db.Float) # Alerta automática

# --- ENDPOINTS ---
@app.route('/api/dashboard/full')
def dash():
    # Centraliza visión financiera y productiva
    ingresos = db.session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == 'INGRESO').scalar() or 0
    egresos = db.session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == 'EGRESO').scalar() or 0
    return jsonify({
        "financiero": {"caja": ingresos - egresos, "egresos": egresos},
        "operativo": {
            "animales": Animal.query.filter_by(activo=True).count(),
            "lotes": Lote.query.filter_by(activo=True).count(),
            "alertas": Insumo.query.filter(Insumo.stock <= Insumo.punto_reposicion).count()
        }
    })

@app.route('/api/reportes/consolidado')
def reporte():
    # Datos crudos para exportación Excel/PDF
    return jsonify({
        "fecha": str(datetime.now())[:16],
        "hacienda": [{"c": a.caravana, "p": a.peso_actual, "e": a.estado_repro} for a in Animal.query.filter_by(activo=True).all()],
        "finanzas": [{"f": str(t.fecha)[:10], "c": t.categoria, "m": t.monto} for t in Transaccion.query.all()]
    })

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    # Datos semilla para Los Frentones
    db.session.add(Insumo(nombre="Gasoil Grado 2", stock=1500, unidad="lts", punto_reposicion=300))
    db.session.add(Animal(caravana="BF-101", categoria="Vaca", raza="Braford", peso_actual=450))
    db.session.add(Lote(nombre="Lote Norte", cultivo="Soja", hectareas=100, condicion="Propio"))
    db.session.commit()
    return "AGRONEXO V8.0 DESPLEGADO CON ÉXITO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)