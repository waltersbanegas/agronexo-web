import os
import pandas as pd
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import extract, func, text # 🆕 IMPORTANTE: Agregamos 'text'
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

# --- RUTAS ---

@app.route('/api/resumen_general', methods=['GET'])
def resumen_general():
    try:
        hoy = datetime.utcnow()
        mes_actual = hoy.month
        anio_actual = hoy.year
        # Verificar tablas antes de consultar
        db.create_all()
        
        subquery_vendidos = db.session.query(Venta.animal_id)
        total_cabezas = db.session.query(Animal).filter(Animal.id.notin_(subquery_vendidos)).count()
        total_hectareas = db.session.query(func.sum(Lote.hectareas)).scalar() or 0
        total_grano_acopiado = db.session.query(func.sum(Silo.kilos_actuales)).scalar() or 0
        gastos_mes = db.session.query(func.sum(Gasto.monto)).filter(extract('month', Gasto.fecha) == mes_actual, extract('year', Gasto.fecha) == anio_actual).scalar() or 0
        ventas_hacienda = Venta.query.filter(extract('month', Venta.fecha) == mes_actual, extract('year', Venta.fecha) == anio_actual).all()
        margen_hacienda = sum((v.precio_total - v.costo_historico) for v in ventas_hacienda)
        ventas_grano = db.session.query(func.sum(VentaGrano.precio_total)).filter(extract('month', VentaGrano.fecha) == mes_actual, extract('year', VentaGrano.fecha) == anio_actual).scalar() or 0
        lotes = Lote.query.all()
        sumas_lotes = []
        for l in lotes:
            suma = db.session.query(func.sum(Lluvia.milimetros)).filter(Lluvia.lote_id == l.id, extract('month', Lluvia.fecha) == mes_actual, extract('year', Lluvia.fecha) == anio_actual).scalar() or 0
            if suma > 0: sumas_lotes.append(suma)
        lluvia_promedio = sum(sumas_lotes) / len(sumas_lotes) if len(sumas_lotes) > 0 else 0
        return jsonify({ "cabezas": total_cabezas, "hectareas": round(total_hectareas, 1), "stock_granos": round(total_grano_acopiado, 0), "gastos_mes": round(gastos_mes, 2), "margen_mes": round(margen_hacienda + ventas_grano, 2), "lluvia_mes": round(lluvia_promedio, 1) })
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
            total_kilos = sum(c.kilos_totales for c in cosechas)
            if contrato.tipo == 'APARCERIA': kilos_dueno = total_kilos * (contrato.porcentaje_dueno / 100)
            else: kilos_dueno = 0 
            kilos_propios = total_kilos - kilos_dueno
            gastos = Gasto.query.filter_by(lote_id=contrato.lote_id).all()
            total_gastos = sum(g.monto for g in gastos)
            cant_animales = Animal.query.filter_by(lote_actual_id=lote.id).count()
            lluvias_mes = Lluvia.query.filter_by(lote_id=lote.id).filter(extract('month', Lluvia.fecha) == hoy.month, extract('year', Lluvia.fecha) == hoy.year).all()
            acumulado_lluvia = sum(l.milimetros for l in lluvias_mes)
            resultados.append({ "id": contrato.id, "lote_id": lote.id, "lote": lote.nombre, "hectareas": lote.hectareas, "propietario": contrato.propietario, "tipo": contrato.tipo, "porcentaje": contrato.porcentaje_dueno, "total_cosechado": total_kilos, "kilos_propios": kilos_propios, "kilos_dueno": kilos_dueno, "total_gastos": total_gastos, "lat": lote.latitud, "lng": lote.longitud, "animales_count": cant_animales, "lluvia_mes": acumulado_lluvia })
        return jsonify(resultados)
    except Exception as e: return jsonify({"error": str(e)}), 500

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
            peso_act = 0; gdp = 0; ult = "Sin datos"
            ubicacion = "En Corral / Sin Lote"
            if vaca.lote_actual_id:
                lote = Lote.query.get(vaca.lote_actual_id)
                if lote: ubicacion = lote.nombre
            if pesajes:
                peso_act = pesajes[0].kilos
                ult = pesajes[0].fecha.strftime("%d/%m/%Y")
                if len(pesajes) > 1:
                    dif_k = peso_act - pesajes[1].kilos
                    dif_d = (pesajes[0].fecha - pesajes[1].fecha).days
                    if dif_d > 0: gdp = dif_k / dif_d
            lista.append({ 
                "id": vaca.id, "caravana": vaca.caravana, "raza": vaca.raza, 
                "categoria": vaca.categoria, "peso_actual": peso_act, 
                "gdp": round(gdp, 3), "ultimo_pesaje": ult, "costo_acumulado": total_gastos, 
                "ubicacion": ubicacion, "lote_actual_id": vaca.lote_actual_id,
                "estado_reproductivo": getattr(vaca, 'estado_reproductivo', 'VACIA') # Safe access
            })
        return jsonify(lista)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_evento_reproductivo', methods=['POST'])
def nuevo_evento_reproductivo():
    try:
        d = request.json
        animal_id = d['animal_id']
        tipo = d['tipo']
        detalle = d['detalle']
        fecha = datetime.utcnow()
        if d.get('fecha'):
            try: fecha = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        evento = EventoReproductivo(animal_id=animal_id, tipo=tipo, detalle=detalle, fecha=fecha)
        db.session.add(evento)
        animal = Animal.query.get(animal_id)
        if tipo == 'INSEMINACION': animal.estado_reproductivo = 'INSEMINADA'
        elif tipo == 'TACTO':
            if detalle == 'POSITIVO': animal.estado_reproductivo = 'PREÑADA'
            else: animal.estado_reproductivo = 'VACIA'
        elif tipo == 'PARTO': animal.estado_reproductivo = 'PARIDA'
        db.session.commit()
        return jsonify({"mensaje": "Evento registrado y estado actualizado"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        animal = Animal.query.get(id)
        if not animal: return jsonify({"error": "No existe"}), 404
        pesajes = Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()
        data_pesos = [{"fecha": p.fecha.strftime("%d/%m"), "kilos": p.kilos} for p in pesajes]
        gastos = Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()
        data_gastos = [{"fecha": g.fecha.strftime("%d/%m/%Y"), "concepto": g.concepto, "monto": g.monto} for g in gastos]
        eventos_repro = EventoReproductivo.query.filter_by(animal_id=id).order_by(EventoReproductivo.fecha.desc()).all()
        data_repro = [{"fecha": e.fecha.strftime("%d/%m/%Y"), "tipo": e.tipo, "detalle": e.detalle} for e in eventos_repro]
        return jsonify({ "caravana": animal.caravana, "historial_pesos": data_pesos, "historial_gastos": data_gastos, "historial_repro": data_repro, "estado_reproductivo": getattr(animal, 'estado_reproductivo', 'VACIA') })
    except Exception as e: return jsonify({"error": str(e)}), 500

# [OTRAS RUTAS DE LOGÍSTICA]
@app.route('/api/silos', methods=['GET'])
def obtener_silos():
    silos = Silo.query.all()
    return jsonify([{ "id": s.id, "nombre": s.nombre, "tipo": s.tipo, "contenido": s.contenido, "capacidad": s.capacidad, "kilos_actuales": s.kilos_actuales, "lat": s.latitud, "lng": s.longitud } for s in silos])

@app.route('/api/nuevo_silo', methods=['POST'])
def nuevo_silo():
    d = request.json
    lat = float(d['lat']) if d.get('lat') else None
    lng = float(d['lng']) if d.get('lng') else None
    nuevo = Silo(nombre=d['nombre'], tipo=d['tipo'], contenido=d['contenido'], capacidad=float(d['capacidad']), latitud=lat, longitud=lng)
    db.session.add(nuevo); db.session.commit()
    return jsonify({"mensaje": "Silo creado"}), 201

@app.route('/api/nueva_cosecha', methods=['POST'])
def nueva_cosecha():
    try:
        d = request.json
        kilos = float(d['kilos'])
        destino = d.get('destino', 'VENTA')
        silo_id = d.get('silo_id')
        nueva = Cosecha(lote_id=d['lote_id'], kilos_totales=kilos, destino=destino, silo_id=silo_id)
        db.session.add(nueva)
        if destino == 'SILO' and silo_id:
            silo = Silo.query.get(silo_id)
            if silo: silo.kilos_actuales += kilos
        db.session.commit()
        return jsonify({"mensaje": "Cosecha registrada"}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/venta_grano', methods=['POST'])
def venta_grano():
    try:
        d = request.json
        kilos = float(d['kilos'])
        precio_total = float(d['precio_total'])
        origen = d['origen']
        silo_id = d.get('silo_id')
        if origen == 'SILO' and silo_id:
            silo = Silo.query.get(silo_id)
            if not silo: return jsonify({"error": "Silo no encontrado"}), 404
            if silo.kilos_actuales < kilos: return jsonify({"error": "Stock insuficiente en silo"}), 400
            silo.kilos_actuales -= kilos
        venta = VentaGrano(fecha=datetime.utcnow(), comprador=d['comprador'], tipo_grano=d['tipo_grano'], kilos=kilos, precio_total=precio_total, origen=origen, silo_id=silo_id)
        db.session.add(venta); db.session.commit()
        return jsonify({"mensaje": "Venta de grano registrada"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_lluvia', methods=['POST'])
def registrar_lluvia():
    try:
        d = request.json
        fecha_lluvia = datetime.utcnow()
        if d.get('fecha'):
            try: fecha_lluvia = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        nueva_lluvia = Lluvia(lote_id=d['lote_id'], milimetros=float(d['milimetros']), fecha=fecha_lluvia)
        db.session.add(nueva_lluvia); db.session.commit()
        return jsonify({"mensaje": "Lluvia registrada correctamente"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/gasto_masivo', methods=['POST'])
def gasto_masivo():
    try:
        d = request.json
        lote_id = d.get('lote_id')
        monto_total = float(d['monto'])
        concepto = d['concepto']
        fecha_gasto = datetime.utcnow()
        if d.get('fecha'):
            try: fecha_gasto = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        animales_destino = []
        todos = Animal.query.all()
        for a in todos:
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            if lote_id == 'all': animales_destino.append(a)
            elif lote_id == 'corral': 
                if a.lote_actual_id is None: animales_destino.append(a)
            else: 
                if a.lote_actual_id == int(lote_id): animales_destino.append(a)
        count = len(animales_destino)
        if count == 0: return jsonify({"error": "No hay animales en ese destino"}), 400
        monto_individual = monto_total / count
        for a in animales_destino:
            nuevo_gasto = Gasto(fecha=fecha_gasto, concepto=f"{concepto} (Campaña)", monto=monto_individual, categoria="SANITARIO", animal_id=a.id)
            db.session.add(nuevo_gasto)
        db.session.commit()
        return jsonify({"mensaje": f"Aplicado a {count} animales. ${round(monto_individual, 2)} c/u"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/registrar_venta', methods=['POST'])
def registrar_venta():
    try:
        d = request.json
        animal_id = d['animal_id']
        fecha_venta = datetime.utcnow()
        if d.get('fecha'):
            try: fecha_venta = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        gastos = Gasto.query.filter_by(animal_id=animal_id).all()
        total_costo = sum(g.monto for g in gastos)
        precio_total_recibido = float(d['precio'])
        nueva_venta = Venta(animal_id=animal_id, fecha=fecha_venta, comprador=d['comprador'], kilos_venta=float(d['kilos']), precio_total=precio_total_recibido, costo_historico=total_costo)
        db.session.add(nueva_venta)
        animal = Animal.query.get(animal_id)
        animal.lote_actual_id = None
        db.session.commit()
        margen = precio_total_recibido - total_costo
        return jsonify({"mensaje": "Venta exitosa", "margen": margen})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/mover_hacienda', methods=['POST'])
def mover_hacienda():
    try:
        d = request.json
        lote_destino = d.get('lote_destino_id')
        ids_animales = d.get('animales_ids', [])
        for animal_id in ids_animales:
            animal = Animal.query.get(animal_id)
            if animal: animal.lote_actual_id = lote_destino
        db.session.commit()
        return jsonify({"mensaje": "Hacienda movida exitosamente"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/exportar_excel', methods=['GET'])
def exportar_excel():
    try:
        data_agro = []
        contratos = ContratoCampo.query.all()
        for c in contratos:
            lote = Lote.query.get(c.lote_id)
            if not lote: continue
            cosechas = Cosecha.query.filter_by(lote_id=lote.id).all()
            total_kilos = sum(cos.kilos_totales for cos in cosechas)
            gastos = Gasto.query.filter_by(lote_id=lote.id).all()
            total_gastos = sum(g.monto for g in gastos)
            lluvias = Lluvia.query.filter_by(lote_id=lote.id).all()
            total_lluvia_historica = sum(l.milimetros for l in lluvias)
            data_agro.append({ "Lote": lote.nombre, "Hectáreas": lote.hectareas, "Total Cosechado (kg)": total_kilos, "Gastos ($)": total_gastos, "Lluvia (mm)": total_lluvia_historica })

        data_ganaderia = []
        animales = Animal.query.all()
        for a in animales:
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            pesajes = Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).all()
            peso_actual = pesajes[0].kilos if pesajes else 0
            gastos_animal = Gasto.query.filter_by(animal_id=a.id).all()
            total_gastos_animal = sum(g.monto for g in gastos_animal)
            data_ganaderia.append({ "Caravana": a.caravana, "Categoría": a.categoria, "Peso (kg)": peso_actual, "Costo Acum ($)": total_gastos_animal, "Estado Repro": getattr(a, 'estado_reproductivo', 'VACIA') })

        data_silos = []
        silos = Silo.query.all()
        for s in silos:
            data_silos.append({ "Silo": s.nombre, "Tipo": s.tipo, "Grano": s.contenido, "Capacidad (Tn)": s.capacidad, "STOCK ACTUAL (Kg)": s.kilos_actuales })

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(data_agro).to_excel(writer, sheet_name='Agricultura', index=False)
            pd.DataFrame(data_ganaderia).to_excel(writer, sheet_name='Hacienda', index=False)
            pd.DataFrame(data_silos).to_excel(writer, sheet_name='Stock Granos', index=False)
        output.seek(0)
        return send_file(output, download_name="Reporte_AgroNexo.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- CRUD BÁSICO ---
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

@app.route('/api/editar_lote/<int:lote_id>', methods=['PUT'])
def editar_lote(lote_id):
    d = request.json
    lote = Lote.query.get(lote_id)
    if lote:
        lote.nombre = d['nombreLote']
        lote.hectareas = float(d['hectareas'])
        if d.get('lat'): lote.latitud = float(d['lat']); lote.longitud = float(d['lng'])
        c = ContratoCampo.query.filter_by(lote_id=lote.id).first()
        if c: c.propietario = d['propietario']; c.tipo = d['tipo']; c.porcentaje_dueno = float(d['porcentaje'])
        db.session.commit()
        return jsonify({"mensaje": "Actualizado"})
    return jsonify({"error": "No existe"}), 404

@app.route('/api/eliminar_lote/<int:lote_id>', methods=['DELETE'])
def eliminar_lote(lote_id):
    try:
        ContratoCampo.query.filter_by(lote_id=lote_id).delete()
        Gasto.query.filter_by(lote_id=lote_id).delete()
        Cosecha.query.filter_by(lote_id=lote_id).delete()
        Lote.query.filter_by(id=lote_id).delete()
        db.session.commit()
        return jsonify({"mensaje": "Eliminado"})
    except: return jsonify({"error": "Error"}), 500

@app.route('/api/nuevo_animal', methods=['POST'])
def nuevo_animal():
    d = request.json
    animal = Animal(caravana=d['caravana'], raza=d['raza'], categoria=d['categoria'], estado_reproductivo='VACIA')
    db.session.add(animal); db.session.commit()
    if d['peso_inicial']: db.session.add(Peso(animal_id=animal.id, kilos=float(d['peso_inicial']))); db.session.commit()
    return jsonify({"mensaje": "Creado"}), 201
    
@app.route('/api/nuevo_pesaje', methods=['POST'])
def nuevo_pesaje():
    d = request.json
    db.session.add(Peso(animal_id=d['animal_id'], kilos=float(d['kilos']))); db.session.commit()
    return jsonify({"mensaje": "Registrado"}), 201

@app.route('/api/nuevo_gasto', methods=['POST'])
def nuevo_gasto():
    d = request.json
    gasto = Gasto(concepto=d['concepto'], monto=float(d['monto']), categoria=d['categoria'], lote_id=d.get('lote_id'), animal_id=d.get('animal_id'))
    db.session.add(gasto); db.session.commit()
    return jsonify({"mensaje": "Gasto Guardado"}), 201

# --- BLOQUE DE REPARACIÓN DE BASE DE DATOS (AUTO-MIGRACIÓN) ---
with app.app_context():
    db.create_all() # Asegura que las tablas existan
    try:
        # Intenta agregar la columna si falta (PostgreSQL syntax)
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE animal ADD COLUMN IF NOT EXISTS estado_reproductivo VARCHAR(50) DEFAULT "VACIA";'))
            conn.commit()
            print("✅ Verificación de columna 'estado_reproductivo' completada.")
    except Exception as e:
        print("ℹ️ Nota de migración:", e)
# ---------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')