import os
import pandas as pd
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import extract, func, text
import traceback

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- CONFIGURACIÓN BASE DE DATOS ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///agronexo.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
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

class Animal(db.Model):
    __tablename__ = 'animal'
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(20), unique=True)
    rfid = db.Column(db.String(50), nullable=True)
    categoria = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    lote_actual_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True)
    estado_reproductivo = db.Column(db.String(50), default='VACIA') 

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

class EventoReproductivo(db.Model):
    __tablename__ = 'evento_reproductivo'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(50)) 
    detalle = db.Column(db.String(100)) 
    protocolo_id = db.Column(db.Integer, nullable=True)
    genetica_id = db.Column(db.Integer, nullable=True)
    operario = db.Column(db.String(50), nullable=True)
    condicion_corporal = db.Column(db.Float, nullable=True)
    fecha_probable_parto = db.Column(db.DateTime, nullable=True)

class InsumoGenetico(db.Model):
    __tablename__ = 'insumo_genetico'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    tipo = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    costo_dosis = db.Column(db.Float)

class Protocolo(db.Model):
    __tablename__ = 'protocolo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    descripcion = db.Column(db.String(200))
    costo_estimado = db.Column(db.Float)

# --- RUTAS DE EMERGENCIA ---
@app.route('/api/reset_tablas', methods=['GET'])
def reset_tablas():
    try:
        with app.app_context(): db.create_all()
        return jsonify({"mensaje": "✅ Tablas verificadas."})
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- RUTAS DE ACCIÓN MASIVA CORREGIDAS ---

@app.route('/api/mover_hacienda', methods=['POST'])
def mover_hacienda():
    try:
        d = request.json
        ids = d.get('animales_ids', [])
        # CORRECCIÓN: Si viene vacío, convertir a None
        destino = d.get('lote_destino_id')
        if not destino or destino == "":
            destino = None
        else:
            destino = int(destino)

        for aid in ids:
            a = Animal.query.get(aid)
            if a: a.lote_actual_id = destino
        db.session.commit()
        return jsonify({"mensaje": "Movimiento exitoso 🚚"})
    except Exception as e:
        print("ERROR MOVER:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/gasto_masivo', methods=['POST'])
def gasto_masivo():
    try:
        d = request.json
        lote_id = str(d.get('lote_id')) # Asegurar string para comparar
        monto_total = float(d['monto'])
        concepto = d['concepto']
        
        # Fecha
        fecha_gasto = datetime.utcnow()
        if d.get('fecha'):
            try: fecha_gasto = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass

        animales_destino = []
        todos = Animal.query.all()
        
        # Lógica de filtrado robusta
        for a in todos:
            # Ignorar vendidos
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            
            if lote_id == 'all':
                animales_destino.append(a)
            elif lote_id == 'corral': 
                if a.lote_actual_id is None: animales_destino.append(a)
            elif lote_id.isdigit(): 
                if a.lote_actual_id == int(lote_id): animales_destino.append(a)

        count = len(animales_destino)
        if count == 0: 
            return jsonify({"error": "No hay animales en el destino seleccionado"}), 400
        
        monto_individual = monto_total / count
        
        for a in animales_destino:
            nuevo_gasto = Gasto(fecha=fecha_gasto, concepto=f"{concepto} (Campaña)", monto=monto_individual, categoria="SANITARIO", animal_id=a.id)
            db.session.add(nuevo_gasto)
        
        db.session.commit()
        return jsonify({"mensaje": f"Gasto aplicado a {count} animales correctamente."})
    except Exception as e:
        print("ERROR GASTO MASIVO:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/evento_reproductivo_masivo', methods=['POST'])
def evento_reproductivo_masivo():
    try:
        d = request.json
        ids_animales = d.get('animales_ids', [])
        tipo = d['tipo']
        detalle = d.get('detalle', '')
        
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        
        # Manejo seguro de IDs opcionales
        prot_id = d.get('protocolo_id')
        if not prot_id or prot_id == "": prot_id = None
        
        gen_id = d.get('genetica_id')
        if not gen_id or gen_id == "": gen_id = None

        count = 0
        for aid in ids_animales:
            animal = Animal.query.get(aid)
            if animal:
                evento = EventoReproductivo(
                    animal_id=animal.id, tipo=tipo, fecha=fecha, detalle=detalle,
                    protocolo_id=prot_id, genetica_id=gen_id
                )
                db.session.add(evento)
                
                # Actualizar estado
                if tipo == 'INSEMINACION': animal.estado_reproductivo = 'INSEMINADA'
                elif tipo == 'TACTO': animal.estado_reproductivo = 'PREÑADA' if detalle == 'POSITIVO' else 'VACIA'
                elif tipo == 'PARTO': animal.estado_reproductivo = 'PARIDA'
                
                count += 1
        
        db.session.commit()
        return jsonify({"mensaje": f"Evento aplicado a {count} animales 🧬"})
    except Exception as e:
        print("ERROR REPRO MASIVO:", str(e))
        return jsonify({"error": str(e)}), 500

# [RESTO DE RUTAS CRUD BÁSICAS - COPIA LAS MISMAS DE SIEMPRE]
# Para ahorrar espacio aquí, asumo que el resto de las rutas (animales, lotes, silos, etc)
# se mantienen igual que en la versión anterior. Si necesitas que las repita, avísame.
# Asegúrate de mantener las rutas: resumen_general, liquidaciones, animales, silos, etc.

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy = datetime.utcnow()
        mes_actual = hoy.month
        anio_actual = hoy.year
        db.create_all()
        try: subquery_vendidos = db.session.query(Venta.animal_id)
        except: subquery_vendidos = []
        try: total_cabezas = db.session.query(Animal).filter(Animal.id.notin_(subquery_vendidos)).count()
        except: total_cabezas = 0
        try: total_hectareas = db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        except: total_hectareas = 0
        try: total_grano_acopiado = db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        except: total_grano_acopiado = 0
        try: gastos_mes = db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha) == mes_actual, extract('year', Gasto.fecha) == anio_actual).scalar() or 0
        except: gastos_mes = 0
        margen_mes = 0
        try:
            ventas_hacienda = Venta.query.filter(extract('month', Venta.fecha) == mes_actual, extract('year', Venta.fecha) == anio_actual).all()
            for v in ventas_hacienda: margen_mes += (v.precio_total - (v.costo_historico or 0))
        except: pass
        lluvia_mes = 0
        try:
            lotes = Lote.query.all()
            if lotes:
                sumas = []
                for l in lotes:
                    s = db.session.query(func.sum(Lluvia.milimetros)).filter(Lluvia.lote_id == l.id, extract('month', Lluvia.fecha) == mes_actual).scalar() or 0
                    if s > 0: sumas.append(s)
                if sumas: lluvia_mes = sum(sumas) / len(sumas)
        except: pass
        return jsonify({ "cabezas": total_cabezas, "hectareas": round(total_hectareas, 1), "stock_granos": round(total_grano_acopiado, 0), "gastos_mes": round(gastos_mes, 2), "margen_mes": round(margen_mes, 2), "lluvia_mes": round(lluvia_mes, 1) })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    try:
        resultados = []
        contratos = ContratoCampo.query.all()
        hoy = datetime.utcnow()
        for contrato in contratos:
            lote = Lote.query.get(contrato.lote_id)
            if not lote: continue 
            cosechas = Cosecha.query.filter_by(lote_id=contrato.lote_id).all()
            total_kilos = sum(c.kilos_totales for c in cosechas) if cosechas else 0
            gastos = Gasto.query.filter_by(lote_id=contrato.lote_id).all()
            total_gastos = sum(g.monto for g in gastos) if gastos else 0
            kilos_dueno = total_kilos * (contrato.porcentaje_dueno / 100) if contrato.tipo == 'APARCERIA' else 0
            kilos_propios = total_kilos - kilos_dueno
            lluvias = Lluvia.query.filter_by(lote_id=lote.id).filter(extract('month', Lluvia.fecha) == hoy.month).all()
            acumulado_lluvia = sum(l.milimetros for l in lluvias) if lluvias else 0
            resultados.append({ "id": contrato.id, "lote_id": lote.id, "lote": lote.nombre, "hectareas": lote.hectareas, "propietario": contrato.propietario, "tipo": contrato.tipo, "porcentaje": contrato.porcentaje_dueno, "total_cosechado": total_kilos, "kilos_propios": kilos_propios, "kilos_dueno": kilos_dueno, "total_gastos": total_gastos, "lat": lote.latitud, "lng": lote.longitud, "lluvia_mes": acumulado_lluvia })
        return jsonify(resultados)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        lista = []
        todos = Animal.query.all()
        for vaca in todos:
            if Venta.query.filter_by(animal_id=vaca.id).first(): continue
            lista.append({ "id": vaca.id, "caravana": vaca.caravana, "raza": vaca.raza, "categoria": vaca.categoria, "peso_actual": 0, "estado_reproductivo": getattr(vaca, 'estado_reproductivo', 'VACIA'), "lote_actual_id": vaca.lote_actual_id })
        return jsonify(lista)
    except: return jsonify([])

@app.route('/api/silos', methods=['GET'])
def obtener_silos():
    try:
        silos = Silo.query.all()
        return jsonify([{ "id": s.id, "nombre": s.nombre, "tipo": s.tipo, "contenido": s.contenido, "capacidad": s.capacidad, "kilos_actuales": s.kilos_actuales, "lat": s.latitud, "lng": s.longitud } for s in silos])
    except: return jsonify([])

@app.route('/api/nuevo_contrato', methods=['POST'])
def crear_contrato():
    d = request.json
    try:
        nl = Lote(nombre=d['nombreLote'], hectareas=float(d['hectareas']), latitud=d.get('lat'), longitud=d.get('lng'))
        db.session.add(nl); db.session.commit()
        nc = ContratoCampo(lote_id=nl.id, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=float(d['porcentaje']))
        db.session.add(nc); db.session.commit()
        return jsonify({"mensaje": "Guardado"}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_animal', methods=['POST'])
def nuevo_animal():
    d = request.json
    try:
        animal = Animal(caravana=d['caravana'], rfid=d.get('rfid'), raza=d['raza'], categoria=d['categoria'], estado_reproductivo='VACIA')
        db.session.add(animal); db.session.commit()
        if d.get('peso_inicial'): db.session.add(Peso(animal_id=animal.id, kilos=float(d['peso_inicial']))); db.session.commit()
        return jsonify({"mensaje": "Creado"}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_silo', methods=['POST'])
def nuevo_silo():
    d = request.json
    nuevo = Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=float(d['capacidad']), latitud=d.get('lat'), longitud=d.get('lng'))
    db.session.add(nuevo); db.session.commit()
    return jsonify({"mensaje": "Silo creado"}), 201

# --- ARRANQUE ---
if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')