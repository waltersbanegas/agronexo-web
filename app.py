import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

# Configuración de base de datos final v2.1
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_final_master.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS TÉCNICOS RECUPERADOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50))  # Vaca, Novillo, Toro
    peso = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(50))  # PREÑADA, VACIA
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cultivo = db.Column(db.String(50)) # Soja, Girasol, Maíz
    has = db.Column(db.Float, default=0.0)
    geometria = db.Column(db.Text, nullable=True) # Coordenadas mapa
    activo = db.Column(db.Boolean, default=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mm = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.String(20))

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    fecha = db.Column(db.String(20))

# --- API ENDPOINTS ---
@app.route('/api/resumen')
def resumen():
    return jsonify({
        "hacienda": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.filter_by(activo=True).count(),
        "lluvias": db.session.query(func.sum(Lluvia.mm)).scalar() or 0,
        "gastos": db.session.query(func.sum(Gasto.monto)).scalar() or 0
    })

@app.route('/api/<string:modulo>', methods=['GET', 'POST'])
def gestion(modulo):
    modelos = {'ganaderia': Animal, 'lotes': Lote, 'lluvias': Lluvia, 'gastos': Gasto}
    model = modelos.get(modulo)
    if request.method == 'POST':
        d = request.json
        if modulo == 'ganaderia': db.session.add(Animal(caravana=d['caravana'], categoria=d['categoria'], peso=d['peso'], estado=d['estado']))
        elif modulo == 'lotes': db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], has=d['has'], geometria=d.get('geometria')))
        elif modulo == 'lluvias': db.session.add(Lluvia(mm=d['mm'], fecha=d['fecha']))
        elif modulo == 'gastos': db.session.add(Gasto(concepto=d['concepto'], monto=d['monto'], fecha=d['fecha']))
        db.session.commit()
        return jsonify({"status": "ok"})
    
    items = model.query.filter_by(activo=True).all() if hasattr(model, 'activo') else model.query.all()
    if modulo == 'ganaderia': return jsonify([{"id":i.id,"caravana":i.caravana,"categoria":i.categoria,"peso":i.peso,"estado":i.estado} for i in items])
    if modulo == 'lotes': return jsonify([{"id":i.id,"nombre":i.nombre,"cultivo":i.cultivo,"has":i.has,"geometria":i.geometria} for i in items])
    if modulo == 'lluvias': return jsonify([{"id":i.id,"mm":i.mm,"fecha":i.fecha} for i in items])
    if modulo == 'gastos': return jsonify([{"id":i.id,"concepto":i.concepto,"monto":i.monto,"fecha":i.fecha} for i in items])

@app.route('/api/<string:modulo>/<int:id>', methods=['PUT', 'DELETE'])
def acciones(modulo, id):
    modelos = {'ganaderia': Animal, 'lotes': Lote, 'lluvias': Lluvia, 'gastos': Gasto}
    item = modelos[modulo].query.get_or_404(id)
    if request.method == 'DELETE':
        if hasattr(item, 'activo'): item.activo = False
        else: db.session.delete(item)
    else:
        d = request.json
        for key, val in d.items(): setattr(item, key, val)
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA MASTER V2.1 RESTAURADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)