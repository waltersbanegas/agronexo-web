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

# --- FUNCIONES DE SEGURIDAD (PARA QUE NO FALLE) ---
def safe_float(val):
    try:
        if val is None or str(val).strip() == "": return 0.0
        return float(val)
    except: return 0.0

def safe_int(val):
    try:
        if val is None or str(val).strip() == "": return None
        return int(float(val)) # float por si viene "1.0"
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

# --- RUTAS RESTAURADAS Y CORREGIDAS ---

@app.route('/api/nueva_cosecha', methods=['POST'])
def nueva_cosecha():
    try:
        d = request.json
        print("Registrando cosecha:", d) # Debug log
        
        # 🛡️ CORRECCIÓN: Manejo seguro de ID de Silo
        silo_id = safe_int(d.get('silo_id'))
        
        nueva = Cosecha(
            lote_id=safe_int(d['lote_id']),
            kilos_totales=safe_float(d['kilos']),
            destino=d.get('destino', 'VENTA'),
            silo_id=silo_id
        )
        db.session.add(nueva)
        
        # Si va a silo, sumar stock
        if d.get('destino') == 'SILO' and silo_id:
            silo = Silo.query.get(silo_id)
            if silo: silo.kilos_actuales += safe_float(d['kilos'])
            
        db.session.commit()
        return jsonify({"mensaje": "Cosecha registrada"})
    except Exception as e:
        print("ERROR COSECHA:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json
        print("Evento Repro:", d) # Debug log
        
        animal_id = safe_int(d.get('animal_id'))
        if not animal_id: return jsonify({"error": "Falta ID animal"}), 400
        
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
            
        # Crear evento
        evento = EventoReproductivo(
            animal_id=animal_id,
            tipo=d['tipo'],
            detalle=d.get('detalle', ''),
            fecha=fecha,
            protocolo_id=safe_int(d.get('protocolo_id')),
            genetica_id=safe_int(d.get('genetica_id')),
            condicion_corporal=safe_float(d.get('condicion_corporal'))
        )
        db.session.add(evento)
        
        # Actualizar estado de la vaca
        animal = Animal.query.get(animal_id)
        if animal:
            if d['tipo'] == 'INSEMINACION': animal.estado_reproductivo = 'INSEMINADA'
            elif d['tipo'] == 'TACTO':
                detalle = d.get('detalle', '')
                animal.estado_reproductivo = 'PREÑADA' if detalle == 'POSITIVO' else 'VACIA'
            elif d['tipo'] == 'PARTO': animal.estado_reproductivo = 'PARIDA'
            
        db.session.commit()
        return jsonify({"mensaje": "Evento registrado"})
    except Exception as e:
        print("ERROR REPRO:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/exportar_excel', methods=['GET'])
def exportar_excel():
    try:
        # Agricultura
        data_agro = []
        lotes = Lote.query.all()
        for l in lotes:
            gasto = db.session.query(func.sum(Gasto.monto)).filter_by(lote_id=l.id).scalar() or 0
            cosecha = db.session.query(func.sum(Cosecha.kilos_totales)).filter_by(lote_id=l.id).scalar() or 0
            data_agro.append({"Lote": l.nombre, "Has": l.hectareas, "Gastos": gasto, "Cosecha (Kg)": cosecha})

        # Ganadería
        data_ganaderia = []
        animales = Animal.query.all()
        for a in animales:
            if not Venta.query.filter_by(animal_id=a.id).first():
                gasto = db.session.query(func.sum(Gasto.monto)).filter_by(animal_id=a.id).scalar() or 0
                ultimo_peso = Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).first()
                peso = ultimo_peso.kilos if ultimo_peso else 0
                data_ganaderia.append({
                    "Caravana": a.caravana, "Categoria": a.categoria, "Raza": a.raza,
                    "Estado Repro": a.estado_reproductivo, "Peso Actual": peso, "Costo Acum": gasto
                })

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(data_agro).to_excel(writer, sheet_name='Agricultura', index=False)
            pd.DataFrame(data_ganaderia).to_excel(writer, sheet_name='Ganaderia', index=False)
            
        output.seek(0)
        return send_file(output, download_name="Reporte_AgroNexo.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# [RESTO DE RUTAS CRUD BÁSICAS - IGUALES QUE ANTES]

@app.route('/api/editar_lote/<int:lote_id>', methods=['PUT'])
def editar_lote(lote_id):
    d = request.json
    try:
        lote = Lote.query.get(lote_id)
        if not lote: return jsonify({"error": "No existe"}), 404
        lote.nombre = d['nombreLote']
        lote.hectareas = safe_float(d['hectareas'])
        if d.get('lat') and d.get('lng'):
            lote.latitud = float(d['lat']); lote.longitud = float(d['lng'])
        c = ContratoCampo.query.filter_by(lote_id=lote.id).first()
        if c:
            c.propietario = d['propietario']; c.tipo = d['tipo']; c.porcentaje_dueno = safe_float(d['porcentaje'])
        db.session.commit()
        return jsonify({"mensaje": "Lote actualizado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/eliminar_lote/<int:lote_id>', methods=['DELETE'])
def eliminar_lote(lote_id):
    try:
        ContratoCampo.query.filter_by(lote_id=lote_id).delete()
        Gasto.query.filter_by(lote_id=lote_id).delete()
        Cosecha.query.filter_by(lote_id=lote_id).delete()
        Lluvia.query.filter_by(lote_id=lote_id).delete()
        animales = Animal.query.filter_by(lote_actual_id=lote_id).all()
        for a in animales: a.lote_actual_id = None
        Lote.query.filter_by(id=lote_id).delete()
        db.session.commit()
        return jsonify({"mensaje": "Lote eliminado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        animal = Animal.query.get(id)
        if not animal: return jsonify({"error": "No existe"}), 404
        pesajes = Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()
        data_pesos = [{"fecha": p.fecha.strftime("%d/%m/%y"), "kilos": p.kilos} for p in pesajes]
        gastos = Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()
        data_gastos = [{"fecha": g.fecha.strftime("%d/%m/%Y"), "concepto": g.concepto, "monto": g.monto} for g in gastos]
        eventos = EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()
        data_repro = [{"fecha": e.fecha.strftime("%d/%m/%Y"), "tipo": e.tipo, "detalle": e.detalle} for e in eventos]
        return jsonify({ 
            "caravana": animal.caravana, "categoria": animal.categoria, 
            "historial_pesos": data_pesos, "historial_gastos": data_gastos, 
            "historial_repro": data_repro, "estado_reproductivo": getattr(animal, 'estado_reproductivo', 'VACIA') 
        })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_lluvia', methods=['POST'])
def registrar_lluvia():
    try:
        d = request.json
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        db.session.add(Lluvia(lote_id=safe_int(d['lote_id']), milimetros=safe_float(d['milimetros']), fecha=fecha))
        db.session.commit()
        return jsonify({"mensaje": "Lluvia registrada"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy = datetime.utcnow()
        mes_actual = hoy.month
        db.create_all()
        try: subquery_vendidos = db.session.query(Venta.animal_id)
        except: subquery_vendidos = []
        try: total_cabezas = db.session.query(Animal).filter(Animal.id.notin_(subquery_vendidos)).count()
        except: total_cabezas = 0
        try: total_hectareas = db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        except: total_hectareas = 0
        try: total_grano_acopiado = db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        except: total_grano_acopiado = 0
        try: gastos_mes = db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha) == mes_actual).scalar() or 0
        except: gastos_mes = 0
        margen_mes = 0
        try:
            ventas_hacienda = Venta.query.filter(extract('month', Venta.fecha) == mes_actual).all()
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
        res = []
        hoy = datetime.utcnow()
        for c in ContratoCampo.query.all():
            l = Lote.query.get(c.lote_id)
            if l: 
                lluvias = Lluvia.query.filter_by(lote_id=l.id).filter(extract('month', Lluvia.fecha) == hoy.month).all()
                mm = sum(ll.milimetros for ll in lluvias)
                cosechas = Cosecha.query.filter_by(lote_id=l.id).all()
                kg = sum(cos.kilos_totales for cos in cosechas)
                gastos = Gasto.query.filter_by(lote_id=l.id).all()
                gts = sum(gs.monto for gs in gastos)
                res.append({ "id":c.id, "lote_id":l.id, "lote":l.nombre, "hectareas":l.hectareas, "tipo":c.tipo, "porcentaje":c.porcentaje_dueno, "lat":l.latitud, "lng":l.longitud, "total_cosechado":kg, "total_gastos":gts, "lluvia_mes":mm, "kilos_propios":0, "kilos_dueno":0 })
        return jsonify(res)
    except: return jsonify([])

@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        res = []
        for a in Animal.query.all():
            if not Venta.query.filter_by(animal_id=a.id).first():
                ultimo_peso = Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).first()
                peso_val = ultimo_peso.kilos if ultimo_peso else 0
                res.append({ "id":a.id, "caravana":a.caravana, "categoria":a.categoria, "raza":a.raza, "peso_actual":peso_val, "estado_reproductivo":getattr(a,'estado_reproductivo','VACIA'), "lote_actual_id":a.lote_actual_id })
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
    d=request.json; db.session.add(Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=safe_float(d['capacidad']), latitud=d.get('lat'), longitud=d.get('lng'))); db.session.commit()
    return jsonify({"msg":"OK"})

@app.route('/api/nuevo_pesaje', methods=['POST'])
def nuevo_pesaje():
    d=request.json
    fecha = datetime.utcnow()
    if d.get('fecha'):
        try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
        except: pass
    db.session.add(Peso(animal_id=d['animal_id'], kilos=safe_float(d['kilos']), fecha=fecha)); db.session.commit(); return jsonify({"msg":"OK"})

@app.route('/api/nuevo_gasto', methods=['POST'])
def nuevo_gasto():
    d=request.json
    fecha = datetime.utcnow()
    if d.get('fecha'):
        try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
        except: pass
    db.session.add(Gasto(fecha=fecha, concepto=d['concepto'], monto=safe_float(d['monto']), categoria=d['categoria'], lote_id=safe_int(d.get('lote_id')), animal_id=safe_int(d.get('animal_id')))); db.session.commit(); return jsonify({"msg":"OK"})

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

@app.route('/api/gasto_masivo', methods=['POST'])
def gasto_masivo():
    try:
        d = request.json
        lote_id = str(d.get('lote_id'))
        monto_total = safe_float(d.get('monto'))
        concepto = d.get('concepto', 'Gasto Masivo')
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        animales = []
        for a in Animal.query.all():
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            if lote_id == 'all': animales.append(a)
            elif lote_id == 'corral' and a.lote_actual_id is None: animales.append(a)
            elif lote_id.isdigit() and a.lote_actual_id == int(lote_id): animales.append(a)
        if not animales: return jsonify({"error": "Sin animales"}), 400
        indiv = monto_total / len(animales)
        for a in animales: db.session.add(Gasto(fecha=fecha, concepto=concepto, monto=indiv, categoria="SANITARIO", animal_id=a.id))
        db.session.commit(); return jsonify({"mensaje": f"Aplicado a {len(animales)}"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/mover_hacienda', methods=['POST'])
def mover_hacienda():
    d=request.json; dest=safe_int(d.get('lote_destino_id'))
    for aid in d.get('animales_ids', []):
        a = Animal.query.get(aid)
        if a: a.lote_actual_id = dest
    db.session.commit(); return jsonify({"mensaje":"OK"})

@app.route('/api/venta_grano', methods=['POST'])
def venta_grano():
    try:
        d = request.json
        kilos = safe_float(d['kilos'])
        s_id = safe_int(d.get('silo_id'))
        if d['origen'] == 'SILO' and s_id:
            silo = Silo.query.get(s_id)
            if silo: silo.kilos_actuales -= kilos
        db.session.add(VentaGrano(comprador=d['comprador'], tipo_grano=d['tipo_grano'], kilos=kilos, precio_total=safe_float(d['precio_total']), origen=d['origen'], silo_id=s_id))
        db.session.commit()
        return jsonify({"mensaje": "Venta OK"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- INICIO ---
if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')