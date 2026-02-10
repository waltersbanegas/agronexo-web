import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Base de datos relacional robusta
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_pro_v4.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    raza = db.Column(db.String(50))
    sexo = db.Column(db.String(10))
    edad = db.Column(db.Integer)
    estado = db.Column(db.String(50))
    madre = db.Column(db.String(100))
    padre = db.Column(db.String(100))
    codigo = db.Column(db.String(50))
    observaciones = db.Column(db.Text)

class Parto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    madre_nombre = db.Column(db.String(100), db.ForeignKey('animal.nombre'))
    fecha = db.Column(db.DateTime, default=func.now())
    nombre_cria = db.Column(db.String(100))
    peso_nacimiento = db.Column(db.Float)

class Produccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_nombre = db.Column(db.String(100), db.ForeignKey('animal.nombre'))
    litros = db.Column(db.Float)
    lactancia_nro = db.Column(db.Integer)
    fecha = db.Column(db.DateTime, default=func.now())

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50)) # Soja, Girasol, Maíz, etc
    has = db.Column(db.Float)
    tenencia = db.Column(db.String(20)) # Propio / Alquilado
    geometria = db.Column(db.Text) # Polígono del mapa

class Finanzas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10)) # INGRESO / GASTO
    unidad = db.Column(db.String(20)) # Ganaderia / Agricultura
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=func.now())

# --- LÓGICA DE NEGOCIO Y CÁLCULOS ---

@app.route('/api/ficha/<nombre>')
def get_ficha(nombre):
    a = Animal.query.filter_by(nombre=nombre).first_or_404()
    partos = Parto.query.filter_by(madre_nombre=nombre).order_by(Parto.fecha).all()
    
    # IEP: Días entre el último y penúltimo parto
    iep = (partos[-1].fecha - partos[-2].fecha).days if len(partos) > 1 else 0
    
    return jsonify({
        "info": {"raza": a.raza, "sexo": a.sexo, "estado": a.estado, "madre": a.madre, "padre": a.padre, "foto": f"{a.nombre}.jpg"},
        "reproduccion": {"crias": len(partos), "iep": iep, "ultimo": partos[-1].fecha if partos else "N/A"}
    })

@app.route('/api/produccion/proyeccion/<nombre>/<int:lactancia>')
def get_proyeccion(nombre, lactancia):
    datos = Produccion.query.filter_by(animal_nombre=nombre, lactancia_nro=lactancia).all()
    if not datos: return jsonify({"error": "No hay datos"})
    
    # Algoritmo de proyección: Promedio ajustado a 305 días
    promedio = sum([d.litros for d in datos]) / len(datos)
    proyeccion = round(promedio * 305, 2)
    
    return jsonify({
        "historico": [{"fecha": d.fecha, "litros": d.litros} for d in datos],
        "proyeccion_305": proyeccion
    })

@app.route('/api/<string:modulo>', methods=['GET', 'POST'])
def crud(modulo):
    modelos = {'animales': Animal, 'lotes': Lote, 'partos': Parto, 'produccion': Produccion, 'finanzas': Finanzas}
    model = modelos.get(modulo)
    if request.method == 'POST':
        obj = model(**request.json)
        db.session.add(obj); db.session.commit()
        return jsonify({"status": "ok", "id": obj.id})
    return jsonify([dict((c.name, getattr(x, c.name)) for c in x.__table__.columns) for x in model.query.all()])

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA INTEGRAL REESTABLECIDO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)