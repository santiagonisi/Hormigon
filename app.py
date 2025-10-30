from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Obra(db.Model):
    __tablename__ = 'obras'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=True)
    clases = db.relationship('Clase', secondary='obra_clase', back_populates='obras')

class Clase(db.Model):
    __tablename__ = 'clases'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) 
    descripcion = db.Column(db.String(250))
    obras = db.relationship('Obra', secondary='obra_clase', back_populates='clases')
    formula = db.relationship('Formula', uselist=False, back_populates='clase')

class ObraClase(db.Model):
    __tablename__ = 'obra_clase'
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)

class Formula(db.Model):
    __tablename__ = 'formulas'
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    clase = db.relationship('Clase', back_populates='formula')
    items = db.relationship('FormulaItem', cascade='all, delete-orphan')

class FormulaItem(db.Model):
    __tablename__ = 'formula_items'
    id = db.Column(db.Integer, primary_key=True)
    formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'), nullable=False)
    material = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(50), nullable=False)

class ParteDiario(db.Model):
    __tablename__ = 'parte_diario'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    hora_despacho = db.Column(db.Time, nullable=True)
    cantidad_m3 = db.Column(db.Float, nullable=True)
    asentamiento_cm = db.Column(db.Float, nullable=True)
    usa_probetas = db.Column(db.Boolean, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    obra = db.relationship('Obra', backref='partes')
    clase = db.relationship('Clase')
    probetas = db.relationship('Probeta', cascade='all, delete-orphan')

class Probeta(db.Model):
    __tablename__ = 'probetas'
    id = db.Column(db.Integer, primary_key=True)
    parte_id = db.Column(db.Integer, db.ForeignKey('parte_diario.id'), nullable=False)
    fecha_ensayo = db.Column(db.Date, nullable=True)
    edad_dias = db.Column(db.Integer, nullable=True)
    lectura_prensa_kn = db.Column(db.Float, nullable=True)
    resistencia_mpa = db.Column(db.Float, nullable=True)


def create_and_seed_db():
    if not os.path.exists(DB_PATH):
        db.create_all()

        o1 = Obra(nombre='Obra Central', fecha=datetime.strptime('2025-08-01', '%Y-%m-%d').date())
        o2 = Obra(nombre='Obra Norte', fecha=datetime.strptime('2025-09-12', '%Y-%m-%d').date())
        c1 = Clase(nombre='H21', descripcion='Hormigón H21')
        c2 = Clase(nombre='H25', descripcion='Hormigón H25')
        c3 = Clase(nombre='H30', descripcion='Hormigón H30')
        db.session.add_all([o1, o2, c1, c2, c3])
        db.session.commit()
        db.session.add_all([
            ObraClase(obra_id=o1.id, clase_id=c1.id),
            ObraClase(obra_id=o1.id, clase_id=c2.id),
            ObraClase(obra_id=o2.id, clase_id=c2.id),
            ObraClase(obra_id=o2.id, clase_id=c3.id),
        ])

        f = Formula(clase_id=c2.id, nombre='Dosificación H25 - Ejemplo')
        db.session.add(f); db.session.commit()
        fi1 = FormulaItem(formula_id=f.id, material='Cemento', cantidad=350, unidad='kg')
        fi2 = FormulaItem(formula_id=f.id, material='Agua', cantidad=170, unidad='lts')
        fi3 = FormulaItem(formula_id=f.id, material='Arena', cantidad=800, unidad='kg')
        db.session.add_all([fi1, fi2, fi3])
        db.session.commit()
        print('DB creada y seed aplicada.')

@app.route('/')
def index():
    return redirect(url_for('parte_diario'))

@app.route('/parte_diario')
def parte_diario():

    page = request.args.get('page', 1, type=int)
    per_page = 10

    obras = Obra.query.order_by(Obra.nombre).all()
    partes = ParteDiario.query.order_by(ParteDiario.fecha.desc(), ParteDiario.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    total_pages = partes.pages if partes.pages >= 1 else 1
    return render_template('parte_diario.html', obras=obras, partes=partes, page=page, total_pages=total_pages)

@app.route('/obras')
def obras_page():
    obras = Obra.query.order_by(Obra.id.desc()).all()
    return render_template('obras.html', obras=obras)

@app.route('/formulas')
def formulas_page():
    clases = Clase.query.order_by(Clase.nombre).all()
    return render_template('formulas.html', clases=clases)

@app.route('/informes')
def informes_page():
    return render_template('informes.html')

@app.route('/api/get_clases/<int:obra_id>')
def api_get_clases(obra_id):
    clases = (db.session.query(Clase.id, Clase.nombre)
              .join(ObraClase, Clase.id == ObraClase.clase_id)
              .filter(ObraClase.obra_id == obra_id)
              .order_by(Clase.nombre).all())
    result = [{'id': c.id, 'nombre': c.nombre} for c in clases]
    return jsonify(result)

@app.route('/api/guardar_parte', methods=['POST'])
def api_guardar_parte():
    data = request.json
    try:
        fecha = datetime.strptime(data.get('fecha'), '%Y-%m-%d').date()
        obra_id = int(data.get('obra_id'))
        clase_id = int(data.get('clase_id'))
        hora = data.get('hora_despacho')
        hora_val = datetime.strptime(hora, '%H:%M').time() if hora else None
        cantidad = float(data.get('cantidad_m3')) if data.get('cantidad_m3') else None
        asentamiento = float(data.get('asentamiento_cm')) if data.get('asentamiento_cm') else None
        usa_probetas = bool(data.get('usa_probetas'))
        parte = ParteDiario(
            fecha=fecha, obra_id=obra_id, clase_id=clase_id,
            hora_despacho=hora_val, cantidad_m3=cantidad,
            asentamiento_cm=asentamiento, usa_probetas=usa_probetas
        )
        db.session.add(parte)
        db.session.commit()

        probetas = data.get('probetas') or []
        for p in probetas:
            fecha_ens = datetime.strptime(p.get('fecha_ensayo'), '%Y-%m-%d').date() if p.get('fecha_ensayo') else None
            edad = int(p.get('edad')) if p.get('edad') else None
            lectura = float(p.get('lectura')) if p.get('lectura') else None
            resistencia = float(p.get('resistencia')) if p.get('resistencia') else None
            pb = Probeta(parte_id=parte.id, fecha_ensayo=fecha_ens, edad_dias=edad,
                        lectura_prensa_kn=lectura, resistencia_mpa=resistencia)
            db.session.add(pb)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Parte guardado', 'parte_id': parte.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/eliminar_parte/<int:parte_id>', methods=['DELETE'])
def api_eliminar_parte(parte_id):
    parte = ParteDiario.query.get(parte_id)
    if not parte:
        return jsonify({'ok': False, 'error': 'No encontrado'}), 404
    db.session.delete(parte)
    db.session.commit()
    return jsonify({'ok': True})

if __name__ == '__main__':

    with app.app_context():
        create_and_seed_db()
    app.run(debug=True)
