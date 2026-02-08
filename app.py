import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_final.db')
db = SQLAlchemy(app)

# MODELOS
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True)
    peso = db.Column(db.Float)
    estado = db.Column(db.String(50))

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    has = db.Column(db.Float)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mm = db.Column(db.Float)
    fecha = db.Column(db.String(20))

# RUTAS DE CARGA (POST)
@app.route('/api/ganaderia', methods=['POST'])
def add_animal():
    d = request.json
    db.session.add(Animal(caravana=d['caravana'], peso=d['peso'], estado=d['estado']))
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/api/lotes', methods=['POST'])
def add_lote():
    d = request.json
    db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], has=d['has']))
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/api/lluvias', methods=['POST'])
def add_lluvia():
    d = request.json
    db.session.add(Lluvia(mm=d['mm'], fecha=d['fecha']))
    db.session.commit()
    return jsonify({"status": "ok"})

# RUTAS DE CONSULTA (GET)
@app.route('/api/ganaderia', methods=['GET'])
def get_animals():
    return jsonify([{"caravana": a.caravana, "peso": a.peso, "estado": a.estado} for a in Animal.query.all()])

@app.route('/api/lotes', methods=['GET'])
def get_lotes():
    return jsonify([{"nombre": l.nombre, "cultivo": l.cultivo, "has": l.has} for l in Lote.query.all()])

@app.route('/api/lluvias', methods=['GET'])
def get_lluvias():
    return jsonify([{"mm": l.mm, "fecha": l.fecha} for l in Lluvia.query.all()])

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)