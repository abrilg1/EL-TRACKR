from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import os

app = Flask(__name__)

# Variables de entorno
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://<usuario>:<clave>@<cluster>/eltrackr")
client = MongoClient(MONGO_URI)
db = client.eltrackr
coleccion = db.usuarios

@app.route('/')
def index():
    registros = list(coleccion.find())
    return render_template('index.html', registros=registros)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        energia = float(request.form['energia'])
        agua = float(request.form['agua'])
        transporte = float(request.form['transporte'])
        co2_total = round(energia*0.0005 + agua*0.0003 + transporte*0.2, 2)
        recomendaciones = "Planta 10 árboles 🌳 y reduce tu consumo en 15%"
        
        coleccion.insert_one({
            "nombre": nombre,
            "correo": correo,
            "energia": energia,
            "agua": agua,
            "transporte": transporte,
            "co2_total": co2_total,
            "recomendaciones": recomendaciones
        })
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    from bson.objectid import ObjectId
    registro = coleccion.find_one({"_id": ObjectId(id)})

    if request.method == 'POST':
        coleccion.update_one({"_id": ObjectId(id)}, {"$set": {
            "nombre": request.form['nombre'],
            "correo": request.form['correo'],
            "energia": float(request.form['energia']),
            "agua": float(request.form['agua']),
            "transporte": float(request.form['transporte'])
        }})
        return redirect(url_for('index'))

    return render_template('edit.html', registro=registro)

@app.route('/delete/<id>')
def delete(id):
    from bson.objectid import ObjectId
    coleccion.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
