import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

# --- Configuración Inicial ---
app = Flask(__name__)
CORS(app) # Permite que el frontend (web) hable con este backend

# Configuración de Base de Datos (SQLite para simplicidad y robustez)
# Se creará el archivo 'agronexo.db' en la carpeta instance o root
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelos de Base de Datos (Estructura de tus datos) ---

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=False) # Vaca, Ternero, Toro
    peso = db.Column(db.Float, default=0.0)
    estado_reproductivo = db.Column(db.String(50), default='VACIA') # VACIA, PREÑADA, PARIDA
    lat = db.Column(db.Float, default=-26.7) # Coordenadas default (Chaco aprox)
    lng = db.Column(db.Float, default=-60.8)
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cultivo = db.Column(db.String(50), default='Sin Sembrar') # Soja, Maíz, Sorgo
    hectareas = db.Column(db.Float, default=0.0)
    lat = db.Column(db.Float, default=-26.7)
    lng = db.Column(db.Float, default=-60.8)
    activo = db.Column(db.Boolean, default=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    milimetros = db.Column(db.Float, nullable=False)
    notas = db.Column(db.String(200))

# --- Rutas / Endpoints de la API ---

@app.route('/')
def home():
    return jsonify({"status": "Online", "system": "AgroNexo V2.0 Clean"})

# --- 1. Módulo GANADERÍA ---

@app.route('/api/ganaderia', methods=['GET'])
def get_animales():
    # Solo traemos animales activos
    animales = Animal.query.filter_by(activo=True).all()
    resultado = []
    for a in animales:
        resultado.append({
            "id": a.id,
            "caravana": a.caravana,
            "categoria": a.categoria,
            "estado_reproductivo": a.estado_reproductivo,
            "peso": a.peso,
            "lat": a.lat,
            "lng": a.lng
        })
    return jsonify(resultado)

@app.route('/api/ganaderia', methods=['POST'])
def add_animal():
    data = request.json
    nuevo_animal = Animal(
        caravana=data.get('caravana'),
        categoria=data.get('categoria'),
        estado_reproductivo=data.get('estado', 'VACIA'),
        lat=data.get('lat', -26.7),
        lng=data.get('lng', -60.8)
    )
    db.session.add(nuevo_animal)
    try:
        db.session.commit()
        return jsonify({"msg": "Animal registrado correctamente", "id": nuevo_animal.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/api/ganaderia/<int:id>', methods=['DELETE'])
def delete_animal(id):
    animal = Animal.query.get(id)
    if animal:
        # Baja lógica (no borramos el dato, solo lo desactivamos)
        animal.activo = False
        db.session.commit()
        return jsonify({"msg": "Animal dado de baja"})
    return jsonify({"error": "Animal no encontrado"}), 404

# --- 2. Módulo AGRICULTURA ---

@app.route('/api/agricultura', methods=['GET'])
def get_lotes():
    lotes = Lote.query.filter_by(activo=True).all()
    lista = []
    for l in lotes:
        lista.append({
            "id": l.id,
            "nombre": l.nombre,
            "cultivo": l.cultivo,
            "hectareas": l.hectareas,
            "lat": l.lat,
            "lng": l.lng
        })
    return jsonify(lista)

@app.route('/api/agricultura', methods=['POST'])
def add_lote():
    data = request.json
    nuevo_lote = Lote(
        nombre=data.get('nombre'),
        cultivo=data.get('cultivo', 'Barbecho'),
        hectareas=float(data.get('hectareas', 0)),
        lat=data.get('lat', -26.7),
        lng=data.get('lng', -60.8)
    )
    db.session.add(nuevo_lote)
    db.session.commit()
    return jsonify({"msg": "Lote creado"})

# --- 3. Módulo LLUVIA (Registrar Lluvia) ---

@app.route('/api/lluvia', methods=['GET', 'POST'])
def gestion_lluvia():
    if request.method == 'POST':
        data = request.json
        nueva = Lluvia(
            milimetros=float(data.get('mm', 0)),
            notas=data.get('notas', '')
        )
        db.session.add(nueva)
        db.session.commit()
        return jsonify({"msg": "Lluvia registrada"})
    
    # GET: Traer últimas lluvias
    lluvias = Lluvia.query.order_by(Lluvia.fecha.desc()).limit(10).all()
    res = [{"id": l.id, "mm": l.milimetros, "fecha": str(l.fecha)} for l in lluvias]
    return jsonify(res)

# --- 4. Módulo MAPA GENERAL ---

@app.route('/api/mapa', methods=['GET'])
def get_mapa_data():
    # Combina Lotes y Animales para mostrarlos juntos en el mapa
    animales = Animal.query.filter_by(activo=True).all()
    lotes = Lote.query.filter_by(activo=True).all()
    
    items_mapa = []
    
    for a in animales:
        items_mapa.append({
            "tipo": "animal",
            "titulo": f"Caravana {a.caravana}",
            "descripcion": f"{a.categoria} - {a.estado_reproductivo}",
            "lat": a.lat,
            "lng": a.lng
        })
        
    for l in lotes:
        items_mapa.append({
            "tipo": "lote",
            "titulo": f"Lote {l.nombre}",
            "descripcion": f"{l.cultivo} ({l.hectareas} Has)",
            "lat": l.lat,
            "lng": l.lng
        })
        
    return jsonify(items_mapa)

# --- 5. Módulo RESUMEN / DASHBOARD ---

@app.route('/api/resumen', methods=['GET'])
def get_resumen():
    total_animales = Animal.query.filter_by(activo=True).count()
    total_lotes = Lote.query.filter_by(activo=True).count()
    # Sumar milímetros de lluvias (ejemplo simple)
    # total_lluvia = db.session.query(func.sum(Lluvia.milimetros)).scalar() or 0
    
    return jsonify({
        "animales": total_animales,
        "lotes": total_lotes,
        "alertas": 0 # Placeholder para futuras alertas
    })

# --- Inicializador ---
# Esto crea las tablas si no existen al arrancar
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Usamos puerto standard de Render o 5000 local
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)