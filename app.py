import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_v11.db')
db = SQLAlchemy(app)

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

@app.route('/api/resumen')
def resumen():
    return jsonify({
        "hacienda": Animal.query.count(),
        "lotes": Lote.query.count(),
        "lluvias": db.session.query(db.func.sum(Lluvia.mm)).scalar() or 0
    })

@app.route('/api/ganaderia', methods=['GET', 'POST'])
def handle_ganaderia():
    if request.method == 'POST':
        d = request.json
        db.session.add(Animal(caravana=d['caravana'], peso=d['peso'], estado=d['estado']))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"caravana": a.caravana, "peso": a.weight, "estado": a.estado} for a in Animal.query.all()])

@app.route('/api/lotes', methods=['GET', 'POST'])
def handle_lotes():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], has=d['has']))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"nombre": l.nombre, "cultivo": l.cultivo, "has": l.has} for l in Lote.query.all()])

@app.route('/api/lluvias', methods=['GET', 'POST'])
def handle_lluvias():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lluvia(mm=d['mm'], fecha=d['fecha']))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"mm": l.mm, "fecha": l.fecha} for l in Lluvia.query.all()])

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA V11.5 REINICIADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)