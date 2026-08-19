# Hormigón

Sistema para el análisis de producción y la generación de informes de hormigón.

## Stack

- **Backend:** Python + Flask
- **ORM:** Flask-SQLAlchemy + SQLAlchemy
- **Base de datos:** SQLite
- **Servidor:** Gunicorn
- **Vistas:** Jinja2

## Estructura del proyecto

```
Hormigon/
├── static/               # CSS, JavaScript y recursos estáticos
├── templates/            # Plantillas de la interfaz
├── app.py                # Aplicación principal
├── requirements.txt      # Dependencias de Python
└── database.db           # Base de datos local
```

## Módulos

- **Producción:** registro y seguimiento de la producción de hormigón.
- **Análisis:** evaluación de resultados y parámetros de producción.
- **Resistencia:** cálculos y control de resistencia del hormigón.
- **Informes:** generación de reportes operativos.
- **Interfaz web:** consulta y gestión de la información.
