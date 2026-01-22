import os
import pandas as pd
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import extract # Necesario para filtrar por mes
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

class Animal(db.Model):
    __tablename__ = 'animal'
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(20), unique=True)
    categoria = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    lote_actual_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=True)

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

# 🆕 NUEVA TABLA: LLUVIAS
class Lluvia(db.Model):
    __tablename__ = 'lluvia'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'))
    milimetros = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# --- RUTAS ---

@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    try:
        resultados = []
        contratos = ContratoCampo.query.all()
        # Fechas para el cálculo de lluvia mensual
        hoy = datetime.utcnow()
        mes_actual = hoy.month
        anio_actual = hoy.year

        for contrato in contratos:
            lote = Lote.query.get(contrato.lote_id)
            if not lote: continue 
            cosechas = Cosecha.query.filter_by(lote_id=contrato.lote_id).all()
            total_kilos = sum(c.kilos_totales for c in cosechas)
            if contrato.tipo == 'APARCERIA':
                kilos_dueno = total_kilos * (contrato.porcentaje_dueno / 100)
            else:
                kilos_dueno = 0 
            kilos_propios = total_kilos - kilos_dueno
            gastos = Gasto.query.filter_by(lote_id=contrato.lote_id).all()
            total_gastos = sum(g.monto for g in gastos)
            cant_animales = Animal.query.filter_by(lote_actual_id=lote.id).count()
            
            # 🆕 CÁLCULO DE LLUVIA ACUMULADA DEL MES
            lluvias_mes = Lluvia.query.filter_by(lote_id=lote.id).filter(
                extract('month', Lluvia.fecha) == mes_actual,
                extract('year', Lluvia.fecha) == anio_actual
            ).all()
            acumulado_lluvia = sum(l.milimetros for l in lluvias_mes)

            resultados.append({
                "id": contrato.id, "lote_id": lote.id, "lote": lote.nombre,
                "hectareas": lote.hectareas, "propietario": contrato.propietario,
                "tipo": contrato.tipo, "porcentaje": contrato.porcentaje_dueno,
                "total_cosechado": total_kilos, "kilos_propios": kilos_propios, 
                "kilos_dueno": kilos_dueno, "total_gastos": total_gastos,
                "lat": lote.latitud, "lng": lote.longitud, "animales_count": cant_animales,
                "lluvia_mes": acumulado_lluvia # 🆕 Enviamos el dato al frontend
            })
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
                "gdp": round(gdp, 3), "ultimo_pesaje": ult, 
                "costo_acumulado": total_gastos, "ubicacion": ubicacion,
                "lote_actual_id": vaca.lote_actual_id
            })
        return jsonify(lista)
    except Exception as e: return jsonify({"error": str(e)}), 500

# 🆕 REGISTRAR LLUVIA
@app.route('/api/registrar_lluvia', methods=['POST'])
def registrar_lluvia():
    try:
        d = request.json
        fecha_lluvia = datetime.utcnow()
        if d.get('fecha'):
            try: fecha_lluvia = datetime.strptime(d['fecha'], '%Y-%m-%d')
            except: pass
        
        nueva_lluvia = Lluvia(
            lote_id=d['lote_id'],
            milimetros=float(d['milimetros']),
            fecha=fecha_lluvia
        )
        db.session.add(nueva_lluvia)
        db.session.commit()
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

@app.route('/api/detalle_animal/<int:id>', methods=['GET'])
def detalle_animal(id):
    try:
        animal = Animal.query.get(id)
        if not animal: return jsonify({"error": "No existe"}), 404
        pesajes = Peso.query.filter_by(animal_id=id).order_by(Peso.fecha.asc()).all()
        data_pesos = [{"fecha": p.fecha.strftime("%d/%m"), "kilos": p.kilos} for p in pesajes]
        gastos = Gasto.query.filter_by(animal_id=id).order_by(Gasto.fecha.desc()).all()
        data_gastos = [{"fecha": g.fecha.strftime("%d/%m/%Y"), "concepto": g.concepto, "monto": g.monto} for g in gastos]
        return jsonify({ "caravana": animal.caravana, "historial_pesos": data_pesos, "historial_gastos": data_gastos })
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
            # 🆕 Agregamos Lluvia al Excel también
            lluvias = Lluvia.query.filter_by(lote_id=lote.id).all()
            total_lluvia_historica = sum(l.milimetros for l in lluvias)
            data_agro.append({ "Lote": lote.nombre, "Hectáreas": lote.hectareas, "Propietario": c.propietario, "Total Cosechado (kg)": total_kilos, "Gastos Totales ($)": total_gastos, "Lluvia Historica (mm)": total_lluvia_historica })

        data_ganaderia = []
        animales = Animal.query.all()
        for a in animales:
            if Venta.query.filter_by(animal_id=a.id).first(): continue
            pesajes = Peso.query.filter_by(animal_id=a.id).order_by(Peso.fecha.desc()).all()
            peso_actual = pesajes[0].kilos if pesajes else 0
            gastos_animal = Gasto.query.filter_by(animal_id=a.id).all()
            total_gastos_animal = sum(g.monto for g in gastos_animal)
            ubic = "Corral"
            if a.lote_actual_id:
                l = Lote.query.get(a.lote_actual_id)
                if l: ubic = l.nombre
            data_ganaderia.append({ "Caravana": a.caravana, "Categoría": a.categoria, "Ubicación": ubic, "Peso Actual (kg)": peso_actual, "Costo Acumulado ($)": total_gastos_animal })

        data_ventas = []
        ventas = Venta.query.all()
        for v in ventas:
            a = Animal.query.get(v.animal_id)
            caravana = a.caravana if a else "Desconocido"
            margen = v.precio_total - v.costo_historico
            precio_promedio_kg = 0
            if v.kilos_venta and v.kilos_venta > 0: precio_promedio_kg = v.precio_total / v.kilos_venta
            data_ventas.append({ "Fecha Venta": v.fecha.strftime('%d/%m/%Y'), "Caravana": caravana, "Comprador": v.comprador, "Kg Venta": v.kilos_venta, "Precio Total ($)": v.precio_total, "Precio Promedio/Kg ($)": round(precio_promedio_kg, 2), "Costo Producción ($)": v.costo_historico, "MARGEN ($)": margen })

        data_gastos = []
        todos_gastos = Gasto.query.all()
        for g in todos_gastos:
            destino = "General"
            if g.lote_id: 
                l = Lote.query.get(g.lote_id)
                destino = f"Lote: {l.nombre}" if l else "Lote Eliminado"
            elif g.animal_id:
                a = Animal.query.get(g.animal_id)
                destino = f"Animal: {a.caravana}" if a else "Animal Eliminado"
            data_gastos.append({ "Fecha": g.fecha.strftime('%d/%m/%Y'), "Concepto": g.concepto, "Categoría": g.categoria, "Monto": g.monto, "Destino": destino })

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(data_agro).to_excel(writer, sheet_name='Agricultura', index=False)
            pd.DataFrame(data_ganaderia).to_excel(writer, sheet_name='Stock Activo', index=False)
            pd.DataFrame(data_ventas).to_excel(writer, sheet_name='Ventas y Margenes', index=False)
            pd.DataFrame(data_gastos).to_excel(writer, sheet_name='Detalle Gastos', index=False)
        output.seek(0)
        return send_file(output, download_name="Reporte_AgroNexo.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- CRUD BÁSICO ---
@app.route('/api/nuevo_contrato', methods=['POST'])
def crear_contrato():
    d = request.json
    try:
        has = float(d['hectareas']) if d['hectareas'] else 0.0
        porc = float(d['porcentaje']) if d['porcentaje'] else 0.0
        lat = float(d['lat']) if d.get('lat') else None
        lng = float(d['lng']) if d.get('lng') else None
        nl = Lote(nombre=d['nombreLote'], hectareas=has, latitud=lat, longitud=lng)
        db.session.add(nl); db.session.commit()
        nc = ContratoCampo(lote_id=nl.id, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=porc)
        db.session.add(nc); db.session.commit()
        return jsonify({"mensaje": "Guardado"}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/editar_lote/<int:lote_id>', methods=['PUT'])
def editar_lote(lote_id):
    d = request.json
    try:
        lote = Lote.query.get(lote_id)
        if not lote: return jsonify({"error": "No existe"}), 404
        lote.nombre = d['nombreLote']
        lote.hectareas = float(d['hectareas'])
        if d.get('lat'): lote.latitud = float(d['lat'])
        if d.get('lng'): lote.longitud = float(d['lng'])
        c = ContratoCampo.query.filter_by(lote_id=lote.id).first()
        if c:
            c.propietario = d['propietario']
            c.tipo = d['tipo']
            c.porcentaje_dueno = float(d['porcentaje'])
        db.session.commit()
        return jsonify({"mensaje": "Actualizado"})
    except: return jsonify({"error": "Error"}), 500

@app.route('/api/eliminar_lote/<int:lote_id>', methods=['DELETE'])
def eliminar_lote(lote_id):
    try:
        ContratoCampo.query.filter_by(lote_id=lote_id).delete()
        Gasto.query.filter_by(lote_id=lote_id).delete()
        Cosecha.query.filter_by(lote_id=lote_id).delete()
        animales = Animal.query.filter_by(lote_actual_id=lote_id).all()
        for a in animales: a.lote_actual_id = None
        Lote.query.filter_by(id=lote_id).delete()
        db.session.commit()
        return jsonify({"mensaje": "Eliminado"})
    except: return jsonify({"error": "Error"}), 500

@app.route('/api/nuevo_animal', methods=['POST'])
def nuevo_animal():
    d = request.json
    fi = datetime.utcnow()
    if 'fecha' in d and d['fecha']: 
        try: fi = datetime.strptime(d['fecha'], '%Y-%m-%d')
        except: pass
    animal = Animal(caravana=d['caravana'], raza=d['raza'], categoria=d['categoria'], fecha_ingreso=fi)
    db.session.add(animal); db.session.commit()
    if d['peso_inicial']:
        db.session.add(Peso(animal_id=animal.id, kilos=float(d['peso_inicial']), fecha=fi))
        db.session.commit()
    return jsonify({"mensaje": "Creado"}), 201
    
@app.route('/api/nuevo_pesaje', methods=['POST'])
def nuevo_pesaje():
    d = request.json
    fr = datetime.utcnow()
    if 'fecha' in d and d['fecha']:
        try: fr = datetime.strptime(d['fecha'], '%Y-%m-%d')
        except: pass
    db.session.add(Peso(animal_id=d['animal_id'], kilos=float(d['kilos']), fecha=fr)); db.session.commit()
    return jsonify({"mensaje": "Registrado"}), 201

@app.route('/api/nueva_cosecha', methods=['POST'])
def nueva_cosecha():
    d = request.json
    db.session.add(Cosecha(lote_id=d['lote_id'], kilos_totales=float(d['kilos']))); db.session.commit()
    return jsonify({"mensaje": "Carga Guardada"}), 201

@app.route('/api/nuevo_gasto', methods=['POST'])
def nuevo_gasto():
    d = request.json
    fr = datetime.utcnow()
    if 'fecha' in d and d['fecha']:
        try: fr = datetime.strptime(d['fecha'], '%Y-%m-%d')
        except: pass
    lid = d.get('lote_id')
    aid = d.get('animal_id')
    gasto = Gasto(fecha=fr, concepto=d['concepto'], monto=float(d['monto']), categoria=d['categoria'], lote_id=lid, animal_id=aid)
    db.session.add(gasto); db.session.commit()
    return jsonify({"mensaje": "Gasto Guardado"}), 201

with app.app_context(): db.create_all()
if __name__ == '__main__': app.run(debug=True, port=5000, host='0.0.0.0')