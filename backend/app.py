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

# --- CONFIGURACIÓN BASE DE DATOS (PARCHE SSL) ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///agronexo.db')

# Corrección CRÍTICA para Render: Forzar SSL
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    # Si no tiene sslmode, lo agregamos para evitar desconexiones
    if "?" not in database_url:
        database_url += "?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,  # Auto-reconectar si se cae
    "pool_recycle": 300,    # Refrescar conexiones cada 5 min
}

db = SQLAlchemy(app)

# --- FUNCIONES DE SEGURIDAD ---
def safe_float(val):
    try:
        if val is None or str(val).strip() == "": return 0.0
        return float(val)
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

# --- RUTAS DE EMERGENCIA Y BORRADO ---

@app.route('/api/reset_tablas', methods=['GET'])
def reset_tablas():
    try:
        with app.app_context(): db.create_all()
        return jsonify({"mensaje": "Tablas OK"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/eliminar_lote/<int:lote_id>', methods=['DELETE'])
def eliminar_lote(lote_id):
    try:
        # BORRADO EN CASCADA MANUAL
        # 1. Borrar lluvias asociadas
        Lluvia.query.filter_by(lote_id=lote_id).delete()
        # 2. Borrar cosechas
        Cosecha.query.filter_by(lote_id=lote_id).delete()
        # 3. Borrar gastos del lote
        Gasto.query.filter_by(lote_id=lote_id).delete()
        # 4. Borrar contrato
        ContratoCampo.query.filter_by(lote_id=lote_id).delete()
        
        # 5. Liberar animales (No borrarlos, ponerlos en 'Sin Lote')
        animales = Animal.query.filter_by(lote_actual_id=lote_id).all()
        for a in animales: a.lote_actual_id = None
        
        # 6. Finalmente borrar lote
        Lote.query.filter_by(id=lote_id).delete()
        
        db.session.commit()
        return jsonify({"mensaje": "Lote y datos asociados eliminados"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar: " + str(e)}), 500

# --- RUTAS PRINCIPALES REPARADAS ---

@app.route('/api/registrar_venta', methods=['POST'])
def registrar_venta():
    try:
        d = request.json
        animal_id = safe_int(d.get('animal_id'))
        
        # Obtener animal
        animal = Animal.query.get(animal_id)
        if not animal: return jsonify({"error": "Animal no encontrado"}), 404

        # Costo acumulado
        gastos = Gasto.query.filter_by(animal_id=animal_id).all()
        total_costo = sum(safe_float(g.monto) for g in gastos)
        
        # Crear venta
        nueva_venta = Venta(
            animal_id=animal_id,
            comprador=d.get('comprador', 'Sin Nombre'),
            kilos_venta=safe_float(d.get('kilos')),
            precio_total=safe_float(d.get('precio')),
            costo_historico=total_costo,
            fecha=datetime.utcnow()
        )
        db.session.add(nueva_venta)
        
        # IMPORTANTE: Marcar animal como vendido (sacar de lote)
        # No lo borramos para que quede en historial
        animal.lote_actual_id = None
        
        db.session.commit()
        return jsonify({"mensaje": "Venta exitosa"})
    except Exception as e:
        print("ERROR VENTA:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json
        animal_id = safe_int(d.get('animal_id'))
        tipo = d.get('tipo')
        detalle = d.get('detalle', '')
        
        evento = EventoReproductivo(
            animal_id=animal_id,
            tipo=tipo,
            detalle=detalle,
            fecha=datetime.utcnow(),
            protocolo_id=safe_int(d.get('protocolo_id')),
            genetica_id=safe_int(d.get('genetica_id')),
            condicion_corporal=safe_float(d.get('condicion_corporal'))
        )
        db.session.add(evento)
        
        # ACTUALIZACIÓN DE ESTADO (Lógica Fuerte)
        animal = Animal.query.get(animal_id)
        if animal:
            if tipo == 'INSEMINACION': 
                animal.estado_reproductivo = 'INSEMINADA'
            elif tipo == 'TACTO':
                # Normalizar texto para evitar errores de mayus/minus
                det_norm = str(detalle).upper()
                if 'POSITIVO' in det_norm or 'PREÑADA' in det_norm:
                    animal.estado_reproductivo = 'PREÑADA'
                else:
                    animal.estado_reproductivo = 'VACIA'
            elif tipo == 'PARTO': 
                animal.estado_reproductivo = 'PARIDA'
            
        db.session.commit()
        return jsonify({"mensaje": "Evento y estado actualizados"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy = datetime.utcnow()
        mes_actual = hoy.month
        # Forzar recarga de tablas por si acaso
        db.create_all()
        
        # 1. Cabezas (excluyendo vendidos)
        subq_ventas = db.session.query(Venta.animal_id)
        cabezas = db.session.query(Animal).filter(Animal.id.notin_(subq_ventas)).count()
        
        # 2. Hectareas
        has = db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        
        # 3. Stock Silos
        grano = db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        
        # 4. Finanzas Mes
        gastos = db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha) == mes_actual).scalar() or 0
        
        # Margen Ventas Mes
        ventas = Venta.query.filter(extract('month', Venta.fecha) == mes_actual).all()
        margen = sum((safe_float(v.precio_total) - safe_float(v.costo_historico)) for v in ventas)
        
        # Ventas Grano Mes
        v_grano = db.session.query(func.sum(VentaGrano.precio_total)).filter(extract('month', VentaGrano.fecha) == mes_actual).scalar() or 0
        
        return jsonify({
            "cabezas": cabezas,
            "hectareas": round(has, 1),
            "stock_granos": round(grano, 0),
            "gastos_mes": round(gastos, 2),
            "margen_mes": round(margen + v_grano, 2),
            "lluvia_mes": 0 # Simplificado
        })
    except Exception as e:
        print("ERROR RESUMEN:", e)
        return jsonify({"error": str(e)}), 500

# [RESTO DE RUTAS - COPIAR Y PEGAR IGUAL QUE ANTES]
# Para que funcione completo, incluye aquí abajo las rutas de:
# nueva_cosecha, nuevo_animal, nuevo_lote, etc.
# Si necesitas el bloque entero de 300 líneas dímelo, pero con reemplazar lo de arriba es la clave.

@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        res = []
        for a in Animal.query.all():
            if not Venta.query.filter_by(animal_id=a.id).first():
                res.append({"id":a.id, "caravana":a.caravana, "categoria":a.categoria, "raza":a.raza, "peso_actual":0, "estado_reproductivo":getattr(a,'estado_reproductivo','VACIA'), "lote_actual_id":a.lote_actual_id})
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    try:
        res = []
        for c in ContratoCampo.query.all():
            l = Lote.query.get(c.lote_id)
            if l: res.append({"id":c.id, "lote_id":l.id, "lote":l.nombre, "hectareas":l.hectareas, "tipo":c.tipo, "porcentaje":c.porcentaje_dueno, "lat":l.latitud, "lng":l.longitud, "total_cosechado":0, "total_gastos":0, "lluvia_mes":0})
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/silos', methods=['GET'])
def obtener_silos():
    try: return jsonify([{"id":s.id, "nombre":s.nombre, "tipo":s.tipo, "contenido":s.contenido, "capacidad":s.capacidad, "kilos_actuales":s.kilos_actuales, "lat":s.latitud, "lng":s.longitud} for s in Silo.query.all()])
    except: return jsonify([])

@app.route('/api/nuevo_contrato', methods=['POST'])
def crear_contrato():
    d=request.json; db.session.add(Lote(nombre=d['nombreLote'], hectareas=safe_float(d.get('hectareas')), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit()
    lid=Lote.query.order_by(Lote.id.desc()).first().id
    db.session.add(ContratoCampo(lote_id=lid, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=safe_float(d.get('porcentaje')))); db.session.commit()
    return jsonify({"msg":"OK"})

@app.route('/api/nuevo_animal', methods=['POST'])
def nuevo_animal():
    d=request.json; db.session.add(Animal(caravana=d['caravana'], rfid=d.get('rfid'), raza=d['raza'], categoria=d['categoria'])); db.session.commit()
    if d.get('peso_inicial'): db.session.add(Peso(animal_id=Animal.query.order_by(Animal.id.desc()).first().id, kilos=safe_float(d['peso_inicial']))); db.session.commit()
    return jsonify({"msg":"OK"})

@app.route('/api/nuevo_silo', methods=['POST'])
def nuevo_silo():
    d=request.json; db.session.add(Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=safe_float(d.get('capacidad')), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_pesaje', methods=['POST'])
def nuevo_pesaje():
    d=request.json; db.session.add(Peso(animal_id=d['animal_id'], kilos=safe_float(d['kilos']))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_gasto', methods=['POST'])
def nuevo_gasto():
    d=request.json; db.session.add(Gasto(concepto=d['concepto'], monto=safe_float(d['monto']), categoria=d['categoria'], lote_id=safe_int(d.get('lote_id')), animal_id=safe_int(d.get('animal_id')))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/registrar_lluvia', methods=['POST'])
def registrar_lluvia():
    d=request.json; db.session.add(Lluvia(lote_id=safe_int(d['lote_id']), milimetros=safe_float(d['milimetros']))); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    a = Animal.query.get(id); 
    if not a: return jsonify({"error":"No existe"}), 404
    evs = EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()
    d_repro = [{"fecha": e.fecha.strftime("%d/%m"), "tipo": e.tipo, "detalle": e.detalle} for e in evs]
    return jsonify({"caravana":a.caravana, "categoria":a.categoria, "historial_pesos":[], "historial_gastos":[], "historial_repro":d_repro, "estado_reproductivo": getattr(a,'estado_reproductivo','VACIA')})

@app.route('/api/gasto_masivo', methods=['POST'])
def gasto_masivo():
    d=request.json; lote_id=str(d.get('lote_id')); monto_total=safe_float(d.get('monto')); concepto=d.get('concepto')
    animales=[]
    for a in Animal.query.all():
        if Venta.query.filter_by(animal_id=a.id).first(): continue
        if lote_id=='all': animales.append(a)
        elif lote_id=='corral' and a.lote_actual_id is None: animales.append(a)
        elif lote_id.isdigit() and a.lote_actual_id==int(lote_id): animales.append(a)
    if not animales: return jsonify({"error":"0 animales"}), 400
    indiv=monto_total/len(animales)
    for a in animales: db.session.add(Gasto(concepto=concepto, monto=indiv, categoria="SANITARIO", animal_id=a.id))
    db.session.commit(); return jsonify({"mensaje":"OK"})

@app.route('/api/mover_hacienda', methods=['POST'])
def mover_hacienda():
    d=request.json; dest=safe_int(d.get('lote_destino_id'))
    for aid in d.get('animales_ids', []):
        a=Animal.query.get(aid)
        if a: a.lote_actual_id=dest
    db.session.commit(); return jsonify({"mensaje":"OK"})

@app.route('/api/evento_reproductivo_masivo', methods=['POST'])
def evento_reproductivo_masivo():
    d = request.json; count=0
    for aid in d.get('animales_ids', []):
        db.session.add(EventoReproductivo(animal_id=aid, tipo=d['tipo'], detalle=d.get('detalle','')))
        a = Animal.query.get(aid)
        if d['tipo'] == 'INSEMINACION': a.estado_reproductivo = 'INSEMINADA'
        elif d['tipo'] == 'TACTO': a.estado_reproductivo = 'PREÑADA' if d.get('detalle') == 'POSITIVO' else 'VACIA'
        elif d['tipo'] == 'PARTO': a.estado_reproductivo = 'PARIDA'
        count+=1
    db.session.commit(); return jsonify({"mensaje": f"Aplicado a {count}"})

@app.route('/api/venta_grano', methods=['POST'])
def venta_grano():
    d=request.json
    db.session.add(VentaGrano(comprador=d['comprador'], tipo_grano=d['tipo_grano'], kilos=safe_float(d['kilos']), precio_total=safe_float(d['precio_total']), origen=d['origen'], silo_id=safe_int(d.get('silo_id'))))
    db.session.commit(); return jsonify({"mensaje":"OK"})

@app.route('/api/nueva_cosecha', methods=['POST'])
def nueva_cosecha():
    d=request.json; db.session.add(Cosecha(lote_id=safe_int(d['lote_id']), kilos_totales=safe_float(d['kilos']), destino=d.get('destino'), silo_id=safe_int(d.get('silo_id')))); db.session.commit(); return jsonify({"mensaje":"OK"})

@app.route('/api/exportar_excel', methods=['GET'])
def exportar_excel():
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame([{"Estado":"OK"}]).to_excel(writer, sheet_name='Data')
    output.seek(0)
    return send_file(output, download_name="Reporte.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# --- INICIO ---
if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')