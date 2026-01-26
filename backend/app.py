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

# --- CONFIGURACIÓN BASE DE DATOS ROBUSTA ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///agronexo.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    if "?" not in database_url:
        database_url += "?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True, "pool_recycle": 300}

db = SQLAlchemy(app)

# --- FUNCIONES DE SEGURIDAD (ANTI-CRASH) ---
def safe_float(val):
    try:
        if val is None: return 0.0
        # Reemplazar coma por punto por si viene formato español
        val_str = str(val).replace(',', '.')
        if val_str.strip() == "": return 0.0
        return float(val_str)
    except: return 0.0

def safe_int(val):
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

# --- RUTAS PRINCIPALES Y LÓGICA DE NEGOCIO ---

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy = datetime.utcnow(); mes=hoy.month
        # Forzar chequeo de conexión
        db.session.execute(text('SELECT 1')) 
        
        # Calcular stock vivo real
        subq_ventas = db.session.query(Venta.animal_id)
        cabezas = db.session.query(Animal).filter(Animal.id.notin_(subq_ventas)).count()
        
        # Calcular hectareas solo de lotes existentes
        has = db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        
        grano = db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        gastos = db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha) == mes).scalar() or 0
        
        ventas = Venta.query.filter(extract('month', Venta.fecha) == mes).all()
        margen = sum((safe_float(v.precio_total) - safe_float(v.costo_historico)) for v in ventas)
        
        v_grano = db.session.query(func.sum(VentaGrano.precio_total)).filter(extract('month', VentaGrano.fecha) == mes).scalar() or 0
        
        return jsonify({
            "cabezas": cabezas,
            "hectareas": round(has, 1),
            "stock_granos": round(grano, 0),
            "gastos_mes": round(gastos, 2),
            "margen_mes": round(margen + v_grano, 2),
            "lluvia_mes": 0 
        })
    except Exception as e:
        print("Error resumen:", e)
        return jsonify({"cabezas":0, "hectareas":0, "stock_granos":0, "gastos_mes":0, "margen_mes":0})

@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        res = []
        # Traer todos los animales que NO estén vendidos
        animales_activos = db.session.query(Animal).filter(Animal.id.notin_(db.session.query(Venta.animal_id))).all()
        
        for a in animales_activos:
            # Obtener nombre del lote para mostrar en la tarjeta
            ubicacion = "En Corral / Sin Lote"
            if a.lote_actual_id:
                lote = Lote.query.get(a.lote_actual_id)
                if lote: ubicacion = lote.nombre
            
            # Obtener último peso
            ultimo_peso = Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).first()
            peso_val = ultimo_peso.kilos if ultimo_peso else 0
            
            res.append({
                "id": a.id,
                "caravana": a.caravana,
                "categoria": a.categoria,
                "raza": a.raza,
                "peso_actual": peso_val,
                "estado_reproductivo": getattr(a, 'estado_reproductivo', 'VACIA'),
                "lote_actual_id": a.lote_actual_id,
                "ubicacion": ubicacion
            })
        return jsonify(res)
    except Exception as e:
        print("Error animales:", e)
        return jsonify([])

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        a = Animal.query.get(id)
        if not a: return jsonify({"error": "No existe"}), 404
        
        # Historiales ordenados
        pesos = Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()
        d_pesos = [{"fecha": p.fecha.strftime("%d/%m"), "kilos": p.kilos} for p in pesos]
        
        gastos = Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()
        d_gastos = [{"fecha": g.fecha.strftime("%d/%m/%Y"), "concepto": g.concepto, "monto": g.monto} for g in gastos]
        
        evs = EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()
        d_repro = [{"fecha": e.fecha.strftime("%d/%m/%Y"), "tipo": e.tipo, "detalle": e.detalle} for e in evs]
        
        return jsonify({
            "id": a.id, # IMPORTANTE: Devolver ID para que el frontend lo use en Venta/Repro
            "caravana": a.caravana,
            "categoria": a.categoria,
            "raza": a.raza,
            "rfid": a.rfid or "",
            "historial_pesos": d_pesos,
            "historial_gastos": d_gastos,
            "historial_repro": d_repro,
            "estado_reproductivo": getattr(a, 'estado_reproductivo', 'VACIA')
        })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    try:
        res = []
        hoy = datetime.utcnow()
        # Iterar sobre LOTES para mostrar todo (incluido lo que no tiene contrato)
        for l in Lote.query.all():
            c = ContratoCampo.query.filter_by(lote_id=l.id).first()
            
            # Datos climáticos y financieros del lote
            lluvias = Lluvia.query.filter_by(lote_id=l.id).filter(extract('month', Lluvia.fecha) == hoy.month).all()
            mm = sum(x.milimetros for x in lluvias)
            
            cosechas = Cosecha.query.filter_by(lote_id=l.id).all()
            kg = sum(x.kilos_totales for x in cosechas)
            
            gastos = Gasto.query.filter_by(lote_id=l.id).all()
            gts = sum(x.monto for x in gastos)
            
            # Armar objeto seguro
            res.append({
                "id": c.id if c else (l.id * 9999), # ID temporal si no hay contrato
                "lote_id": l.id,
                "lote": l.nombre,
                "hectareas": l.hectareas,
                "tipo": c.tipo if c else "SIN CONTRATO",
                "propietario": c.propietario if c else "-",
                "porcentaje": c.porcentaje_dueno if c else 0,
                "lat": l.latitud,
                "lng": l.longitud,
                "total_cosechado": kg,
                "total_gastos": gts,
                "lluvia_mes": mm
            })
        return jsonify(res)
    except Exception as e: return jsonify([])

# --- ACCIONES DE CREACIÓN Y EDICIÓN ---

@app.route('/api/nuevo_contrato', methods=['POST'])
def crear_contrato():
    try:
        d = request.json
        # Crear Lote (usar 0.0 si no hay coordenadas para evitar error 500)
        lat = d.get('lat')
        lng = d.get('lng')
        
        nl = Lote(
            nombre=d['nombreLote'], 
            hectareas=safe_float(d['hectareas']), 
            latitud=lat if lat else None, 
            longitud=lng if lng else None
        )
        db.session.add(nl)
        db.session.commit()
        
        # Crear Contrato
        nc = ContratoCampo(
            lote_id=nl.id, 
            propietario=d['propietario'], 
            tipo=d['tipo'], 
            porcentaje_dueno=safe_float(d.get('porcentaje'))
        )
        db.session.add(nc)
        db.session.commit()
        return jsonify({"mensaje": "Lote creado correctamente"})
    except Exception as e:
        print("Error Nuevo Lote:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_venta', methods=['POST'])
def registrar_venta():
    try:
        d = request.json
        print("Venta:", d)
        
        aid = safe_int(d.get('animal_id'))
        if not aid: return jsonify({"error": "Falta ID Animal"}), 400
        
        # Calcular costos históricos para margen
        gastos = Gasto.query.filter_by(animal_id=aid).all()
        costo = sum(safe_float(g.monto) for g in gastos)
        
        precio = safe_float(d.get('precio'))
        kilos = safe_float(d.get('kilos'))
        
        # Registrar Venta
        venta = Venta(
            animal_id=aid, 
            comprador=d.get('comprador', 'Consumidor Final'), 
            kilos_venta=kilos, 
            precio_total=precio, 
            costo_historico=costo,
            fecha=datetime.utcnow()
        )
        db.session.add(venta)
        
        # Quitar del stock activo
        animal = Animal.query.get(aid)
        if animal: animal.lote_actual_id = None
        
        db.session.commit()
        return jsonify({"mensaje": "Venta registrada exitosamente", "margen": precio - costo})
    except Exception as e:
        print("Error Venta:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json
        aid = safe_int(d.get('animal_id'))
        
        ev = EventoReproductivo(
            animal_id=aid, 
            tipo=d['tipo'], 
            detalle=d.get('detalle',''), 
            fecha=datetime.utcnow(),
            protocolo_id=safe_int(d.get('protocolo_id')),
            genetica_id=safe_int(d.get('genetica_id'))
        )
        db.session.add(ev)
        
        a = Animal.query.get(aid)
        if a:
            if d['tipo'] == 'INSEMINACION': a.estado_reproductivo = 'INSEMINADA'
            elif d['tipo'] == 'TACTO': a.estado_reproductivo = 'PREÑADA' if 'POSITIVO' in str(d.get('detalle')).upper() else 'VACIA'
            elif d['tipo'] == 'PARTO': 
                a.estado_reproductivo = 'PARIDA'
                # Nacimiento Automático
                try:
                    ts = int(time.time())
                    cria = Animal(
                        caravana=f"CRIA-{a.caravana}-{str(ts)[-4:]}", 
                        categoria='Ternero', 
                        raza=a.raza, 
                        lote_actual_id=a.lote_actual_id,
                        fecha_ingreso=datetime.utcnow()
                    )
                    db.session.add(cria)
                except: pass
        
        db.session.commit()
        return jsonify({"mensaje": "Evento registrado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/editar_animal/<int:id>', methods=['PUT'])
def editar_animal(id):
    try:
        a = Animal.query.get(id)
        if not a: return jsonify({"error": "No existe"}), 404
        d = request.json
        a.caravana = d['caravana']
        a.rfid = d.get('rfid')
        a.categoria = d['categoria']
        a.raza = d['raza']
        db.session.commit()
        return jsonify({"mensaje": "Animal actualizado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/mover_hacienda', methods=['POST'])
def mover_hacienda():
    try:
        d = request.json
        dest = safe_int(d.get('lote_destino_id')) # safe_int devuelve None si es ""
        count = 0
        for aid in d.get('animales_ids', []):
            a = Animal.query.get(aid)
            if a: 
                a.lote_actual_id = dest
                count += 1
        db.session.commit()
        return jsonify({"mensaje": f"Movimiento exitoso ({count} animales)"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_lluvia', methods=['POST'])
def registrar_lluvia():
    try:
        d = request.json
        lid = safe_int(d.get('lote_id'))
        if not lid: return jsonify({"error": "Selecciona un lote"}), 400
        db.session.add(Lluvia(lote_id=lid, milimetros=safe_float(d.get('milimetros')), fecha=datetime.utcnow()))
        db.session.commit()
        return jsonify({"mensaje": "Lluvia registrada"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/gasto_masivo', methods=['POST'])
def gasto_masivo():
    try:
        d = request.json
        lote_id = str(d.get('lote_id'))
        monto = safe_float(d.get('monto'))
        if monto <= 0: return jsonify({"error": "Monto inválido"}), 400
        
        animales = []
        todos = Animal.query.all()
        for a in todos:
            # Ignorar vendidos
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            
            if lote_id == 'all': animales.append(a)
            elif lote_id == 'corral': 
                if a.lote_actual_id is None: animales.append(a)
            elif lote_id.isdigit():
                if a.lote_actual_id == int(lote_id): animales.append(a)
        
        if not animales: return jsonify({"error": "No hay animales en el destino"}), 400
        
        indiv = monto / len(animales)
        for a in animales:
            db.session.add(Gasto(fecha=datetime.utcnow(), concepto=d.get('concepto'), monto=indiv, categoria="SANITARIO", animal_id=a.id))
        
        db.session.commit()
        return jsonify({"mensaje": "Gasto aplicado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/exportar_excel', methods=['GET'])
def exportar_excel():
    try:
        # Generar excel vacío si falla la consulta para evitar error 500
        data = [{"Estado": "Sistema Operativo", "Fecha": datetime.utcnow().strftime("%d/%m/%Y")}]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(data).to_excel(writer, sheet_name='Reporte')
        output.seek(0)
        return send_file(output, download_name="Reporte.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/purgar_agricultura', methods=['DELETE'])
def purgar_agricultura():
    try:
        db.session.query(Lluvia).delete()
        db.session.query(Cosecha).delete()
        db.session.query(ContratoCampo).delete()
        db.session.execute(text("UPDATE animal SET lote_actual_id = NULL"))
        db.session.query(Lote).delete()
        db.session.commit()
        return jsonify({"mensaje": "Agricultura Reiniciada"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/eliminar_lote/<int:lote_id>', methods=['DELETE'])
def eliminar_lote(lote_id):
    try:
        Lluvia.query.filter_by(lote_id=lote_id).delete()
        Cosecha.query.filter_by(lote_id=lote_id).delete()
        Gasto.query.filter_by(lote_id=lote_id).delete()
        ContratoCampo.query.filter_by(lote_id=lote_id).delete()
        animales = Animal.query.filter_by(lote_actual_id=lote_id).all()
        for a in animales: a.lote_actual_id = None
        Lote.query.filter_by(id=lote_id).delete()
        db.session.commit()
        return jsonify({"mensaje": "Eliminado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# [OTRAS RUTAS DE CREACIÓN BÁSICA]
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
@app.route('/api/silos', methods=['GET'])
def silos(): return jsonify([{"id":s.id, "nombre":s.nombre, "tipo":s.tipo, "contenido":s.contenido, "capacidad":s.capacidad, "kilos_actuales":s.kilos_actuales, "lat":s.latitud, "lng":s.longitud} for s in Silo.query.all()])

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')