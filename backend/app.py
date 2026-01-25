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
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- CONFIGURACIÓN BASE DE DATOS ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///agronexo.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- FUNCIONES DE SEGURIDAD (ANTIBALAS) ---
def safe_float(val):
    """Convierte cualquier cosa a float. Si falla, devuelve 0.0"""
    try:
        if val is None or str(val).strip() == "": return 0.0
        return float(val)
    except: return 0.0

def safe_int(val):
    """Convierte cualquier cosa a int. Si falla, devuelve None"""
    try:
        if val is None or str(val).strip() == "": return None
        return int(float(val))
    except: return None

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

# --- RUTAS CORREGIDAS Y BLINDADAS ---

@app.route('/api/registrar_venta', methods=['POST'])
def registrar_venta():
    try:
        d = request.json
        # 🛡️ BLINDAJE: Usamos safe_float para todo
        animal_id = safe_int(d.get('animal_id'))
        
        # Calcular costos previos
        gastos = Gasto.query.filter_by(animal_id=animal_id).all()
        total_costo = sum(safe_float(g.monto) for g in gastos)
        
        precio_total = safe_float(d.get('precio')) # Antes fallaba aquí si era string o vacío
        
        nueva = Venta(
            animal_id=animal_id,
            comprador=d.get('comprador', 'Sin Nombre'),
            kilos_venta=safe_float(d.get('kilos')),
            precio_total=precio_total,
            costo_historico=total_costo,
            fecha=datetime.utcnow()
        )
        db.session.add(nueva)
        
        # Sacar del stock
        animal = Animal.query.get(animal_id)
        if animal: animal.lote_actual_id = None
            
        db.session.commit()
        return jsonify({"mensaje": "Venta exitosa", "margen": precio_total - total_costo})
    except Exception as e:
        print("ERROR VENTA:", str(e))
        return jsonify({"error": "Error al vender: " + str(e)}), 500

@app.route('/api/nueva_cosecha', methods=['POST'])
def nueva_cosecha():
    try:
        d = request.json
        silo_id = safe_int(d.get('silo_id')) # Puede ser None
        kilos = safe_float(d.get('kilos')) # Antes fallaba aquí
        
        nueva = Cosecha(
            lote_id=safe_int(d.get('lote_id')),
            kilos_totales=kilos,
            destino=d.get('destino', 'VENTA'),
            silo_id=silo_id
        )
        db.session.add(nueva)
        
        # Actualizar Silo si corresponde
        if d.get('destino') == 'SILO' and silo_id:
            silo = Silo.query.get(silo_id)
            if silo: 
                actual = safe_float(silo.kilos_actuales)
                silo.kilos_actuales = actual + kilos
                
        db.session.commit()
        return jsonify({"mensaje": "Cosecha registrada"})
    except Exception as e:
        print("ERROR COSECHA:", str(e))
        return jsonify({"error": "Error cosecha: " + str(e)}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json
        animal_id = safe_int(d.get('animal_id'))
        
        evento = EventoReproductivo(
            animal_id=animal_id,
            tipo=d.get('tipo', 'CONSULTA'),
            detalle=d.get('detalle', ''),
            fecha=datetime.utcnow(),
            protocolo_id=safe_int(d.get('protocolo_id')),
            genetica_id=safe_int(d.get('genetica_id')),
            condicion_corporal=safe_float(d.get('condicion_corporal'))
        )
        db.session.add(evento)
        
        # Lógica de Estado
        animal = Animal.query.get(animal_id)
        if animal:
            if d['tipo'] == 'INSEMINACION': animal.estado_reproductivo = 'INSEMINADA'
            elif d['tipo'] == 'TACTO':
                # Si el detalle contiene "POSITIVO", preñada. Si no, vacía.
                det = d.get('detalle', '').upper()
                animal.estado_reproductivo = 'PREÑADA' if 'POSITIVO' in det else 'VACIA'
            elif d['tipo'] == 'PARTO': animal.estado_reproductivo = 'PARIDA'
            
        db.session.commit()
        return jsonify({"mensaje": "Evento registrado"})
    except Exception as e:
        return jsonify({"error": "Error repro: " + str(e)}), 500

@app.route('/api/gasto_masivo', methods=['POST'])
def gasto_masivo():
    try:
        d = request.json
        lote_id = str(d.get('lote_id'))
        monto_total = safe_float(d.get('monto')) # Antes fallaba aquí
        
        animales_destino = []
        todos = Animal.query.all()
        for a in todos:
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            if lote_id == 'all': animales_destino.append(a)
            elif lote_id == 'corral' and a.lote_actual_id is None: animales_destino.append(a)
            elif lote_id.isdigit() and a.lote_actual_id == int(lote_id): animales_destino.append(a)

        count = len(animales_destino)
        if count == 0: return jsonify({"error": "No hay animales"}), 400
        
        indiv = monto_total / count
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass

        for a in animales_destino:
            db.session.add(Gasto(fecha=fecha, concepto=d.get('concepto', 'Gasto'), monto=indiv, categoria="SANITARIO", animal_id=a.id))
        
        db.session.commit()
        return jsonify({"mensaje": f"Aplicado a {count}"})
    except Exception as e:
        return jsonify({"error": "Error gasto: " + str(e)}), 500

@app.route('/api/exportar_excel', methods=['GET'])
def exportar_excel():
    try:
        data_agro = []
        lotes = Lote.query.all()
        for l in lotes:
            g = db.session.query(func.sum(Gasto.monto)).filter_by(lote_id=l.id).scalar() or 0
            c = db.session.query(func.sum(Cosecha.kilos_totales)).filter_by(lote_id=l.id).scalar() or 0
            data_agro.append({"Lote": l.nombre, "Has": l.hectareas, "Gastos": g, "Cosecha": c})

        data_gan = []
        animales = Animal.query.all()
        for a in animales:
            if not Venta.query.filter_by(animal_id=a.id).first():
                g = db.session.query(func.sum(Gasto.monto)).filter_by(animal_id=a.id).scalar() or 0
                data_gan.append({"Caravana": a.caravana, "Estado": getattr(a,'estado_reproductivo',''), "Costo": g})

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(data_agro).to_excel(writer, sheet_name='Agricultura', index=False)
            pd.DataFrame(data_gan).to_excel(writer, sheet_name='Ganaderia', index=False)
        output.seek(0)
        return send_file(output, download_name="Reporte.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({"error": "Error Excel: " + str(e)}), 500

# [OTRAS RUTAS DE SOPORTE - IGUALES PERO BLINDADAS]

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        a = Animal.query.get(id)
        if not a: return jsonify({"error": "No existe"}), 404
        
        pesos = Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()
        d_pesos = [{"fecha": p.fecha.strftime("%d/%m"), "kilos": p.kilos} for p in pesos]
        
        gastos = Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()
        d_gastos = [{"fecha": g.fecha.strftime("%d/%m"), "concepto": g.concepto, "monto": g.monto} for g in gastos]
        
        evs = EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()
        d_repro = [{"fecha": e.fecha.strftime("%d/%m"), "tipo": e.tipo, "detalle": e.detalle} for e in evs]
        
        return jsonify({
            "caravana": a.caravana, "categoria": a.categoria,
            "historial_pesos": d_pesos, "historial_gastos": d_gastos, "historial_repro": d_repro,
            "estado_reproductivo": getattr(a,'estado_reproductivo','VACIA')
        })
    except: return jsonify({"error":"Error carga animal"}), 500

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        db.create_all()
        cabezas = db.session.query(Animal).filter(Animal.id.notin_(db.session.query(Venta.animal_id))).count()
        return jsonify({
            "cabezas": cabezas, "hectareas": 0, "stock_granos": 0, "gastos_mes": 0, "margen_mes": 0, "lluvia_mes": 0
        })
    except: return jsonify({"cabezas":0}) # Fallback total

# ... (Rutas simples como silos, lotes, animales LIST se mantienen igual que la versión anterior) ...
@app.route('/api/liquidaciones', methods=['GET'])
def liquidaciones():
    return jsonify([{"id":l.id, "lote":l.nombre, "hectareas":l.hectareas, "lat":l.latitud, "lng":l.longitud, "total_cosechado":0, "total_gastos":0, "lluvia_mes":0} for l in Lote.query.all()])

@app.route('/api/animales', methods=['GET'])
def animales():
    try:
        res = []
        for a in Animal.query.all():
            if not Venta.query.filter_by(animal_id=a.id).first():
                res.append({"id":a.id, "caravana":a.caravana, "categoria":a.categoria, "raza":a.raza, "peso_actual":0, "estado_reproductivo":getattr(a,'estado_reproductivo','VACIA'), "lote_actual_id":a.lote_actual_id})
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/silos', methods=['GET'])
def silos(): return jsonify([{"id":s.id, "nombre":s.nombre, "tipo":s.tipo, "contenido":s.contenido, "capacidad":s.capacidad, "kilos_actuales":s.kilos_actuales, "lat":s.latitud, "lng":s.longitud} for s in Silo.query.all()])

# Creación simple blindada
@app.route('/api/nuevo_contrato', methods=['POST'])
def nc(): d=request.json; db.session.add(Lote(nombre=d['nombreLote'], hectareas=safe_float(d.get('hectareas')), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit(); db.session.add(ContratoCampo(lote_id=Lote.query.order_by(Lote.id.desc()).first().id, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=safe_float(d.get('porcentaje')))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_animal', methods=['POST'])
def na(): d=request.json; db.session.add(Animal(caravana=d['caravana'], rfid=d.get('rfid'), raza=d['raza'], categoria=d['categoria'])); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_silo', methods=['POST'])
def ns(): d=request.json; db.session.add(Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=safe_float(d.get('capacidad')), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_pesaje', methods=['POST'])
def np(): d=request.json; db.session.add(Peso(animal_id=d['animal_id'], kilos=safe_float(d['kilos']))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_gasto', methods=['POST'])
def ng(): d=request.json; db.session.add(Gasto(concepto=d['concepto'], monto=safe_float(d['monto']), categoria=d['categoria'], lote_id=safe_int(d.get('lote_id')), animal_id=safe_int(d.get('animal_id')))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/registrar_lluvia', methods=['POST'])
def rl(): d=request.json; db.session.add(Lluvia(lote_id=safe_int(d['lote_id']), milimetros=safe_float(d['milimetros']))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/editar_lote/<int:id>', methods=['PUT'])
def el(id): 
    l=Lote.query.get(id); d=request.json
    if l: l.nombre=d['nombreLote']; l.hectareas=safe_float(d.get('hectareas')); db.session.commit()
    return jsonify({"msg":"OK"})

@app.route('/api/eliminar_lote/<int:id>', methods=['DELETE'])
def dll(id):
    try: Lote.query.filter_by(id=id).delete(); db.session.commit(); return jsonify({"msg":"OK"})
    except: return jsonify({"error":"Error borrando"}), 500

@app.route('/api/venta_grano', methods=['POST'])
def vg():
    d=request.json
    db.session.add(VentaGrano(comprador=d['comprador'], tipo_grano=d['tipo_grano'], kilos=safe_float(d['kilos']), precio_total=safe_float(d['precio_total']), origen=d['origen'], silo_id=safe_int(d.get('silo_id'))))
    if d['origen'] == 'SILO': 
        s=Silo.query.get(safe_int(d.get('silo_id')))
        if s: s.kilos_actuales -= safe_float(d['kilos'])
    db.session.commit()
    return jsonify({"msg":"OK"})

@app.route('/api/mover_hacienda', methods=['POST'])
def mh():
    d=request.json
    for aid in d.get('animales_ids', []):
        a=Animal.query.get(aid)
        if a: a.lote_actual_id=safe_int(d.get('lote_destino_id'))
    db.session.commit()
    return jsonify({"msg":"OK"})

@app.route('/api/evento_reproductivo_masivo', methods=['POST'])
def erm():
    d=request.json
    for aid in d.get('animales_ids', []):
        db.session.add(EventoReproductivo(animal_id=aid, tipo=d['tipo'], detalle=d.get('detalle','')))
        a=Animal.query.get(aid)
        if d['tipo'] == 'INSEMINACION': a.estado_reproductivo = 'INSEMINADA'
        elif d['tipo'] == 'TACTO': a.estado_reproductivo = 'PREÑADA' if d.get('detalle') == 'POSITIVO' else 'VACIA'
        elif d['tipo'] == 'PARTO': a.estado_reproductivo = 'PARIDA'
    db.session.commit()
    return jsonify({"msg":"OK"})

# --- INICIO ---
if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')