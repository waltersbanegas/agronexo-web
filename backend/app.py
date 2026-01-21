from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agronexo.db'
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

# --- RUTAS ---

@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    try:
        resultados = []
        contratos = ContratoCampo.query.all()
        for contrato in contratos:
            cosechas = Cosecha.query.filter_by(lote_id=contrato.lote_id).all()
            total_kilos = sum(c.kilos_totales for c in cosechas)
            
            if contrato.tipo == 'APARCERIA':
                kilos_dueno = total_kilos * (contrato.porcentaje_dueno / 100)
            else:
                kilos_dueno = 0 
            kilos_propios = total_kilos - kilos_dueno
            
            gastos = Gasto.query.filter_by(lote_id=contrato.lote_id).all()
            total_gastos = sum(g.monto for g in gastos)

            lote = Lote.query.get(contrato.lote_id)
            if not lote: continue # Seguridad por si el lote se borró mal

            cant_animales = Animal.query.filter_by(lote_actual_id=lote.id).count()
            
            resultados.append({
                "id": contrato.id, "lote_id": lote.id, "lote": lote.nombre,
                "hectareas": lote.hectareas, "propietario": contrato.propietario,
                "tipo": contrato.tipo, "porcentaje": contrato.porcentaje_dueno,
                "total_cosechado": total_kilos, "kilos_propios": kilos_propios, 
                "kilos_dueno": kilos_dueno, "total_gastos": total_gastos,
                "lat": lote.latitud, "lng": lote.longitud, "animales_count": cant_animales
            })
        return jsonify(resultados)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_contrato', methods=['POST'])
def crear_contrato():
    try:
        d = request.json
        has = float(d['hectareas']) if d['hectareas'] else 0.0
        porc = float(d['porcentaje']) if d['porcentaje'] else 0.0
        lat = float(d['lat']) if d.get('lat') else None
        lng = float(d['lng']) if d.get('lng') else None

        nl = Lote(nombre=d['nombreLote'], hectareas=has, latitud=lat, longitud=lng)
        db.session.add(nl)
        db.session.commit()
        
        nc = ContratoCampo(lote_id=nl.id, propietario=d['propietario'], tipo=d['tipo'], porcentaje_dueno=porc)
        db.session.add(nc)
        db.session.commit()
        return jsonify({"mensaje": "Guardado"}), 201
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

# --- NUEVAS RUTAS PARA EDITAR Y BORRAR ---

@app.route('/api/editar_lote/<int:lote_id>', methods=['PUT'])
def editar_lote(lote_id):
    try:
        d = request.json
        lote = Lote.query.get(lote_id)
        if not lote: return jsonify({"error": "No existe"}), 404

        # Actualizar Lote
        lote.nombre = d['nombreLote']
        lote.hectareas = float(d['hectareas'])
        if d.get('lat'): lote.latitud = float(d['lat'])
        if d.get('lng'): lote.longitud = float(d['lng'])
        
        # Actualizar Contrato (buscamos el asociado al lote)
        contrato = ContratoCampo.query.filter_by(lote_id=lote.id).first()
        if contrato:
            contrato.propietario = d['propietario']
            contrato.tipo = d['tipo']
            contrato.porcentaje_dueno = float(d['porcentaje'])

        db.session.commit()
        return jsonify({"mensaje": "Actualizado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/eliminar_lote/<int:lote_id>', methods=['DELETE'])
def eliminar_lote(lote_id):
    try:
        # 1. Borrar Contrato asociado
        ContratoCampo.query.filter_by(lote_id=lote_id).delete()
        # 2. Borrar Gastos asociados al lote
        Gasto.query.filter_by(lote_id=lote_id).delete()
        # 3. Borrar Cosechas asociadas
        Cosecha.query.filter_by(lote_id=lote_id).delete()
        # 4. Finalmente borrar el lote
        Lote.query.filter_by(id=lote_id).delete()
        
        db.session.commit()
        return jsonify({"mensaje": "Eliminado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ... (Rutas de Animales, Pesaje, Cosecha, Gasto se mantienen igual) ...
@app.route('/api/animales', methods=['GET'])
def obtener_animales():
    try:
        lista = []
        todos = Animal.query.all()
        for vaca in todos:
            pesajes = Peso.query.filter_by(animal_id=vaca.id).order_by(Peso.fecha.desc()).all()
            gastos = Gasto.query.filter_by(animal_id=vaca.id).all()
            total_gastos = sum(g.monto for g in gastos)
            peso_act = 0; gdp = 0; ult = "Sin datos"
            if pesajes:
                peso_act = pesajes[0].kilos
                ult = pesajes[0].fecha.strftime("%d/%m/%Y")
                if len(pesajes) > 1:
                    dif_k = peso_act - pesajes[1].kilos
                    dif_d = (pesajes[0].fecha - pesajes[1].fecha).days
                    if dif_d > 0: gdp = dif_k / dif_d
            lista.append({"id": vaca.id, "caravana": vaca.caravana, "raza": vaca.raza, "categoria": vaca.categoria, "peso_actual": peso_act, "gdp": round(gdp, 3), "ultimo_pesaje": ult, "costo_acumulado": total_gastos})
        return jsonify(lista)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/nuevo_animal', methods=['POST'])
def nuevo_animal():
    d = request.json
    fi = datetime.utcnow()
    if 'fecha' in d and d['fecha']: 
        try: fi = datetime.strptime(d['fecha'], '%Y-%m-%d')
        except: pass
    animal = Animal(caravana=d['caravana'], raza=d['raza'], categoria=d['categoria'], fecha_ingreso=fi)
    db.session.add(animal)
    db.session.commit()
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
    db.session.add(Peso(animal_id=d['animal_id'], kilos=float(d['kilos']), fecha=fr))
    db.session.commit()
    return jsonify({"mensaje": "Registrado"}), 201

@app.route('/api/nueva_cosecha', methods=['POST'])
def nueva_cosecha():
    d = request.json
    db.session.add(Cosecha(lote_id=d['lote_id'], kilos_totales=float(d['kilos'])))
    db.session.commit()
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
    db.session.add(gasto)
    db.session.commit()
    return jsonify({"mensaje": "Gasto Guardado"}), 201

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')