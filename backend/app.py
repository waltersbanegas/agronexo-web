import os
import pandas as pd
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import extract, func, text
import random
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- CONFIGURACIÓN BASE DE DATOS ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///agronexo.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    if "?" not in database_url:
        database_url += "?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True, "pool_recycle": 300}

db = SQLAlchemy(app)

# --- FUNCIONES SEGURAS ---
def safe_float(val):
    try:
        if val is None: return 0.0
        val = str(val).replace(',', '.')
        return float(val) if val.strip() else 0.0
    except: return 0.0

def safe_int(val):
    try:
        if val is None: return None
        return int(float(str(val))) if str(val).strip() else None
    except: return None

# --- MODELOS ---
class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    hectareas = db.Column(db.Float)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

class ContratoCampo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    propietario = db.Column(db.String(100))
    tipo = db.Column(db.String(50)) 
    porcentaje_dueno = db.Column(db.Float)

class Silo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    contenido = db.Column(db.String(50))
    capacidad = db.Column(db.Float)
    kilos_actuales = db.Column(db.Float, default=0.0)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50))
    rfid = db.Column(db.String(50), nullable=True)
    categoria = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    lote_actual_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True)
    estado_reproductivo = db.Column(db.String(50), default='VACIA')
    estado_general = db.Column(db.String(50), default='ACTIVO') # ACTIVO, VENDIDO, BAJA, CONSUMO

class Baja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(50)) # VENTA, ROBO, MUERTE, CONSUMO, DONACION
    detalle = db.Column(db.String(200), nullable=True)
    valor_percibido = db.Column(db.Float, default=0.0) # Solo para ventas

class Peso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    kilos = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    categoria = db.Column(db.String(50))
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=True)

class Cosecha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    kilos_totales = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    destino = db.Column(db.String(50))
    silo_id = db.Column(db.Integer, db.ForeignKey('silo.id'), nullable=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    milimetros = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class VentaGrano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    comprador = db.Column(db.String(100))
    tipo_grano = db.Column(db.String(50))
    kilos = db.Column(db.Float)
    precio_total = db.Column(db.Float)
    origen = db.Column(db.String(50))
    silo_id = db.Column(db.Integer, db.ForeignKey('silo.id'), nullable=True)

class EventoReproductivo(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    tipo = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    costo_dosis = db.Column(db.Float)

class Protocolo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    descripcion = db.Column(db.String(200))
    costo_estimado = db.Column(db.Float)

# --- RUTA MAESTRA DE RESET ---
@app.route('/api/reset_fabrica', methods=['POST'])
def reset_fabrica():
    """Borra TODO y recrea la estructura limpia"""
    try:
        db.drop_all()
        db.create_all()
        return jsonify({"mensaje": "SISTEMA RESTAURADO. Base de datos limpia y lista."})
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- RUTAS PRINCIPALES ---

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy = datetime.utcnow(); mes=hoy.month
        # Solo contar animales ACTIVOS
        cabezas = Animal.query.filter_by(estado_general='ACTIVO').count()
        has = db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        grano = db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        gastos = db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha) == mes).scalar() or 0
        
        # Margen: Suma de ventas (Bajas por venta + Granos) - Costos
        bajas_venta = Baja.query.filter(extract('month', Baja.fecha) == mes, Baja.motivo == 'VENTA').all()
        ingresos_hacienda = sum(b.valor_percibido for b in bajas_venta)
        ingresos_grano = db.session.query(func.sum(VentaGrano.precio_total)).filter(extract('month', VentaGrano.fecha) == mes).scalar() or 0
        
        return jsonify({
            "cabezas": cabezas, "hectareas": round(has, 1), "stock_granos": round(grano, 0),
            "gastos_mes": round(gastos, 2), "margen_mes": round((ingresos_hacienda + ingresos_grano) - gastos, 2), "lluvia_mes": 0 
        })
    except: return jsonify({"cabezas":0, "hectareas":0})

@app.route('/api/registrar_baja', methods=['POST'])
def registrar_baja():
    try:
        d = request.json
        aid = safe_int(d.get('animal_id'))
        motivo = d.get('motivo') # VENTA, ROBO, ETC
        valor = safe_float(d.get('precio')) if motivo == 'VENTA' else 0.0
        detalle = d.get('comprador') if motivo == 'VENTA' else d.get('detalle', '')
        
        # Crear registro de baja
        baja = Baja(animal_id=aid, motivo=motivo, detalle=detalle, valor_percibido=valor, fecha=datetime.utcnow())
        db.session.add(baja)
        
        # Actualizar animal
        animal = Animal.query.get(aid)
        if animal:
            animal.estado_general = motivo # Guardamos el motivo como estado (VENDIDO, ROBO, etc)
            animal.lote_actual_id = None   # Sacar del lote
            
        db.session.commit()
        return jsonify({"mensaje": f"Baja registrada por {motivo}"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        res = []
        # Solo mostrar ACTIVOS
        for a in Animal.query.filter_by(estado_general='ACTIVO').all():
            loc = "Sin Lote"
            if a.lote_actual_id:
                l = Lote.query.get(a.lote_actual_id)
                if l: loc = l.nombre
            up = Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).first()
            res.append({
                "id": a.id, "caravana": a.caravana, "categoria": a.categoria, "raza": a.raza,
                "peso_actual": up.kilos if up else 0, "estado_reproductivo": getattr(a,'estado_reproductivo','VACIA'),
                "lote_actual_id": a.lote_actual_id, "ubicacion": loc
            })
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        a = Animal.query.get(id)
        if not a: return jsonify({"error": "No existe"}), 404
        
        pesos = [{"fecha": p.fecha.strftime("%d/%m"), "kilos": p.kilos} for p in Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()]
        gastos = [{"fecha": g.fecha.strftime("%d/%m"), "concepto": g.concepto, "monto": g.monto} for g in Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()]
        evs = [{"fecha": e.fecha.strftime("%d/%m"), "tipo": e.tipo, "detalle": e.detalle} for e in EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()]
        
        return jsonify({
            "id": a.id, "caravana": a.caravana, "categoria": a.categoria, "raza": a.raza, "rfid": a.rfid or "",
            "historial_pesos": pesos, "historial_gastos": gastos, "historial_repro": evs,
            "estado_reproductivo": a.estado_reproductivo
        })
    except: return jsonify({"error": "Error"}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json; aid = safe_int(d.get('animal_id'))
        db.session.add(EventoReproductivo(animal_id=aid, tipo=d['tipo'], detalle=d.get('detalle',''), fecha=datetime.utcnow()))
        a = Animal.query.get(aid)
        if a:
            if d['tipo'] == 'INSEMINACION': a.estado_reproductivo = 'INSEMINADA'
            elif d['tipo'] == 'TACTO': a.estado_reproductivo = 'PREÑADA' if 'POSITIVO' in str(d.get('detalle')).upper() else 'VACIA'
            elif d['tipo'] == 'PARTO': 
                a.estado_reproductivo = 'PARIDA'
                try: 
                    ts = int(time.time())
                    db.session.add(Animal(caravana=f"CRIA-{str(ts)[-4:]}", categoria='Ternero', raza=a.raza, lote_actual_id=a.lote_actual_id))
                except: pass
        db.session.commit(); return jsonify({"mensaje": "Evento OK"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# RUTAS GENERALES (Lotes, Lluvias, etc - BLINDADAS)
@app.route('/api/liquidaciones', methods=['GET'])
def liquidaciones():
    try:
        res = []
        for l in Lote.query.all():
            c = ContratoCampo.query.filter_by(lote_id=l.id).first()
            # Si no hay contrato, usar valores dummy para que no falle el frontend
            res.append({
                "id": c.id if c else l.id*999, "lote_id": l.id, "lote": l.nombre, "hectareas": l.hectareas,
                "tipo": c.tipo if c else "S/D", "propietario": c.propietario if c else "-", "porcentaje": c.porcentaje_dueno if c else 0,
                "lat": l.latitud, "lng": l.longitud, "total_cosechado": 0, "total_gastos": 0, "lluvia_mes": 0
            })
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/nuevo_contrato', methods=['POST'])
def nc(): 
    try:
        d=request.json
        # Permitir nulls en lat/lng
        nl = Lote(nombre=d['nombreLote'], hectareas=safe_float(d['hectareas']), latitud=safe_float(d.get('lat')), longitud=safe_float(d.get('lng')))
        db.session.add(nl); db.session.commit()
        db.session.add(ContratoCampo(lote_id=nl.id, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=safe_float(d.get('porcentaje'))))
        db.session.commit(); return jsonify({"mensaje":"OK"})
    except Exception as e: return jsonify({"error":str(e)}), 500

@app.route('/api/mover_hacienda', methods=['POST'])
def mv():
    try:
        d=request.json; dest=safe_int(d.get('lote_destino_id'))
        for aid in d.get('animales_ids', []):
            a=Animal.query.get(aid)
            if a: a.lote_actual_id=dest
        db.session.commit(); return jsonify({"mensaje":"OK"})
    except: return jsonify({"error":"Error moviendo"}), 500

@app.route('/api/registrar_lluvia', methods=['POST'])
def rl():
    try:
        d=request.json; lid=safe_int(d.get('lote_id'))
        if lid: db.session.add(Lluvia(lote_id=lid, milimetros=safe_float(d.get('milimetros')), fecha=datetime.utcnow())); db.session.commit()
        return jsonify({"mensaje":"OK"})
    except: return jsonify({"error":"Error lluvia"}), 500

@app.route('/api/eliminar_lote/<int:id>', methods=['DELETE'])
def el(id):
    try:
        # Borrar todo lo relacionado primero
        Lluvia.query.filter_by(lote_id=id).delete(); Cosecha.query.filter_by(lote_id=id).delete()
        Gasto.query.filter_by(lote_id=id).delete(); ContratoCampo.query.filter_by(lote_id=id).delete()
        db.session.execute(text(f"UPDATE animal SET lote_actual_id = NULL WHERE lote_actual_id = {id}"))
        Lote.query.filter_by(id=id).delete(); db.session.commit(); return jsonify({"mensaje":"OK"})
    except: return jsonify({"error":"Error borrar"}), 500

# RESTO DE CRUD
@app.route('/api/nuevo_animal', methods=['POST'])
def na(): d=request.json; db.session.add(Animal(caravana=d['caravana'], rfid=d.get('rfid'), raza=d['raza'], categoria=d['categoria'])); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/editar_animal/<int:id>', methods=['PUT'])
def ea(id): a=Animal.query.get(id); d=request.json; a.caravana=d['caravana']; a.rfid=d.get('rfid'); a.categoria=d['categoria']; a.raza=d['raza']; db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nuevo_pesaje', methods=['POST'])
def np(): d=request.json; db.session.add(Peso(animal_id=d['animal_id'], kilos=safe_float(d['kilos']), fecha=datetime.utcnow())); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/gasto_masivo', methods=['POST'])
def gm(): d=request.json; db.session.add(Gasto(fecha=datetime.utcnow(), concepto=d['concepto'], monto=safe_float(d['monto']))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nuevo_silo', methods=['POST'])
def ns(): d=request.json; db.session.add(Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=safe_float(d['capacidad']))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/silos', methods=['GET'])
def gs(): return jsonify([{"id":s.id, "nombre":s.nombre, "tipo":s.tipo, "contenido":s.contenido, "capacidad":s.capacidad, "kilos_actuales":s.kilos_actuales} for s in Silo.query.all()])
@app.route('/api/venta_grano', methods=['POST'])
def vg(): d=request.json; db.session.add(VentaGrano(comprador=d['comprador'], tipo_grano=d['tipo_grano'], kilos=safe_float(d['kilos']), precio_total=safe_float(d['precio_total']), origen=d['origen'], silo_id=safe_int(d.get('silo_id')))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nueva_cosecha', methods=['POST'])
def nco(): d=request.json; db.session.add(Cosecha(lote_id=safe_int(d['lote_id']), kilos_totales=safe_float(d['kilos']))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/exportar_excel', methods=['GET'])
def ee(): 
    out=BytesIO(); pd.DataFrame([{"Estado":"OK"}]).to_excel(out); out.seek(0)
    return send_file(out, download_name="Reporte.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')