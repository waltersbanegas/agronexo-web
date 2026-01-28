import os
import random
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
# Permitir conexiones desde cualquier origen (CORS)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuración DB
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (Tablas de Datos) ---
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

class EventoReproduccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer)
    tipo = db.Column(db.String(50)) # IATF, TACTO, PARTO
    resultado = db.Column(db.String(100))
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())

# --- RUTAS DE DATOS ---

@app.route('/')
def home():
    return jsonify({"status": "Online", "version": "Master V6 Full"})

@app.route('/reset')
def reset_db():
    try:
        db.drop_all()
        db.create_all()
        # Sembrar Datos de Prueba
        db.session.add(Lote(nombre="Lote Norte", cultivo="Soja", hectareas=100, lat=-26.701, lng=-60.801))
        db.session.add(Lote(nombre="Lote Sur", cultivo="Maíz", hectareas=50, lat=-26.705, lng=-60.805))
        # Sembrar Animales
        estados = ["VACIA", "PREÑADA", "PARIDA"]
        for i in range(1, 16):
            est = random.choice(estados)
            db.session.add(Animal(
                caravana=f"RP-{100+i}", categoria="Vaca", estado_reproductivo=est,
                lat=-26.7 + (random.random()/50), lng=-60.8 + (random.random()/50)
            ))
        db.session.add(Lluvia(milimetros=25, notas="Lluvia inicial"))
        db.session.commit()
        return "¡SISTEMA COMPLETAMENTE RESTAURADO! Recarga la web."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/api/resumen')
def get_resumen():
    return jsonify({
        "animales": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.filter_by(activo=True).count(),
        "lluvias": Lluvia.query.count(),
    })

@app.route('/api/mapa')
def get_mapa():
    data = []
    # Animales (Puntos)
    for a in Animal.query.filter_by(activo=True).all():
        color = "red" if a.estado_reproductivo == "PREÑADA" else "blue"
        data.append({
            "tipo": "animal", "lat": a.lat, "lng": a.lng, 
            "titulo": a.caravana, "desc": f"{a.categoria} - {a.estado_reproductivo}", 
            "color": color
        })
    # Lotes (Puntos Verdes)
    for l in Lote.query.filter_by(activo=True).all():
        data.append({
            "tipo": "lote", "lat": l.lat, "lng": l.lng, 
            "titulo": l.nombre, "desc": f"{l.cultivo} ({l.hectareas} ha)", 
            "color": "green"
        })
    return jsonify(data)

# --- CRUD GANADERÍA ---
@app.route('/api/ganaderia', methods=['GET', 'POST'])
def api_ganaderia():
    if request.method == 'POST':
        d = request.json
        db.session.add(Animal(
            caravana=d.get('caravana'), categoria=d.get('categoria'), 
            estado_reproductivo=d.get('estado', 'VACIA'),
            lat=d.get('lat', -26.7), lng=d.get('lng', -60.8)
        ))
        db.session.commit()
        return jsonify({"msg": "Guardado"})
    
    lista = Animal.query.filter_by(activo=True).all()
    return jsonify([{
        "id": a.id, "caravana": a.caravana, "categoria": a.categoria, 
        "estado": a.estado_reproductivo, "lat": a.lat, "lng": a.lng
    } for a in lista])

# --- CRUD AGRICULTURA ---
@app.route('/api/agricultura', methods=['GET', 'POST'])
def api_agricultura():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lote(
            nombre=d.get('nombre'), cultivo=d.get('cultivo'), hectareas=d.get('hectareas'),
            lat=d.get('lat', -26.7), lng=d.get('lng', -60.8)
        ))
        db.session.commit()
        return jsonify({"msg": "Guardado"})
    
    lista = Lote.query.filter_by(activo=True).all()
    return jsonify([{
        "id": l.id, "nombre": l.nombre, "cultivo": l.cultivo, 
        "hectareas": l.hectareas, "lat": l.lat, "lng": l.lng
    } for l in lista])

# --- CRUD LLUVIA ---
@app.route('/api/lluvia', methods=['GET', 'POST'])
def api_lluvia():
    if request.method == 'POST':
        d = request.json
        db.session.add(Lluvia(milimetros=float(d.get('mm')), notas=d.get('notas', '')))
        db.session.commit()
        return jsonify({"msg": "Guardado"})
    
    lista = Lluvia.query.order_by(Lluvia.fecha.desc()).all()
    return jsonify([{"id": l.id, "mm": l.milimetros, "fecha": str(l.fecha)[:10]} for l in lista])

# --- CRUD REPRODUCCIÓN ---
@app.route('/api/reproduccion', methods=['GET', 'POST'])
def api_repro():
    if request.method == 'POST':
        d = request.json
        db.session.add(EventoReproduccion(animal_id=d.get('id'), tipo=d.get('tipo'), resultado=d.get('res')))
        db.session.commit()
        return jsonify({"msg": "Evento registrado"})
    return jsonify([]) # (Simplificado para GET)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)