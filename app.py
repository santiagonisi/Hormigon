from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from sqlalchemy import event
import sqlite3
from sqlalchemy.engine import Engine
from statistics import mean

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
    probetas = db.relationship('Probeta', back_populates='parte', cascade='all, delete-orphan')

class Probeta(db.Model):
    __tablename__ = 'probetas'
    id = db.Column(db.Integer, primary_key=True)
    parte_id = db.Column(db.Integer, db.ForeignKey('parte_diario.id'), nullable=False)
    fecha_ensayo = db.Column(db.Date, nullable=True)
    edad_dias = db.Column(db.Integer, nullable=True)
    lectura_prensa_kn = db.Column(db.Float, nullable=True)
    resistencia_mpa = db.Column(db.Float, nullable=True)

    parte = db.relationship('ParteDiario', back_populates='probetas')


def create_and_seed_db():
    db.create_all()
    clases_seed = [
        ('H8', 'Hormigón H8'),
        ('H13', 'Hormigón H13'),
        ('H15', 'Hormigón H15'),
        ('H17', 'Hormigón H17'),
        ('H20', 'Hormigón H20'),
        ('H21', 'Hormigón H21'),
        ('H25', 'Hormigón H25'),
        ('H30', 'Hormigón H30'),
        ('H35', 'Hormigón H35'),
        ('H40', 'Hormigón H40'),
        ('RDC', 'RDC')
    ]

    existentes = {c.nombre for c in Clase.query.with_entities(Clase.nombre).all()}
    nuevas = [Clase(nombre=nombre, descripcion=descripcion)
              for nombre, descripcion in clases_seed
              if nombre not in existentes]

    if nuevas:
        db.session.add_all(nuevas)
        db.session.commit()


with app.app_context():
    create_and_seed_db()


@app.route('/')
def index():
    return redirect(url_for('parte_diario'))

@app.route('/parte_diario')
def parte_diario():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    hoy = date.today()

    roturas = Probeta.query.filter(Probeta.fecha_ensayo == hoy).all()
    roturas_hoy = []
    for prob in roturas:
        if prob.parte not in roturas_hoy:
            roturas_hoy.append(prob.parte)

    obras = Obra.query.order_by(Obra.nombre).all()
    partes = ParteDiario.query.order_by(ParteDiario.fecha.desc(), ParteDiario.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    total_pages = partes.pages if partes.pages >= 1 else 1

    return render_template(
        'parte_diario.html',
        obras=obras,
        partes=partes,
        hoy=hoy,
        roturas_hoy=roturas_hoy,
        page=page,
        total_pages=total_pages
    )

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
    formulas_paginate = Formula.query.order_by(Formula.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
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

@app.route('/api/obras', methods=['POST'])
def api_guardar_obra():
    data = request.json
    try:
        obra_id = data.get('id')
        nombre = data.get('nombre')
        fecha = datetime.strptime(data.get('fecha'), '%Y-%m-%d').date() if data.get('fecha') else None
        formulas_ids = data.get('formulas', [])

        if obra_id:
            obra = Obra.query.get_or_404(obra_id)
            obra.nombre = nombre
            obra.fecha = fecha
        else:
            obra = Obra(nombre=nombre, fecha=fecha)
            db.session.add(obra)
            db.session.flush()

        obra.formulas.clear()
        for f_id in formulas_ids:
            formula = Formula.query.get(f_id)
            if formula:
                obra.formulas.append(formula)

        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Obra guardada', 'id': obra.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/obras/<int:obra_id>')
def api_get_obra(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    return jsonify({
        'id': obra.id,
        'nombre': obra.nombre,
        'fecha': obra.fecha.strftime('%Y-%m-%d') if obra.fecha else None,
        'formulas': [f.id for f in obra.formulas]
    })

@app.route('/api/obras/<int:obra_id>', methods=['DELETE'])
def api_eliminar_obra(obra_id):
    obra = Obra.query.get(obra_id)
    if not obra:
        return jsonify({'ok': False, 'error': 'No encontrado'}), 404
    db.session.delete(obra)
    db.session.commit()
    return jsonify({'ok': True})

from datetime import time as dtime

@app.route('/api/guardar_parte', methods=['POST'])
def api_guardar_parte():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'ok': False, 'error': 'No se recibieron datos JSON'}), 400

    try:
        parte_id = data.get('id')

        fecha_raw = data.get('fecha')
        if not fecha_raw:
            return jsonify({'ok': False, 'error': 'Campo "fecha" requerido'}), 400
        try:
            fecha = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
        except Exception:
            return jsonify({'ok': False, 'error': f'Formato de fecha inválido: {fecha_raw}'}), 400

        try:
            obra_id = int(data.get('obra_id')) if data.get('obra_id') not in (None, '') else None
            clase_id = int(data.get('clase_id')) if data.get('clase_id') not in (None, '') else None
        except ValueError:
            return jsonify({'ok': False, 'error': 'IDs de obra/clase deben ser numéricos'}), 400

        if not obra_id or not clase_id:
            return jsonify({'ok': False, 'error': 'Obra y Clase son requeridos'}), 400

        hora_raw = data.get('hora_despacho')
        hora_despacho = None
        if hora_raw:
            try:
                hora_despacho = datetime.strptime(hora_raw, '%H:%M').time()
            except Exception:
                return jsonify({'ok': False, 'error': f'Formato de hora inválido: {hora_raw}'}), 400

        def safe_float(val):
            if val is None or val == '':
                return None
            try:
                return float(val)
            except Exception:
                return None

        cantidad_m3 = safe_float(data.get('cantidad_m3'))
        asentamiento_cm = safe_float(data.get('asentamiento_cm'))

        usa_probetas = bool(data.get('usa_probetas', False))
        probetas_data = data.get('probetas', []) or []

        if parte_id:
            parte = ParteDiario.query.get_or_404(parte_id)
            parte.fecha = fecha
            parte.obra_id = obra_id
            parte.clase_id = clase_id
            parte.hora_despacho = hora_despacho
            parte.cantidad_m3 = cantidad_m3
            parte.asentamiento_cm = asentamiento_cm
            parte.usa_probetas = usa_probetas
            parte.probetas[:] = []
            db.session.flush()
        else:
            parte = ParteDiario(
                fecha=fecha,
                obra_id=obra_id,
                clase_id=clase_id,
                hora_despacho=hora_despacho,
                cantidad_m3=cantidad_m3,
                asentamiento_cm=asentamiento_cm,
                usa_probetas=usa_probetas
            )
            db.session.add(parte)
            db.session.flush()

        if usa_probetas and probetas_data:
            for p in probetas_data:
                fecha_p = p.get('fecha_ensayo') or p.get('fecha')
                edad_raw = p.get('edad') if p.get('edad') is not None else p.get('edad_dias')
                lectura_raw = p.get('lectura') if p.get('lectura') is not None else p.get('lectura_prensa_kn')
                resistencia_raw = p.get('resistencia') if p.get('resistencia') is not None else p.get('resistencia_mpa')

                fecha_ensayo = None
                if fecha_p:
                    try:
                        fecha_ensayo = datetime.strptime(fecha_p, '%Y-%m-%d').date()
                    except Exception:
                        fecha_ensayo = None

                try:
                    edad_dias = int(edad_raw) if edad_raw not in (None, '') else None
                except Exception:
                    edad_dias = None

                try:
                    lectura_prensa_kn = float(lectura_raw) if lectura_raw not in (None, '') else None
                except Exception:
                    lectura_prensa_kn = None

                try:
                    resistencia_mpa = float(resistencia_raw) if resistencia_raw not in (None, '') else None
                except Exception:
                    resistencia_mpa = None

                probeta = Probeta(
                    parte_id=parte.id,
                    fecha_ensayo=fecha_ensayo,
                    edad_dias=edad_dias,
                    lectura_prensa_kn=lectura_prensa_kn,
                    resistencia_mpa=resistencia_mpa
                )
                db.session.add(probeta)

        db.session.commit()
        return jsonify({'ok': True, 'id': parte.id})
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
        'probetas': [ {
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

@app.route('/api/guardar_formula', methods=['POST'])
def api_guardar_formula():
    data = request.json
    try:
        clase_id = data.get('clase_id')
        nombre = data.get('nombre')
        items = data.get('items', [])
        
        formula = Formula(clase_id=clase_id, nombre=nombre)
        db.session.add(formula)
        db.session.flush()
        
        for item in items:
            formula_item = FormulaItem(
                formula_id=formula.id,
                material=item['material'],
                cantidad=item['cantidad'],
                unidad=item['unidad']
            )
            db.session.add(formula_item)
        
        db.session.commit()
        return jsonify({'ok': True, 'id': formula.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/formulas')
def api_get_formulas():
    formulas = Formula.query.order_by(Formula.id.desc()).all()
    result = []
    for f in formulas:
        result.append({
            'id': f.id,
            'clase_nombre': f.clase.nombre,
            'nombre': f.nombre,
            'items': [{'material': i.material, 'cantidad': i.cantidad, 'unidad': i.unidad} for i in f.items]
        })
    return jsonify(result)

@app.route('/api/formulas/<int:formula_id>', methods=['DELETE'])
def api_eliminar_formula(formula_id):
    formula = Formula.query.get(formula_id)
    if not formula:
        return jsonify({'ok': False, 'error': 'No encontrado'}), 404
    db.session.delete(formula)
    db.session.commit()
    return jsonify({'ok': True})



@app.route('/informes')
def informes():

    clases = Clase.query.all()
    datos = []

    OBJETIVOS_RESISTENCIA = {
        "H8": 8,
        "H13": 13,
        "H15": 15,
        "H17": 17,
        "H20": 20,
        "H21": 21,
        "H25": 25,
        "H30": 30
    }

    for c in clases:


        partes_con_asent = (
            ParteDiario.query
            .filter(ParteDiario.clase_id == c.id)
            .filter(ParteDiario.asentamiento_cm.isnot(None))
            .all()
        )

        asentamientos_vals = [p.asentamiento_cm for p in partes_con_asent]

        if asentamientos_vals:
            promedio_asentamiento = round(sum(asentamientos_vals) / len(asentamientos_vals), 2)
        else:
            promedio_asentamiento = None


        probRes = (
            Probeta.query
            .join(ParteDiario, Probeta.parte_id == ParteDiario.id)
            .filter(ParteDiario.clase_id == c.id)
            .filter(Probeta.resistencia_mpa.isnot(None))
            .all()
        )

        if probRes:
            valores = [p.resistencia_mpa for p in probRes]
            promedio_resistencia = round(sum(valores) / len(valores), 2)
        else:
            promedio_resistencia = None

        objetivo_resistencia = OBJETIVOS_RESISTENCIA.get(c.nombre)


        try:
            mpa = int(''.join(filter(str.isdigit, c.nombre)))
        except:
            mpa = 0

        datos.append({
            "nombre": c.nombre,
            "mpa": mpa,
            "promedio": promedio_asentamiento,
            "promedio_resistencia": promedio_resistencia,
            "objetivo_resistencia": objetivo_resistencia
        })

    datos.sort(key=lambda x: x["mpa"])

    return render_template("informes.html", datos=datos)


@app.route('/informes/<clase_nombre>')
def informes_detalle(clase_nombre):
    clase = Clase.query.filter_by(nombre=clase_nombre).first_or_404()
    partes = ParteDiario.query.filter_by(clase_id=clase.id).filter(ParteDiario.asentamiento_cm.isnot(None)).order_by(ParteDiario.fecha.asc()).all()
    if not partes:
        return render_template('informes_detalle.html', clase_nombre=clase_nombre,
                               fechas=[], asentamientos=[], promedio=None,
                               promedio_verano=None, promedio_invierno=None)
    fechas = [p.fecha.strftime('%Y-%m-%d') for p in partes]
    asentamientos = [p.asentamiento_cm for p in partes]
    promedio = mean(asentamientos)
    ref_sup = promedio + 2
    ref_inf = promedio - 2
    def es_verano(m): return m in [12,1,2]
    def es_invierno(m): return m in [6,7,8]
    asentamientos_verano = [p.asentamiento_cm for p in partes if es_verano(p.fecha.month)]
    asentamientos_invierno = [p.asentamiento_cm for p in partes if es_invierno(p.fecha.month)]
    promedio_verano = mean(asentamientos_verano) if asentamientos_verano else None
    promedio_invierno = mean(asentamientos_invierno) if asentamientos_invierno else None
    return render_template(
        'informes_detalle.html',
        clase_nombre=clase_nombre,
        clase=clase,
        fechas=fechas,
        asentamientos=asentamientos,
        promedio=promedio,
        ref_sup=ref_sup,
        ref_inf=ref_inf,
        promedio_verano=promedio_verano,
        promedio_invierno=promedio_invierno
    )
    

if __name__ == '__main__':
    app.run(debug=True)
