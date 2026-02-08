import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_v13_pro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELOS DE DATOS INTEGRADOS
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

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    lote_id = db.Column(db.Integer)
    fecha = db.Column(db.String(20))

# --- ENDPOINTS ---
@app.route('/api/resumen')
def resumen():
    total_gastos = db.session.query(func.sum(Gasto.monto)).scalar() or 0
    return jsonify({
        "hacienda": Animal.query.count(),
        "lotes": Lote.query.count(),
        "lluvias": db.session.query(func.sum(Lluvia.mm)).scalar() or 0,
        "gastos": total_gastos
    })

@app.route('/api/<string:modulo>', methods=['GET', 'POST'])
def gestion_datos(modulo):
    modelos = {'ganaderia': Animal, 'lotes': Lote, 'lluvias': Lluvia, 'gastos': Gasto}
    model = modelos.get(modulo)
    if request.method == 'POST':
        d = request.json
        if modulo == 'ganaderia': db.session.add(Animal(caravana=d['caravana'], peso=d['peso'], estado=d['estado']))
        elif modulo == 'lotes': db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], has=d['has']))
        elif modulo == 'lluvias': db.session.add(Lluvia(mm=d['mm'], fecha=d['fecha']))
        elif modulo == 'gastos': db.session.add(Gasto(concepto=d['concepto'], monto=d['monto'], lote_id=d['lote_id'], fecha=d['fecha']))
        db.session.commit()
        return jsonify({"status": "ok"})
    
    items = model.query.all()
    if modulo == 'ganaderia': return jsonify([{"id":i.id,"caravana":i.caravana,"peso":i.peso,"estado":i.estado} for i in items])
    if modulo == 'lotes': return jsonify([{"id":i.id,"nombre":i.nombre,"cultivo":i.cultivo,"has":i.has} for i in items])
    if modulo == 'lluvias': return jsonify([{"id":i.id,"mm":i.mm,"fecha":i.fecha} for i in items])
    if modulo == 'gastos': return jsonify([{"id":i.id,"concepto":i.concepto,"monto":i.monto,"fecha":i.fecha} for i in items])

@app.route('/api/<string:modulo>/<int:id>', methods=['PUT', 'DELETE'])
def acciones(modulo, id):
    modelos = {'ganaderia': Animal, 'lotes': Lote, 'lluvias': Lluvia, 'gastos': Gasto}
    item = modelos[modulo].query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item)
    else:
        d = request.json
        for key, val in d.items(): setattr(item, key, val)
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "AGRONEXO V13 - MODULO GASTOS ACTIVADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)