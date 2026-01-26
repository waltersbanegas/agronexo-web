import os
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

# --- Configuración Base de Datos ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (Tablas) ---

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=False) # Vaca, Vaquillona, Toro
    estado_reproductivo = db.Column(db.String(50), default='VACIA') # VACIA, PREÑADA, PARIDA, EN_SERVICIO
    dias_preñez = db.Column(db.Integer, default=0)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class EventoReproduccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False) # IATF, TACTO, PARTO, CELO
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    resultado = db.Column(db.String(100)) # "Preñada", "Vacia", "Macho", "Hembra"
    observaciones = db.Column(db.String(200))

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cultivo = db.Column(db.String(50), default='Barbecho')
    hectareas = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(50), default='Ok') # Ok, Falta Agua, Plaga
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    milimetros = db.Column(db.Float, nullable=False)

# --- ENDPOINTS / API ---

@app.route('/')
def home():
    return jsonify({"status": "Online", "version": "AgroNexo Final"})

# 1. RESUMEN (Dashboard)
@app.route('/api/resumen', methods=['GET'])
def get_resumen():
    # Verificamos si hay datos, si no, creamos datos DEMO para que el usuario vea algo
    check_and_seed_demo_data()
    
    total_animales = Animal.query.filter_by(activo=True).count()
    total_lotes = Lote.query.filter_by(activo=True).count()
    
    # Cálculo simple de finanzas (simulado)
    gastos = 1500000 
    margen = 3200000
    
    return jsonify({
        "animales": total_animales,
        "lotes": total_lotes,
        "alertas": 2, # Ejemplo: 2 vacas por parir
        "finanzas": {"gastos": gastos, "margen": margen},
        "modulos": ["ganaderia", "agricultura", "reproduccion", "mapa"] # Habilita botones en frontend si es dinámico
    })

# 2. GANADERÍA
@app.route('/api/ganaderia', methods=['GET', 'POST'])
def gestion_ganaderia():
    if request.method == 'POST':
        data = request.json
        nuevo = Animal(
            caravana=data.get('caravana'),
            categoria=data.get('categoria'),
            estado_reproductivo=data.get('estado', 'VACIA'),
            lat=data.get('lat', -26.7),
            lng=data.get('lng', -60.8)
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({"msg": "Animal guardado"})
    
    animales = Animal.query.filter_by(activo=True).all()
    return jsonify([{
        "id": a.id, "caravana": a.caravana, "categoria": a.categoria, 
        "estado": a.estado_reproductivo, "lat": a.lat, "lng": a.lng
    } for a in animales])

# 3. REPRODUCCIÓN (El módulo que faltaba)
@app.route('/api/reproduccion', methods=['GET', 'POST'])
def gestion_reproduccion():
    if request.method == 'POST':
        # Registrar evento (IATF, Tacto, etc)
        data = request.json
        nuevo_evento = EventoReproduccion(
            animal_id=data.get('animal_id'),
            tipo=data.get('tipo'), # 'IATF', 'TACTO'
            resultado=data.get('resultado', '-'),
            observaciones=data.get('observaciones', '')
        )
        # Actualizar estado de la vaca si es necesario
        animal = Animal.query.get(data.get('animal_id'))
        if animal:
            if data.get('tipo') == 'TACTO' and data.get('resultado') == 'PREÑADA':
                animal.estado_reproductivo = 'PREÑADA'
            elif data.get('tipo') == 'PARTO':
                animal.estado_reproductivo = 'PARIDA'
        
        db.session.add(nuevo_evento)
        db.session.commit()
        return jsonify({"msg": "Evento reproductivo registrado"})

    # GET: Traer alertas o lista de inseminaciones
    eventos = EventoReproduccion.query.order_by(EventoReproduccion.fecha.desc()).limit(20).all()
    data_eventos = []
    for e in eventos:
        vaca = Animal.query.get(e.animal_id)
        nombre_vaca = vaca.caravana if vaca else "Desconocida"
        data_eventos.append({
            "id": e.id, "animal": nombre_vaca, "tipo": e.tipo, 
            "fecha": str(e.fecha), "resultado": e.resultado
        })
    return jsonify(data_eventos)

# 4. AGRICULTURA
@app.route('/api/agricultura', methods=['GET'])
def get_agricultura():
    lotes = Lote.query.filter_by(activo=True).all()
    return jsonify([{
        "id": l.id, "nombre": l.nombre, "cultivo": l.cultivo, 
        "hectareas": l.hectareas, "lat": l.lat, "lng": l.lng
    } for l in lotes])

# 5. MAPA GENERAL
@app.route('/api/mapa', methods=['GET'])
def get_mapa():
    animales = Animal.query.filter_by(activo=True).all()
    lotes = Lote.query.filter_by(activo=True).all()
    marcadores = []
    
    for a in animales:
        color = "red" if a.estado_reproductivo == 'PREÑADA' else "blue"
        marcadores.append({
            "tipo": "animal", "titulo": f"Caravana {a.caravana}",
            "desc": f"{a.categoria} ({a.estado_reproductivo})",
            "lat": a.lat, "lng": a.lng, "color": color
        })
        
    for l in lotes:
        marcadores.append({
            "tipo": "lote", "titulo": f"Lote {l.nombre}",
            "desc": f"{l.cultivo} - {l.hectareas} Has",
            "lat": l.lat, "lng": l.lng, "color": "green"
        })
    return jsonify(marcadores)

# --- FUNCIÓN DE AUTO-GENERACIÓN DE DATOS (Solo si está vacío) ---
def check_and_seed_demo_data():
    try:
        if Animal.query.first() is None:
            print("Base de datos vacía. Generando datos DEMO...")
            # Crear Lotes
            l1 = Lote(nombre="Norte 1", cultivo="Soja", hectareas=50, lat=-26.701, lng=-60.801)
            l2 = Lote(nombre="Sur 2", cultivo="Maíz", hectareas=30, lat=-26.705, lng=-60.805)
            db.session.add_all([l1, l2])
            
            # Crear Animales (Algunas preñadas para probar Reproducción)
            for i in range(1, 11):
                estado = "PREÑADA" if i % 3 == 0 else "VACIA"
                a = Animal(
                    caravana=f"V-{100+i}", 
                    categoria="Vaca", 
                    estado_reproductivo=estado,
                    lat=-26.7 + (random.random()/100), 
                    lng=-60.8 + (random.random()/100)
                )
                db.session.add(a)
            
            db.session.commit()
            print("Datos DEMO generados exitosamente.")
    except Exception as e:
        print(f"Error generando datos demo: {e}")

# --- INICIALIZADOR ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)