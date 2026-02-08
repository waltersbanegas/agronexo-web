import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_final_pro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELOS DE DATOS
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

# --- ENDPOINTS DE CONSULTA Y CARGA ---
@app.route('/api/resumen')
def resumen():
    return jsonify({
        "hacienda": Animal.query.count(),
        "lotes": Lote.query.count(),
        "lluvias": db.session.query(func.sum(Lluvia.mm)).scalar() or 0
    })

@app.route('/api/ganaderia', methods=['GET', 'POST'])
def handle_ganaderia():
    if request.method == 'POST':
        d = request.json
        db.session.add(Animal(caravana=d['caravana'], peso=d['peso'], estado=d['estado']))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"id": a.id, "caravana": a.caravana, "peso": a.peso, "estado": a.estado} for a in Animal.query.all()])

@app.route('/api/lotes', methods=['GET', 'POST'])
def handle_lotes():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], has=d['has']))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"id": l.id, "nombre": l.nombre, "cultivo": l.cultivo, "has": l.has} for l in Lote.query.all()])

@app.route('/api/lluvias', methods=['GET', 'POST'])
def handle_lluvias():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lluvia(mm=d['mm'], fecha=d['fecha']))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([{"id": ll.id, "mm": ll.mm, "fecha": ll.fecha} for ll in Lluvia.query.all()])

# --- ACCIONES DE EDICIÓN Y BORRADO ---
@app.route('/api/<string:modulo>/<int:id>', methods=['PUT', 'DELETE'])
def acciones(modulo, id):
    modelos = {'ganaderia': Animal, 'lotes': Lote, 'lluvias': Lluvia}
    item = modelos[modulo].query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item)
    else:
        d = request.json
        for key, value in d.items(): setattr(item, key, value)
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA AGROPECUARIO V.PRO ACTIVADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)