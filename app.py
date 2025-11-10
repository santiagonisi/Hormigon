from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy import event
import sqlite3
from sqlalchemy.engine import Engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Obra(db.Model):
    __tablename__ = 'obras'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=True)
    clases = db.relationship('Clase', secondary='obra_clase', back_populates='obras')
    formulas = db.relationship('Formula', secondary='obra_formula', back_populates='obras')


class Clase(db.Model):
    __tablename__ = 'clases'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(250))
    obras = db.relationship('Obra', secondary='obra_clase', back_populates='clases')
    formulas = db.relationship('Formula', back_populates='clase', cascade='all, delete-orphan')


class ObraClase(db.Model):
    __tablename__ = 'obra_clase'
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)


class ObraFormula(db.Model):
    __tablename__ = 'obra_formula'
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'), nullable=False)


class Formula(db.Model):
    __tablename__ = 'formulas'
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    clase = db.relationship('Clase', back_populates='formulas')
    items = db.relationship('FormulaItem', cascade='all, delete-orphan')
    obras = db.relationship('Obra', secondary='obra_formula', back_populates='formulas')


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
    db.create_all()

    if Clase.query.count() == 0:
        clases = [
            Clase(nombre='H8', descripcion='Hormigón H8'),
            Clase(nombre='H13', descripcion='Hormigón H13'),
            Clase(nombre='H15', descripcion='Hormigón H15'),
            Clase(nombre='H17', descripcion='Hormigón H17'),
            Clase(nombre='H20', descripcion='Hormigón H20'),
            Clase(nombre='H21', descripcion='Hormigón H21'),
            Clase(nombre='H25', descripcion='Hormigón H25'),
            Clase(nombre='H30', descripcion='Hormigón H30')
        ]
        db.session.add_all(clases)
        db.session.commit()


@app.route('/')
def index():
    return redirect(url_for('parte_diario'))


@app.route('/parte_diario')
def parte_diario():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    obras = Obra.query.order_by(Obra.nombre).all()
    partes = ParteDiario.query.order_by(ParteDiario.fecha.desc(), ParteDiario.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    total_pages = partes.pages if partes.pages >= 1 else 1
    return render_template('parte_diario.html', obras=obras, partes=partes, page=page, total_pages=total_pages)


@app.route('/obras')
def obras():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    obras_paginate = Obra.query.order_by(Obra.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    total_pages = obras_paginate.pages or 1
    formulas = Formula.query.outerjoin(Clase).order_by(Clase.nombre, Formula.nombre).all()
    return render_template('obras.html', obras=obras_paginate.items, formulas=formulas,
                           page=page, total_pages=total_pages, obras_paginate=obras_paginate)


@app.route('/formulas')
def formulas():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    formulas_paginate = Formula.query.order_by(Formula.id.desc()).paginate(page=page, per_page=per_page,
                                                                           error_out=False)
    total_pages = formulas_paginate.pages or 1
    clases = Clase.query.order_by(Clase.nombre).all()
    return render_template('formulas.html', clases=clases, formulas=formulas_paginate.items,
                           page=page, total_pages=total_pages, formulas_paginate=formulas_paginate)



@app.route('/api/get_clases/<int:obra_id>')
def api_get_clases(obra_id):
    clases = (db.session.query(Clase.id, Clase.nombre)
              .join(Formula, Clase.id == Formula.clase_id)
              .join(ObraFormula, Formula.id == ObraFormula.formula_id)
              .filter(ObraFormula.obra_id == obra_id)
              .distinct()
              .order_by(Clase.nombre).all())
    result = [{'id': c.id, 'nombre': c.nombre} for c in clases]
    return jsonify(result)


@app.route('/api/guardar_parte', methods=['POST'])
def api_guardar_parte():
    data = request.json
    try:
        parte_id = data.get('id')
        fecha = datetime.strptime(data.get('fecha'), '%Y-%m-%d').date()
        obra_id = int(data.get('obra_id'))
        clase_id = int(data.get('clase_id'))
        hora = data.get('hora_despacho')
        hora_val = datetime.strptime(hora, '%H:%M').time() if hora else None
        cantidad = float(data.get('cantidad_m3')) if data.get('cantidad_m3') else None
        asentamiento = float(data.get('asentamiento_cm')) if data.get('asentamiento_cm') else None
        usa_probetas = bool(data.get('usa_probetas'))

        if parte_id:
            parte = ParteDiario.query.get_or_404(parte_id)
            parte.fecha = fecha
            parte.obra_id = obra_id
            parte.clase_id = clase_id
            parte.hora_despacho = hora_val
            parte.cantidad_m3 = cantidad
            parte.asentamiento_cm = asentamiento
            parte.usa_probetas = usa_probetas
            Probeta.query.filter_by(parte_id=parte.id).delete()
        else:
            parte = ParteDiario(
                fecha=fecha, obra_id=obra_id, clase_id=clase_id,
                hora_despacho=hora_val, cantidad_m3=cantidad,
                asentamiento_cm=asentamiento, usa_probetas=usa_probetas
            )
            db.session.add(parte)
            db.session.flush()

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


@app.route('/api/parte_diario/<int:parte_id>')
def api_get_parte(parte_id):
    parte = ParteDiario.query.get_or_404(parte_id)
    return jsonify({
        'id': parte.id,
        'fecha': parte.fecha.strftime('%Y-%m-%d'),
        'obra_id': parte.obra_id,
        'clase_id': parte.clase_id,
        'hora_despacho': parte.hora_despacho.strftime('%H:%M') if parte.hora_despacho else None,
        'cantidad_m3': parte.cantidad_m3,
        'asentamiento_cm': parte.asentamiento_cm,
        'usa_probetas': parte.usa_probetas,
        'probetas': [{
            'fecha_ensayo': p.fecha_ensayo.strftime('%Y-%m-%d') if p.fecha_ensayo else None,
            'edad_dias': p.edad_dias,
            'lectura_prensa_kn': p.lectura_prensa_kn,
            'resistencia_mpa': p.resistencia_mpa
        } for p in parte.probetas]
    })


@app.route('/api/eliminar_parte/<int:parte_id>', methods=['DELETE'])
def api_eliminar_parte(parte_id):
    parte = ParteDiario.query.get(parte_id)
    if not parte:
        return jsonify({'ok': False, 'error': 'No encontrado'}), 404
    db.session.delete(parte)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/formulas')
def api_formulas():
    formulas = Formula.query.join(Clase).all()
    result = []
    for f in formulas:
        result.append({
            'id': f.id,
            'clase_id': f.clase_id,
            'clase_nombre': f.clase.nombre,
            'nombre': f.nombre,
            'items': [{'material': i.material, 'cantidad': i.cantidad, 'unidad': i.unidad}
                      for i in f.items]
        })
    return jsonify(result)


@app.route('/api/guardar_formula', methods=['POST'])
def api_guardar_formula():
    try:
        data = request.json
        formula = Formula(
            clase_id=data['clase_id'],
            nombre=data['nombre']
        )
        db.session.add(formula)
        db.session.commit()

        for item in data['items']:
            formula_item = FormulaItem(
                formula_id=formula.id,
                material=item['material'],
                cantidad=item['cantidad'],
                unidad=item['unidad']
            )
            db.session.add(formula_item)

        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/obras/<int:obra_id>')
def api_get_obra(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    return jsonify({
        'id': obra.id,
        'nombre': obra.nombre,
        'fecha': obra.fecha.isoformat() if obra.fecha else None,
        'formulas': [f.id for f in obra.formulas]
    })


@app.route('/api/obras', methods=['POST'])
def api_guardar_obra():
    try:
        data = request.json
        if data.get('id'):
            obra = Obra.query.get_or_404(data['id'])
            obra.nombre = data['nombre']
            obra.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date() if data['fecha'] else None
        else:
            obra = Obra(
                nombre=data['nombre'],
                fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date() if data['fecha'] else None
            )
            db.session.add(obra)

        formula_ids = data.get('formulas') or []
        formulas = Formula.query.filter(Formula.id.in_(formula_ids)).all() if formula_ids else []
        obra.formulas = formulas

        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/obras/<int:obra_id>', methods=['DELETE'])
def api_eliminar_obra(obra_id):
    try:
        obra = Obra.query.get_or_404(obra_id)
        ParteDiario.query.filter_by(obra_id=obra_id).delete()
        ObraFormula.query.filter_by(obra_id=obra_id).delete()
        db.session.delete(obra)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/formulas/<int:formula_id>', methods=['DELETE'])
def api_eliminar_formula(formula_id):
    try:
        formula = Formula.query.get_or_404(formula_id)
        FormulaItem.query.filter_by(formula_id=formula_id).delete()
        ObraFormula.query.filter_by(formula_id=formula_id).delete()
        db.session.delete(formula)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/informes', endpoint='informes')
def informes_page():

    clases_db = Clase.query.all()
    clases = sorted(clases_db, key=lambda c: int(''.join(filter(str.isdigit, c.nombre))))

    asentamientos_reales = []
    for clase in clases:
        partes = (
            ParteDiario.query
            .filter(ParteDiario.clase_id == clase.id, ParteDiario.asentamiento_cm.isnot(None))
            .all()
        )
        if partes:
            promedio = sum(p.asentamiento_cm for p in partes) / len(partes)
        else:
            promedio = 0
        asentamientos_reales.append(promedio)

    asentamientos_ref = [5 for _ in clases]

    return render_template(
        'informes.html',
        clases=[c.nombre for c in clases],
        asentamientos_reales=asentamientos_reales,
        asentamientos_ref=asentamientos_ref
    )


if __name__ == '__main__':
    with app.app_context():
        create_and_seed_db()
    app.run(debug=True)
