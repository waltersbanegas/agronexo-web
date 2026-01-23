import os
import pandas as pd
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import extract, func, text
import traceback

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN BASE DE DATOS ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///agronexo.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---

# [MODELOS EXISTENTES SIN CAMBIOS: Lote, ContratoCampo, Silo, Cosecha, Peso, Gasto, Venta, Lluvia, VentaGrano]
# ... (Mantén aquí las clases Lote, ContratoCampo, Silo, Cosecha, Peso, Gasto, Venta, Lluvia, VentaGrano tal cual estaban) ...
# Pego aquí las clases que NO cambian para que el código sea funcional completo si copias y pegas:

class Lote(db.Model):
    __tablename__ = 'lote'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    hectareas = db.Column(db.Float)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

class ContratoCampo(db.Model):
    __tablename__ = 'contrato_campo'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    propietario = db.Column(db.String(100))
    tipo = db.Column(db.String(50)) 
    porcentaje_dueno = db.Column(db.Float)

class Silo(db.Model):
    __tablename__ = 'silo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    contenido = db.Column(db.String(50))
    capacidad = db.Column(db.Float)
    kilos_actuales = db.Column(db.Float, default=0.0)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

class Cosecha(db.Model):
    __tablename__ = 'cosecha'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    kilos_totales = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    destino = db.Column(db.String(50)) 
    silo_id = db.Column(db.Integer, db.ForeignKey('silo.id'), nullable=True)

class Peso(db.Model):
    __tablename__ = 'peso'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    kilos = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Gasto(db.Model):
    __tablename__ = 'gasto'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    categoria = db.Column(db.String(50))
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=True)

class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    comprador = db.Column(db.String(100))
    kilos_venta = db.Column(db.Float)
    precio_total = db.Column(db.Float)
    costo_historico = db.Column(db.Float)

class Lluvia(db.Model):
    __tablename__ = 'lluvia'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    milimetros = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class VentaGrano(db.Model):
    __tablename__ = 'venta_grano'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    comprador = db.Column(db.String(100))
    tipo_grano = db.Column(db.String(50))
    kilos = db.Column(db.Float)
    precio_total = db.Column(db.Float)
    origen = db.Column(db.String(50))
    silo_id = db.Column(db.Integer, db.ForeignKey('silo.id'), nullable=True)

# 🆕 NUEVOS MODELOS PARA REPRODUCCIÓN AVANZADA

class InsumoGenetico(db.Model): # Toros / Semen
    __tablename__ = 'insumo_genetico'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100)) # Ej: "Toro Campeón 2024"
    tipo = db.Column(db.String(50)) # "SEMEN_CONVENCIONAL", "SEMEN_SEXADO", "TORO_NATURAL"
    raza = db.Column(db.String(50))
    costo_dosis = db.Column(db.Float) # Costo unitario para reportes

class Protocolo(db.Model): # Recetas IATF
    __tablename__ = 'protocolo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100)) # Ej: "IATF Convencional + Repaso"
    descripcion = db.Column(db.String(200))
    costo_estimado = db.Column(db.Float) # Costo de hormonas/dispositivos por cabeza

class Animal(db.Model):
    __tablename__ = 'animal'
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(20), unique=True) # ID Visual
    rfid = db.Column(db.String(50), nullable=True) # 🆕 ID Electrónico (SENASA)
    categoria = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    lote_actual_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True)
    estado_reproductivo = db.Column(db.String(50), default='VACIA') 

class EventoReproductivo(db.Model):
    __tablename__ = 'evento_reproductivo'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(50)) # INSEMINACION, TACTO, PARTO, CELO_DETECTADO
    detalle = db.Column(db.String(100)) # Resultado texto simple
    
    # 🆕 CAMPOS NUEVOS PARA TRAZABILIDAD
    protocolo_id = db.Column(db.Integer, db.ForeignKey('protocolo.id'), nullable=True)
    genetica_id = db.Column(db.Integer, db.ForeignKey('insumo_genetico.id'), nullable=True)
    operario = db.Column(db.String(50), nullable=True)
    condicion_corporal = db.Column(db.Float, nullable=True) # Escala 1-5 o 1-9
    fecha_probable_parto = db.Column(db.DateTime, nullable=True) # Calculado si es preñez

# --- RUTAS ---

# [RUTAS EXISTENTES SIN CAMBIOS: resumen_general, liquidaciones, silos, cosechas, etc...]
# Mantenlas todas. Aquí solo pongo las NUEVAS o MODIFICADAS.

@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        lista = []
        todos = Animal.query.all()
        for vaca in todos:
            if Venta.query.filter_by(animal_id=vaca.id).first(): continue
            pesajes = Peso.query.filter_by(animal_id=vaca.id).order_by(Peso.fecha.desc()).all()
            gastos = Gasto.query.filter_by(animal_id=vaca.id).all()
            total_gastos = sum(g.monto for g in gastos)
            peso_act = 0; gdp = 0
            ubicacion = "En Corral / Sin Lote"
            if vaca.lote_actual_id:
                lote = Lote.query.get(vaca.lote_actual_id)
                if lote: ubicacion = lote.nombre
            if pesajes:
                peso_act = pesajes[0].kilos
                if len(pesajes) > 1:
                    dif_k = peso_act - pesajes[1].kilos
                    dif_d = (pesajes[0].fecha - pesajes[1].fecha).days
                    if dif_d > 0: gdp = dif_k / dif_d
            lista.append({ 
                "id": vaca.id, "caravana": vaca.caravana, "rfid": vaca.rfid, # 🆕
                "raza": vaca.raza, "categoria": vaca.categoria, "peso_actual": peso_act, 
                "gdp": round(gdp, 3), "costo_acumulado": total_gastos, 
                "ubicacion": ubicacion, "lote_actual_id": vaca.lote_actual_id,
                "estado_reproductivo": getattr(vaca, 'estado_reproductivo', 'VACIA') 
            })
        return jsonify(lista)
    except Exception as e: return jsonify({"error": str(e)}), 500

# 🆕 GESTIÓN DE CONFIGURACIÓN REPRODUCTIVA
@app.route('/api/config_repro', methods=['GET'])
def obtener_config_repro():
    toros = InsumoGenetico.query.all()
    protocolos = Protocolo.query.all()
    return jsonify({
        "toros": [{"id":t.id, "nombre":t.nombre, "tipo":t.tipo} for t in toros],
        "protocolos": [{"id":p.id, "nombre":p.nombre, "costo":p.costo_estimado} for p in protocolos]
    })

@app.route('/api/crear_config_repro', methods=['POST'])
def crear_config_repro():
    d = request.json
    if d['tipo_objeto'] == 'TORO':
        nuevo = InsumoGenetico(nombre=d['nombre'], tipo=d['tipo'], raza=d['raza'], costo_dosis=float(d['costo']))
        db.session.add(nuevo)
    elif d['tipo_objeto'] == 'PROTOCOLO':
        nuevo = Protocolo(nombre=d['nombre'], descripcion=d['descripcion'], costo_estimado=float(d['costo']))
        db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Creado exitosamente"})

# 🆕 EVENTO REPRODUCTIVO MASIVO (CON LÓGICA FINANCIERA)
@app.route('/api/evento_reproductivo_masivo', methods=['POST'])
def evento_reproductivo_masivo():
    try:
        d = request.json
        ids_animales = d.get('animales_ids', [])
        tipo = d['tipo']
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        
        # Datos extra
        protocolo_id = d.get('protocolo_id')
        genetica_id = d.get('genetica_id')
        operario = d.get('operario')
        condicion_corporal = d.get('condicion_corporal')
        
        # Costos a aplicar (Prorrateo)
        costo_total_evento = 0.0
        
        # Calcular costos unitarios
        costo_protocolo = 0.0
        costo_genetica = 0.0
        
        if protocolo_id:
            prot = Protocolo.query.get(protocolo_id)
            if prot: costo_protocolo = prot.costo_estimado
        
        if genetica_id:
            gen = InsumoGenetico.query.get(genetica_id)
            if gen: costo_genetica = gen.costo_dosis

        count = 0
        for aid in ids_animales:
            animal = Animal.query.get(aid)
            if animal:
                # 1. Crear Evento
                evento = EventoReproductivo(
                    animal_id=animal.id, tipo=tipo, fecha=fecha,
                    detalle=d.get('detalle', ''),
                    protocolo_id=protocolo_id, genetica_id=genetica_id,
                    operario=operario, condicion_corporal=condicion_corporal
                )
                
                # 2. Actualizar Estado
                if tipo == 'INSEMINACION': 
                    animal.estado_reproductivo = 'INSEMINADA'
                    # Crear Gasto Automático
                    gasto_total = costo_protocolo + costo_genetica
                    if gasto_total > 0:
                        nuevo_gasto = Gasto(fecha=fecha, concepto="Inseminación (Protocolo+Dosis)", monto=gasto_total, categoria="REPRODUCCION", animal_id=animal.id)
                        db.session.add(nuevo_gasto)

                elif tipo == 'TACTO':
                    es_positivo = d.get('detalle') == 'POSITIVO'
                    animal.estado_reproductivo = 'PREÑADA' if es_positivo else 'VACIA'
                    if es_positivo:
                        # Calcular fecha parto (aprox 283 días después de la última inseminación o desde hoy si no hay dato)
                        evento.fecha_probable_parto = fecha + timedelta(days=200) # Estimado tacto, ajuste según feto
                        # Idealmente buscaríamos la fecha de inseminación previa
                        ultima_ia = EventoReproductivo.query.filter_by(animal_id=animal.id, tipo='INSEMINACION').order_by(EventoReproductivo.fecha.desc()).first()
                        if ultima_ia:
                            evento.fecha_probable_parto = ultima_ia.fecha + timedelta(days=283)

                elif tipo == 'PARTO': 
                    animal.estado_reproductivo = 'PARIDA'
                
                db.session.add(evento)
                count += 1
        
        db.session.commit()
        return jsonify({"mensaje": f"Evento aplicado a {count} animales"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# [MANTENER TODAS LAS OTRAS RUTAS DEL ARCHIVO ANTERIOR: nuevo_animal, editar_lote, liquidaciones, etc...]
# Por favor, asegúrate de copiar las rutas existentes del archivo anterior (resumen_general, nuevo_silo, etc) aquí abajo.
# ... (Código existente) ...

# --- INICIO CON MIGRACIÓN ---
with app.app_context():
    db.create_all()
    # Migración silenciosa de columnas nuevas
    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE animal ADD COLUMN IF NOT EXISTS rfid VARCHAR(50);'))
            conn.execute(text('ALTER TABLE evento_reproductivo ADD COLUMN IF NOT EXISTS protocolo_id INTEGER;'))
            conn.execute(text('ALTER TABLE evento_reproductivo ADD COLUMN IF NOT EXISTS genetica_id INTEGER;'))
            conn.execute(text('ALTER TABLE evento_reproductivo ADD COLUMN IF NOT EXISTS fecha_probable_parto TIMESTAMP;'))
            conn.commit()
    except: pass

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')