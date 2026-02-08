import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_v11.db')
db = SQLAlchemy(app)

# --- MODELOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True)
    raza = db.Column(db.String(50), default='Braford')
    peso = db.Column(db.Float)
    estado = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    hectareas = db.Column(db.Float)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mm = db.Column(db.Float)
    fecha = db.Column(db.DateTime, server_default=func.now())

# --- RUTAS DE CARGA (POST) ---
@app.route('/api/ganaderia', methods=['GET', 'POST'])
def ganaderia():
    if request.method == 'POST':
        d = request.json
        db.session.add(Animal(caravana=d['caravana'], peso=d['peso'], estado=d['estado']))
        db.session.commit()
        return jsonify({"msg": "ok"})
    return jsonify([{"caravana":a.caravana, "peso":a.peso, "estado":a.estado} for a in Animal.query.all()])

@app.route('/api/lotes', methods=['GET', 'POST'])
def lotes():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], hectareas=d['has']))
        db.session.commit()
        return jsonify({"msg": "ok"})
    return jsonify([{"nombre":l.nombre, "cultivo":l.cultivo, "has":l.hectareas} for l in Lote.query.all()])

@app.route('/api/lluvias', methods=['GET', 'POST'])
def lluvias():
    if request.method == 'POST':
        db.session.add(Lluvia(mm=request.json['mm']))
        db.session.commit()
        return jsonify({"msg": "ok"})
    return jsonify([{"fecha": str(l.fecha)[:10], "mm": l.mm} for l in Lluvia.query.all()])

@app.route('/api/resumen')
def resumen():
    return jsonify({
        "hacienda": Animal.query.count(),
        "lotes": Lote.query.count(),
        "lluvias": db.session.query(func.sum(Lluvia.mm)).scalar() or 0
    })

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)