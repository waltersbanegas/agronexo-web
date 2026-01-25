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

# --- SEGURIDAD DE DATOS ---
def safe_float(val):
    try: return float(val) if val and str(val).strip() else 0.0
    except: return 0.0

def safe_int(val):
    try: return int(float(val)) if val and str(val).strip() else None
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
    caravana = db.Column(db.String(50), unique=True)
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

# --- RUTAS DE SISTEMA ---
@app.route('/api/reset_tablas', methods=['GET'])
def reset_tablas():
    with app.app_context(): db.create_all()
    return jsonify({"mensaje": "Tablas OK"})

@app.route('/api/purgar_agricultura', methods=['DELETE'])
def purgar_agricultura():
    try:
        db.session.query(Lluvia).delete(); db.session.query(Cosecha).delete(); db.session.query(ContratoCampo).delete()
        db.session.execute(text("UPDATE animal SET lote_actual_id = NULL"))
        db.session.query(Lote).delete(); db.session.commit()
        return jsonify({"mensaje": "Reset OK"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- RUTAS CRÍTICAS DE GANADERÍA ---

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        a = Animal.query.get(id)
        if not a: return jsonify({"error":"No existe"}), 404
        
        # Historial de Pesos (Ordenado para el gráfico)
        pesajes = Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()
        d_pesos = [{"fecha": p.fecha.strftime("%d/%m"), "kilos": p.kilos} for p in pesajes]
        
        gastos = Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()
        d_gastos = [{"fecha": g.fecha.strftime("%d/%m/%Y"), "concepto": g.concepto, "monto": g.monto} for g in gastos]
        
        evs = EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()
        d_repro = [{"fecha": e.fecha.strftime("%d/%m/%Y"), "tipo": e.tipo, "detalle": e.detalle} for e in evs]
        
        return jsonify({
            "caravana": a.caravana, 
            "categoria": a.categoria, 
            "historial_pesos": d_pesos, # Data del gráfico
            "historial_gastos": d_gastos, 
            "historial_repro": d_repro, 
            "estado_reproductivo": getattr(a,'estado_reproductivo','VACIA')
        })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json
        print("Evento Individual:", d) # Debug
        aid = safe_int(d.get('animal_id'))
        
        # 1. Registrar el evento
        ev = EventoReproductivo(
            animal_id=aid, 
            tipo=d['tipo'], 
            detalle=d.get('detalle',''), 
            fecha=datetime.utcnow(),
            protocolo_id=safe_int(d.get('protocolo_id')),
            genetica_id=safe_int(d.get('genetica_id'))
        )
        db.session.add(ev)
        
        # 2. Actualizar estado
        a = Animal.query.get(aid)
        if a:
            if d['tipo'] == 'INSEMINACION': 
                a.estado_reproductivo = 'INSEMINADA'
            elif d['tipo'] == 'TACTO': 
                a.estado_reproductivo = 'PREÑADA' if 'POSITIVO' in str(d.get('detalle')).upper() else 'VACIA'
            elif d['tipo'] == 'PARTO': 
                a.estado_reproductivo = 'PARIDA'
                
                # 3. NACIMIENTO AUTOMÁTICO (Sin try/except para ver si falla)
                # Generamos una caravana única usando timestamp para evitar colisiones
                ts = int(time.time())
                cria_caravana = f"CRIA-{a.caravana}-{ts}"[-15:] # Max 15 chars
                
                cria = Animal(
                    caravana=cria_caravana, 
                    categoria='Ternero', 
                    raza=a.raza, 
                    lote_actual_id=a.lote_actual_id,
                    fecha_ingreso=datetime.utcnow()
                )
                db.session.add(cria)
                print(f"Cria creada: {cria_caravana}") # Debug log
        
        db.session.commit()
        return jsonify({"mensaje": "Evento registrado correctamente"})
    except Exception as e:
        print("Error Repro:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/evento_reproductivo_masivo', methods=['POST'])
def evento_reproductivo_masivo():
    d = request.json
    count = 0
    try:
        for aid in d.get('animales_ids', []):
            # Reutilizamos lógica (simplificada para masivo)
            db.session.add(EventoReproductivo(animal_id=aid, tipo=d['tipo'], detalle=d.get('detalle',''), fecha=datetime.utcnow()))
            a = Animal.query.get(aid)
            if d['tipo'] == 'INSEMINACION': a.estado_reproductivo = 'INSEMINADA'
            elif d['tipo'] == 'TACTO': a.estado_reproductivo = 'PREÑADA' if 'POSITIVO' in str(d.get('detalle')).upper() else 'VACIA'
            elif d['tipo'] == 'PARTO': a.estado_reproductivo = 'PARIDA'
            count+=1
        db.session.commit()
        return jsonify({"mensaje": f"Aplicado a {count}"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# [RESTO DE RUTAS CRUD STANDARD]
@app.route('/api/mover_hacienda', methods=['POST'])
def mover_hacienda():
    d=request.json; dest=safe_int(d.get('lote_destino_id')); c=0
    for aid in d.get('animales_ids', []):
        a=Animal.query.get(aid)
        if a: a.lote_actual_id=dest; c+=1
    db.session.commit(); return jsonify({"mensaje":f"Movidos {c}"})

@app.route('/api/registrar_lluvia', methods=['POST'])
def registrar_lluvia():
    d=request.json; db.session.add(Lluvia(lote_id=safe_int(d.get('lote_id')), milimetros=safe_float(d.get('milimetros')), fecha=datetime.utcnow()))
    db.session.commit(); return jsonify({"mensaje":"Lluvia OK"})

@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    try:
        res=[]; hoy=datetime.utcnow(); lotes=Lote.query.all()
        for l in lotes:
            c=ContratoCampo.query.filter_by(lote_id=l.id).first()
            lluvias=Lluvia.query.filter_by(lote_id=l.id).filter(extract('month', Lluvia.fecha)==hoy.month).all()
            mm=sum(x.milimetros for x in lluvias)
            cos=Cosecha.query.filter_by(lote_id=l.id).all(); kg=sum(x.kilos_totales for x in cos)
            gas=Gasto.query.filter_by(lote_id=l.id).all(); gts=sum(x.monto for x in gas)
            cid=c.id if c else (l.id*9999)
            res.append({"id":cid,"lote_id":l.id,"lote":l.nombre,"hectareas":l.hectareas,"tipo":c.tipo if c else "S/C","propietario":c.propietario if c else "-","porcentaje":c.porcentaje_dueno if c else 0,"lat":l.latitud,"lng":l.longitud,"total_cosechado":kg,"total_gastos":gts,"lluvia_mes":mm})
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/animales', methods=['GET'])
def animales():
    res=[]
    for a in Animal.query.all():
        if not Venta.query.filter_by(animal_id=a.id).first():
            loc="En Corral / Sin Lote"
            if a.lote_actual_id:
                l=Lote.query.get(a.lote_actual_id)
                if l: loc=l.nombre
            up=Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).first()
            res.append({"id":a.id,"caravana":a.caravana,"categoria":a.categoria,"raza":a.raza,"peso_actual":up.kilos if up else 0,"estado_reproductivo":getattr(a,'estado_reproductivo','VACIA'),"lote_actual_id":a.lote_actual_id,"ubicacion":loc})
    return jsonify(res)

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy=datetime.utcnow(); mes=hoy.month; db.session.execute(text('SELECT 1'))
        subq=db.session.query(Venta.animal_id)
        cabezas=db.session.query(Animal).filter(Animal.id.notin_(subq)).count()
        has=db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        grano=db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        gastos=db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha)==mes).scalar() or 0
        return jsonify({"cabezas":cabezas,"hectareas":round(has,1),"stock_granos":round(grano,0),"gastos_mes":round(gastos,2),"margen_mes":0,"lluvia_mes":0})
    except: return jsonify({"cabezas":0})

# CRUD SIMPLE
@app.route('/api/silos', methods=['GET'])
def silos(): return jsonify([{"id":s.id, "nombre":s.nombre, "tipo":s.tipo, "contenido":s.contenido, "capacidad":s.capacidad, "kilos_actuales":s.kilos_actuales, "lat":s.latitud, "lng":s.longitud} for s in Silo.query.all()])
@app.route('/api/nuevo_contrato', methods=['POST'])
def nc(): d=request.json; db.session.add(Lote(nombre=d['nombreLote'], hectareas=safe_float(d.get('hectareas')), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit(); db.session.add(ContratoCampo(lote_id=Lote.query.order_by(Lote.id.desc()).first().id, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=safe_float(d.get('porcentaje')))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nuevo_animal', methods=['POST'])
def na(): d=request.json; db.session.add(Animal(caravana=d['caravana'], rfid=d.get('rfid'), raza=d['raza'], categoria=d['categoria'])); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nuevo_silo', methods=['POST'])
def ns(): d=request.json; db.session.add(Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=safe_float(d.get('capacidad')), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nuevo_pesaje', methods=['POST'])
def np(): d=request.json; db.session.add(Peso(animal_id=d['animal_id'], kilos=safe_float(d['kilos']), fecha=datetime.utcnow())); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nuevo_gasto', methods=['POST'])
def ng(): d=request.json; db.session.add(Gasto(fecha=datetime.utcnow(), concepto=d['concepto'], monto=safe_float(d['monto']), categoria=d['categoria'], lote_id=safe_int(d.get('lote_id')), animal_id=safe_int(d.get('animal_id')))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/editar_lote/<int:id>', methods=['PUT'])
def el(id): l=Lote.query.get(id); d=request.json; l.nombre=d['nombreLote']; l.hectareas=safe_float(d['hectareas']); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/venta_grano', methods=['POST'])
def vg(): d=request.json; db.session.add(VentaGrano(comprador=d['comprador'], tipo_grano=d['tipo_grano'], kilos=safe_float(d['kilos']), precio_total=safe_float(d['precio_total']), origen=d['origen'], silo_id=safe_int(d.get('silo_id')))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/nueva_cosecha', methods=['POST'])
def nco(): d=request.json; db.session.add(Cosecha(lote_id=safe_int(d['lote_id']), kilos_totales=safe_float(d['kilos']), destino=d.get('destino'), silo_id=safe_int(d.get('silo_id')))); db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/registrar_venta', methods=['POST'])
def rv(): d=request.json; db.session.add(Venta(animal_id=d['animal_id'], comprador=d['comprador'], kilos_venta=safe_float(d['kilos']), precio_total=safe_float(d['precio']), costo_historico=0)); a=Animal.query.get(d['animal_id']); a.lote_actual_id=None; db.session.commit(); return jsonify({"msg":"OK"})
@app.route('/api/exportar_excel', methods=['GET'])
def ee(): output=BytesIO(); pd.DataFrame([{"Estado":"OK"}]).to_excel(output); output.seek(0); return send_file(output, download_name="Reporte.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
@app.route('/api/gasto_masivo', methods=['POST'])
def gm(): 
    d=request.json; lote_id=str(d.get('lote_id')); monto=safe_float(d.get('monto')); animales=[]
    for a in Animal.query.all():
        if Venta.query.filter_by(animal_id=a.id).first(): continue
        if lote_id=='all': animales.append(a)
        elif lote_id=='corral' and a.lote_actual_id is None: animales.append(a)
        elif lote_id.isdigit() and a.lote_actual_id==int(lote_id): animales.append(a)
    for a in animales: db.session.add(Gasto(concepto=d.get('concepto'), monto=monto/len(animales), categoria="SANITARIO", animal_id=a.id))
    db.session.commit(); return jsonify({"msg":"OK"})

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')