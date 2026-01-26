import os
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
# CORS habilitado para que el frontend pueda conectarse sin bloqueos
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Configuración ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    estado_reproductivo = db.Column(db.String(50), default='VACIA')
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cultivo = db.Column(db.String(50), default='Barbecho')
    hectareas = db.Column(db.Float, default=0.0)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class EventoReproduccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    tipo = db.Column(db.String(50))
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    resultado = db.Column(db.String(100))

class Lluvia(db.Model): # Agregado modelo Lluvia para evitar errores
    id = db.Column(db.Integer, primary_key=True)
    milimetros = db.Column(db.Float)
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())

# --- FUNCIÓN DE RESET ---
def reiniciar_datos():
    db.drop_all()
    db.create_all()
    
    # Crear Lotes
    l1 = Lote(nombre="Lote Norte", cultivo="Soja", hectareas=150, lat=-26.701, lng=-60.801)
    l2 = Lote(nombre="Lote Sur", cultivo="Maíz", hectareas=80, lat=-26.705, lng=-60.805)
    db.session.add_all([l1, l2])
    
    # Crear Animales
    for i in range(1, 16):
        a = Animal(caravana=f"A-{100+i}", categoria="Vaca", estado_reproductivo="PREÑADA" if i%2==0 else "VACIA", 
                   lat=-26.7 + (random.random()/50), lng=-60.8 + (random.random()/50))
        db.session.add(a)
    
    db.session.commit()

# --- RUTAS ---
@app.route('/')
def home():
    # Si ves este mensaje en el navegador, es que YA se actualizó
    return jsonify({
        "status": "Online", 
        "version": "V3_FINAL_FUNCIONA", 
        "mensaje": "Si ves esto, ve a /reset para cargar datos"
    })

@app.route('/reset')
def reset_manual():
    try:
        reiniciar_datos()
        return "¡ÉXITO! Datos restaurados. Vuelve al inicio y recarga la página."
    except Exception as e:
        return f"Error al resetear: {str(e)}"

@app.route('/api/resumen', methods=['GET'])
def get_resumen():
    total_animales = Animal.query.filter_by(activo=True).count()
    total_lotes = Lote.query.filter_by(activo=True).count()
    return jsonify({
        "animales": total_animales,
        "lotes": total_lotes,
        "finanzas": {"gastos": 1200000, "margen": 4500000},
        "modulos": ["ganaderia", "agricultura", "reproduccion", "mapa"]
    })

@app.route('/api/ganaderia', methods=['GET', 'POST'])
def gestion_ganaderia():
    if request.method == 'POST':
        d = request.json
        db.session.add(Animal(caravana=d.get('caravana'), categoria=d.get('categoria'), lat=d.get('lat'), lng=d.get('lng')))
        db.session.commit()
        return jsonify({"msg": "Ok"})
    
    lista = Animal.query.filter_by(activo=True).all()
    return jsonify([{"id": a.id, "caravana": a.caravana, "categoria": a.categoria, "estado": a.estado_reproductivo, "lat": a.lat, "lng": a.lng} for a in lista])

@app.route('/api/agricultura', methods=['GET'])
def gestion_agricultura():
    lista = Lote.query.filter_by(activo=True).all()
    return jsonify([{"id": l.id, "nombre": l.nombre, "cultivo": l.cultivo, "hectareas": l.hectareas, "lat": l.lat, "lng": l.lng} for l in lista])

@app.route('/api/mapa', methods=['GET'])
def get_mapa():
    # Retorna datos combinados para el mapa
    data = []
    for a in Animal.query.filter_by(activo=True).all():
        data.append({"tipo": "animal", "lat": a.lat, "lng": a.lng, "titulo": a.caravana, "desc": a.categoria, "color": "blue"})
    for l in Lote.query.filter_by(activo=True).all():
        data.append({"tipo": "lote", "lat": l.lat, "lng": l.lng, "titulo": l.nombre, "desc": l.cultivo, "color": "green"})
    return jsonify(data)

@app.route('/api/reproduccion', methods=['GET'])
def get_repro():
    return jsonify([])

@app.route('/api/lluvia', methods=['GET']) # Endpoint dummy para lluvia
def get_lluvia():
    return jsonify([])

# --- ARRANQUE ---
with app.app_context():
    db.create_all()
    if Animal.query.count() == 0:
        reiniciar_datos()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)