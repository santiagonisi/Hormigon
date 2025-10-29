from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/')
def inicio():
    return redirect(url_for('parte_diario'))

@app.route('/parte_diario')
def parte_diario():
    return render_template('parte_diario.html')

@app.route('/obras')
def obras():
    return render_template('obras.html')

@app.route('/formulas')
def formulas():
    return render_template('formulas.html')

if __name__ == '__main__':
    app.run(debug=True)
