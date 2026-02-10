import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_pro_final.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS INTEGRADOS ---

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
    nro_parto = db.Column(db.Integer)
    nombre_cria = db.Column(db.String(100))
    sexo_cria = db.Column(db.String(10))
    peso_nacimiento = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=func.now())

class Produccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_nombre = db.Column(db.String(100))
    litros = db.Column(db.Float)
    lactancia_nro = db.Column(db.Integer)
    fecha = db.Column(db.DateTime, default=func.now())

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cultivo = db.Column(db.String(50))
    has = db.Column(db.Float)
    geometria = db.Column(db.Text) #

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mm = db.Column(db.Float)
    lote_id = db.Column(db.Integer)
    fecha = db.Column(db.String(20))

class Finanzas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20)) # INGRESO / GASTO
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    fecha = db.Column(db.String(20))

# --- LÓGICA DE NEGOCIO ---

@app.route('/api/resumen')
def resumen():
    return jsonify({
        "animales": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.count(),
        "lluvias": db.session.query(func.sum(Lluvia.mm)).scalar() or 0,
        "gastos": db.session.query(func.sum(Finanzas.monto)).filter(Finanzas.tipo == 'GASTO').scalar() or 0
    })

@app.route('/api/ficha/<nombre>')
def ficha(nombre):
    a = Animal.query.filter_by(nombre=nombre).first_or_404()
    partos = Parto.query.filter_by(madre_nombre=nombre).order_by(Parto.fecha).all()
    iep = (partos[-1].fecha - partos[-2].fecha).days if len(partos) > 1 else 0
    return jsonify({
        "datos": {"raza":a.raza,"sexo":a.sexo,"edad":a.edad,"estado":a.estado,"madre":a.madre,"padre":a.padre,"codigo":a.codigo,"obs":a.observaciones},
        "repro": {"crias":len(partos), "iep":iep, "primero":partos[0].fecha if partos else "--", "ultimo":partos[-1].fecha if partos else "--"}
    })

@app.route('/api/produccion/proyeccion/<nombre>/<int:lactancia>')
def proyeccion(nombre, lactancia):
    registros = Produccion.query.filter_by(animal_nombre=nombre, lactancia_nro=lactancia).all()
    total_litros = sum([r.litros for r in registros])
    proy_305 = (total_litros / len(registros) * 305) if len(registros) > 0 else 0
    return jsonify({"historico": [{"fecha":r.fecha,"litros":r.litros} for r in registros], "proyeccion": round(proy_305, 2)})

@app.route('/api/<string:modulo>', methods=['GET', 'POST'])
def crud_general(modulo):
    modelos = {'animales': Animal, 'lotes': Lote, 'lluvias': Lluvia, 'finanzas': Finanzas, 'partos': Parto, 'produccion': Produccion}
    model = modelos.get(modulo)
    if request.method == 'POST':
        d = request.json
        # Lógica de inserción dinámica
        obj = model(**d)
        db.session.add(obj); db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify([dict((c.name, getattr(x, c.name)) for c in x.__table__.columns) for x in model.query.all()])

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA INTEGRAL REESTABLECIDO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)