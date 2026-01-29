import os
import random
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True)
    categoria = db.Column(db.String(50))
    estado_reproductivo = db.Column(db.String(50), default='VACIA')
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    hectareas = db.Column(db.Float)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    milimetros = db.Column(db.Float)
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    notas = db.Column(db.String(200))

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_caravana = db.Column(db.String(50))
    tipo = db.Column(db.String(50)) # IATF, TACTO
    resultado = db.Column(db.String(50))
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())

# --- RUTAS ---
@app.route('/')
def home(): return jsonify({"status": "Online", "v": "7.0"})

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    # Datos Semilla
    db.session.add(Lote(nombre="Lote Norte", cultivo="Soja", hectareas=100, lat=-26.701, lng=-60.801))
    for i in range(101, 116):
        db.session.add(Animal(caravana=f"RP-{i}", categoria="Vaca", estado_reproductivo=random.choice(["VACIA","PREÑADA"]), lat=-26.7+random.random()/60, lng=-60.8+random.random()/60))
    db.session.commit()
    return "Base de Datos V7 Restaurada."

@app.route('/api/resumen')
def resumen():
    return jsonify({
        "animales": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.filter_by(activo=True).count(),
        "lluvias": Lluvia.query.count()
    })

@app.route('/api/mapa')
def mapa():
    data = []
    for a in Animal.query.filter_by(activo=True).all():
        data.append({"tipo":"animal", "lat":a.lat, "lng":a.lng, "titulo":a.caravana, "desc":f"{a.categoria} ({a.estado_reproductivo})", "color": "red" if a.estado_reproductivo=="PREÑADA" else "blue"})
    for l in Lote.query.filter_by(activo=True).all():
        data.append({"tipo":"lote", "lat":l.lat, "lng":l.lng, "titulo":l.nombre, "desc":f"{l.cultivo} {l.hectareas}ha", "color":"green"})
    return jsonify(data)

@app.route('/api/ganaderia', methods=['GET','POST'])
def ganaderia():
    if request.method=='POST':
        d=request.json
        db.session.add(Animal(caravana=d['caravana'], categoria=d['categoria'], estado_reproductivo=d['estado'], lat=d['lat'], lng=d['lng']))
        db.session.commit()
        return jsonify({"msg":"Ok"})
    return jsonify([{"caravana":a.caravana, "categoria":a.categoria, "estado":a.estado_reproductivo} for a in Animal.query.filter_by(activo=True).all()])

@app.route('/api/agricultura', methods=['GET','POST'])
def agricultura():
    if request.method=='POST':
        d=request.json
        db.session.add(Lote(nombre=d['nombre'], cultivo=d['cultivo'], hectareas=d['has'], lat=d['lat'], lng=d['lng']))
        db.session.commit()
        return jsonify({"msg":"Ok"})
    return jsonify([{"nombre":l.nombre, "cultivo":l.cultivo, "hectareas":l.hectareas} for l in Lote.query.filter_by(activo=True).all()])

@app.route('/api/lluvia', methods=['GET','POST'])
def lluvia():
    if request.method=='POST':
        db.session.add(Lluvia(milimetros=request.json['mm'], notas="App"))
        db.session.commit()
        return jsonify({"msg":"Ok"})
    return jsonify([{"fecha":str(l.fecha)[:10], "mm":l.milimetros} for l in Lluvia.query.order_by(Lluvia.fecha.desc()).all()])

@app.route('/api/repro', methods=['GET','POST'])
def repro():
    if request.method=='POST':
        d=request.json
        # Guardar Evento
        db.session.add(Evento(animal_caravana=d['caravana'], tipo=d['tipo'], resultado=d['resultado']))
        # Actualizar Animal
        a = Animal.query.filter_by(caravana=d['caravana']).first()
        if a:
            if d['tipo']=='TACTO' and d['resultado']=='PREÑADA': a.estado_reproductivo='PREÑADA'
            if d['tipo']=='PARTO': a.estado_reproductivo='PARIDA'
        db.session.commit()
        return jsonify({"msg":"Ok"})
    return jsonify([{"animal":e.animal_caravana, "tipo":e.tipo, "res":e.resultado, "fecha":str(e.fecha)[:10]} for e in Evento.query.order_by(Evento.fecha.desc()).limit(20).all()])

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))