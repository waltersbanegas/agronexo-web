import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agronexo_restored.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelos Originales Recuperados ---
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caravana = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    peso = db.Column(db.Float, default=0.0)
    estado_reproductivo = db.Column(db.String(50), default='VACIA')
    lat = db.Column(db.Float, default=-26.7)
    lng = db.Column(db.Float, default=-60.8)
    activo = db.Column(db.Boolean, default=True)

class Lote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cultivo = db.Column(db.String(50), default='Sin Sembrar')
    hectareas = db.Column(db.Float, default=0.0)
    lat = db.Column(db.Float, default=-26.7)
    lng = db.Column(db.Float, default=-60.8)
    activo = db.Column(db.Boolean, default=True)

class Lluvia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), server_default=func.now())
    milimetros = db.Column(db.Float, nullable=False)
    notas = db.Column(db.String(200))

# --- Endpoints Restaurados ---

@app.route('/api/resumen')
def get_resumen():
    return jsonify({
        "animales": Animal.query.filter_by(activo=True).count(),
        "lotes": Lote.query.filter_by(activo=True).count(),
        "total_lluvia": db.session.query(func.sum(Lluvia.milimetros)).scalar() or 0
    })

@app.route('/api/ganaderia', methods=['GET', 'POST'])
def gestion_ganaderia():
    if request.method == 'POST':
        data = request.json
        nuevo = Animal(
            caravana=data.get('caravana'),
            categoria=data.get('categoria'),
            estado_reproductivo=data.get('estado', 'VACIA'),
            peso=float(data.get('peso', 0)),
            lat=data.get('lat', -26.7),
            lng=data.get('lng', -60.8)
        )
        db.session.add(nuevo); db.session.commit()
        return jsonify({"msg": "Registrado"})
    
    animales = Animal.query.filter_by(activo=True).all()
    return jsonify([{"id":a.id,"caravana":a.caravana,"categoria":a.categoria,"peso":a.peso,"estado":a.estado_reproductivo} for a in animales])

@app.route('/api/agricultura', methods=['GET', 'POST'])
def gestion_agricultura():
    if request.method == 'POST':
        data = request.json
        nuevo = Lote(
            nombre=data.get('nombre'),
            cultivo=data.get('cultivo', 'Barbecho'),
            hectareas=float(data.get('hectareas', 0)),
            lat=data.get('lat', -26.7),
            lng=data.get('lng', -60.8)
        )
        db.session.add(nuevo); db.session.commit()
        return jsonify({"msg": "Lote creado"})
    
    lotes = Lote.query.filter_by(activo=True).all()
    return jsonify([{"id":l.id,"nombre":l.nombre,"cultivo":l.cultivo,"hectareas":l.hectareas} for l in lotes])

@app.route('/api/lluvia', methods=['GET', 'POST'])
def gestion_lluvia():
    if request.method == 'POST':
        data = request.json
        nueva = Lluvia(milimetros=float(data.get('mm', 0)), notas=data.get('notas', ''))
        db.session.add(nueva); db.session.commit()
        return jsonify({"msg": "Lluvia registrada"})
    lluvias = Lluvia.query.order_by(Lluvia.fecha.desc()).limit(10).all()
    return jsonify([{"id":l.id,"mm":l.milimetros,"fecha":str(l.fecha)} for l in lluvias])

@app.route('/api/ganaderia/<int:id>', methods=['DELETE'])
def delete_animal(id):
    a = Animal.query.get(id)
    if a: a.activo = False; db.session.commit()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)