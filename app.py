import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_elite_v3.db')
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
    activo = db.Column(db.Boolean, default=True)

class Parto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    madre_nombre = db.Column(db.String(100))
    fecha = db.Column(db.String(20))
    nombre_cria = db.Column(db.String(100))
    sexo_cria = db.Column(db.String(10))
    peso_nacimiento = db.Column(db.Float)

class Produccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_nombre = db.Column(db.String(100))
    litros = db.Column(db.Float)
    lactancia_nro = db.Column(db.Integer)
    fecha = db.Column(db.String(20))

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    has = db.Column(db.Float)
    tenencia = db.Column(db.String(20))
    geometria = db.Column(db.Text, nullable=True)

class Finanzas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20)) # INGRESO / GASTO
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    fecha = db.Column(db.String(20))

# --- ENDPOINTS ---

@app.route('/api/resumen')
def resumen():
    return jsonify({
        "hacienda": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.count(),
        "lluvias": 0, # Placeholder para API clima
        "gastos": db.session.query(func.sum(Finanzas.monto)).filter(Finanzas.tipo == 'GASTO').scalar() or 0
    })

@app.route('/api/<string:modulo>', methods=['GET', 'POST'])
def gestion(modulo):
    modelos = {'ganaderia': Animal, 'lotes': Lote, 'finanzas': Finanzas, 'partos': Parto, 'produccion': Produccion}
    model = modelos.get(modulo)
    if request.method == 'POST':
        d = request.json
        obj = model(**d)
        db.session.add(obj)
        db.session.commit()
        return jsonify({"status": "ok"})
    
    items = model.query.all()
    return jsonify([dict((c.name, getattr(x, c.name)) for c in x.__table__.columns) for x in items])

@app.route('/api/proyeccion/<nombre>/<int:lactancia>')
def proyeccion_305(nombre, lactancia):
    registros = Produccion.query.filter_by(animal_nombre=nombre, lactancia_nro=lactancia).all()
    if len(registros) < 1: return jsonify({"proyeccion": 0})
    # Algoritmo de Wood simplificado: Promedio diario x 305 días
    promedio = sum([r.litros for r in registros]) / len(registros)
    return jsonify({"proyeccion": round(promedio * 305, 2)})

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA ELITE V3 INICIALIZADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)