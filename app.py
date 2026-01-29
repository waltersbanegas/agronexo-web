import os
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_pro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS AVANZADOS ---

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cultivo = db.Column(db.String(50)) # Soja, Maíz, etc.
    hectareas = db.Column(db.Float)
    condicion = db.Column(db.String(50)) # Propio, Alquilado
    costo_alquiler = db.Column(db.Float, default=0.0) # USD o Quintales
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True)
    categoria = db.Column(db.String(50)) # Vaca, Toro, Ternero
    raza = db.Column(db.String(50), default='Braford') # Por defecto Braford
    peso = db.Column(db.Float, default=0.0)
    estado_reproductivo = db.Column(db.String(50), default='VACIA')
    origen = db.Column(db.String(50), default='Propio') # Compra / Propio
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True) # Vinculado a lote
    milimetros = db.Column(db.Float)
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    notas = db.Column(db.String(200))

# --- RUTAS ---

@app.route('/')
def home(): return jsonify({"status": "Online", "version": "Expert V8"})

@app.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    # Sembrar Datos PRO
    l1 = Lote(nombre="Lote Norte (Los Frentones)", cultivo="Soja", hectareas=100, condicion="Propio", lat=-26.42, lng=-61.41)
    l2 = Lote(nombre="Campo Arrendado", cultivo="Maíz", hectareas=50, condicion="Alquilado", costo_alquiler=200, lat=-26.45, lng=-61.45)
    db.session.add_all([l1, l2])
    
    # Animales Braford
    for i in range(1, 11):
        db.session.add(Animal(
            caravana=f"BF-{100+i}", categoria="Vaca", raza="Braford", peso=450,
            estado_reproductivo=random.choice(["PREÑADA", "VACIA"]),
            lat=-26.42 + (random.random()/100), lng=-61.41 + (random.random()/100)
        ))
    db.session.commit()
    return "Base de Datos EXPERTA Restaurada."

# --- API CRUD COMPLETA (GET, POST, DELETE) ---

@app.route('/api/resumen')
def resumen():
    return jsonify({
        "animales": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.filter_by(activo=True).count(),
        "lluvias": Lluvia.query.count()
    })

# AGRICULTURA
@app.route('/api/lotes', methods=['GET', 'POST'])
def lotes():
    if request.method == 'POST':
        d = request.json
        new = Lote(
            nombre=d['nombre'], cultivo=d['cultivo'], hectareas=d['has'],
            condicion=d['condicion'], costo_alquiler=d.get('costo', 0),
            lat=d['lat'], lng=d['lng']
        )
        db.session.add(new)
        db.session.commit()
        return jsonify({"msg": "Lote creado"})
    
    # GET
    res = []
    for l in Lote.query.filter_by(activo=True).all():
        res.append({
            "id": l.id, "nombre": l.nombre, "cultivo": l.cultivo, "has": l.hectareas,
            "condicion": l.condicion, "costo": l.costo_alquiler, "lat": l.lat, "lng": l.lng
        })
    return jsonify(res)

@app.route('/api/lotes/<int:id>', methods=['DELETE'])
def delete_lote(id):
    l = Lote.query.get(id)
    if l: 
        l.activo = False # Borrado lógico
        db.session.commit()
    return jsonify({"msg": "Eliminado"})

# GANADERÍA
@app.route('/api/animales', methods=['GET', 'POST'])
def animales():
    if request.method == 'POST':
        d = request.json
        new = Animal(
            caravana=d['caravana'], categoria=d['categoria'], raza=d.get('raza', 'Braford'),
            peso=d.get('peso', 0), estado_reproductivo=d['estado'],
            lat=d['lat'], lng=d['lng']
        )
        db.session.add(new)
        db.session.commit()
        return jsonify({"msg": "Animal creado"})
    
    # GET
    res = []
    for a in Animal.query.filter_by(activo=True).all():
        res.append({
            "id": a.id, "caravana": a.caravana, "cat": a.categoria, "raza": a.raza,
            "peso": a.peso, "estado": a.estado_reproductivo, "lat": a.lat, "lng": a.lng
        })
    return jsonify(res)

@app.route('/api/animales/<int:id>', methods=['DELETE'])
def delete_animal(id):
    a = Animal.query.get(id)
    if a:
        a.activo = False
        db.session.commit()
    return jsonify({"msg": "Eliminado"})

# LLUVIA (Ahora vinculada a Lote)
@app.route('/api/lluvias', methods=['GET', 'POST'])
def lluvias():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lluvia(lote_id=d.get('lote_id'), milimetros=d['mm'], notas=d.get('notas','')))
        db.session.commit()
        return jsonify({"msg": "Lluvia registrada"})
    
    res = []
    for l in Lluvia.query.order_by(Lluvia.fecha.desc()).all():
        nombre_lote = "General"
        if l.lote_id:
            obj_lote = Lote.query.get(l.lote_id)
            if obj_lote: nombre_lote = obj_lote.nombre
            
        res.append({"id": l.id, "mm": l.milimetros, "fecha": str(l.fecha)[:10], "lote": nombre_lote})
    return jsonify(res)

# MAPA (Híbrido real)
@app.route('/api/mapa')
def mapa():
    data = []
    for a in Animal.query.filter_by(activo=True).all():
        color = "red" if a.estado_reproductivo == "PREÑADA" else "blue"
        data.append({
            "tipo": "animal", "lat": a.lat, "lng": a.lng, 
            "titulo": f"{a.caravana} ({a.raza})", 
            "desc": f"{a.categoria} - {a.peso}kg - {a.estado_reproductivo}", 
            "color": color
        })
    for l in Lote.query.filter_by(activo=True).all():
        data.append({
            "tipo": "lote", "lat": l.lat, "lng": l.lng, 
            "titulo": l.nombre, 
            "desc": f"{l.cultivo} - {l.hectareas} Has ({l.condicion})", 
            "color": "green"
        })
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)