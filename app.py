import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_master_v3.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Consecutivo automático
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
    nro_parto = db.Column(db.Integer)
    nombre_cria = db.Column(db.String(100))
    sexo_cria = db.Column(db.String(10))
    peso_nacimiento = db.Column(db.Float)
    peso_madre = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=func.now())

class Produccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_nombre = db.Column(db.String(100), db.ForeignKey('animal.nombre'))
    litros = db.Column(db.Float)
    lactancia_nro = db.Column(db.Integer)
    fecha = db.Column(db.DateTime, default=func.now())

# --- LÓGICA DE NEGOCIO ---

@app.route('/api/ficha/<nombre>')
def ficha_animal(nombre):
    a = Animal.query.filter_by(nombre=nombre).first_or_404()
    partos = Parto.query.filter_by(madre_nombre=nombre).order_by(Parto.fecha).all()
    
    # Cálculos Automáticos
    iep = 0
    if len(partos) > 1:
        delta = partos[-1].fecha - partos[-2].fecha
        iep = delta.days

    return jsonify({
        "datos": {
            "raza": a.raza, "sexo": a.sexo, "edad": a.edad, "estado": a.estado,
            "madre": a.madre, "padre": a.padre, "codigo": a.codigo, "obs": a.observaciones,
            "foto": f"{a.nombre}.jpg" # Gestión automática de imágenes
        },
        "reproduccion": {
            "cantidad_crias": len(partos),
            "iep_dias": iep,
            "primer_parto": partos[0].fecha.strftime('%Y-%m-%d') if partos else "N/A",
            "ultimo_parto": partos[-1].fecha.strftime('%Y-%m-%d') if partos else "N/A"
        }
    })

@app.route('/api/produccion/proyeccion/<nombre>/<int:lactancia>')
def proyectar_lactancia(nombre, lactancia):
    registros = Produccion.query.filter_by(animal_nombre=nombre, lactancia_nro=lactancia).all()
    if len(registros) < 1: return jsonify({"error": "Datos insuficientes"})
    
    promedio_diario = sum([r.litros for r in registros]) / len(registros)
    proyeccion_305 = promedio_diario * 305 # Algoritmo de proyección simple
    
    return jsonify({
        "historico": [{"fecha": r.fecha.strftime('%Y-%m-%d'), "litros": r.litros} for r in registros],
        "proyeccion_total": round(proyeccion_305, 2)
    })

# CRUD y Guardado
@app.route('/api/animales', methods=['POST'])
def save_animal():
    d = request.json
    nuevo = Animal(nombre=d['nombre'], raza=d['raza'], sexo=d['sexo'], edad=d['edad'], 
                   estado=d['estado'], madre=d['madre'], padre=d['padre'], 
                   codigo=d['codigo'], observaciones=d['obs'])
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"status": "ok", "id": nuevo.id})

@app.route('/reset')
def reset():
    db.drop_all(); db.create_all()
    return "SISTEMA INICIALIZADO"

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=10000)