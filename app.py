from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_super_segura_2024'

# Conexión a MongoDB
MONGO_URI = "mongodb+srv://delcarmengonzalezabrilcbtis272_db_user:admin123@escuela.ivy474z.mongodb.net/eltrackr?retryWrites=true&w=majority"

print("🔧 Intentando conectar a MongoDB...")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.eltrackr
    coleccion = db.huellas_carbono
    # Verificar conexión
    client.admin.command('ping')
    print("✅ CONEXIÓN EXITOSA a MongoDB Atlas") 
    print(f"📊 Base de datos: {db.name}")
    print(f"📄 Colección: {coleccion.name}")
    CONEXION_ACTIVA = True
except Exception as e:
    print(f"❌ ERROR de conexión: {e}")
    coleccion = None
    CONEXION_ACTIVA = False

def calcular_huella_co2(energia, agua, transporte):
    """Calcula la huella de carbono"""
    factor_energia = 0.5
    factor_agua = 0.0003
    factor_transporte = 0.2
    
    co2_total = (energia * factor_energia) + (agua * factor_agua) + (transporte * factor_transporte)
    return round(co2_total, 2)

def generar_recomendaciones(co2_total, energia, agua, transporte):
    """Genera recomendaciones personalizadas"""
    recomendaciones = []
    
    if co2_total > 500:
        recomendaciones.append("🚨 Tu huella es alta. Considera reducir tu consumo energético.")
    elif co2_total > 200:
        recomendaciones.append("⚠️ Huella moderada. Pequeños cambios pueden ayudar.")
    else:
        recomendaciones.append("✅ Excelente! Mantén tus buenos hábitos.")
    
    if energia > 300:
        recomendaciones.append("💡 Reduce el consumo de energía usando electrodomésticos eficientes")
    if agua > 200:
        recomendaciones.append("💧 Ahorra agua con duchas más cortas")
    if transporte > 100:
        recomendaciones.append("🚗 Usa transporte público o comparte viajes")
    
    recomendaciones.append(f"🌳 Planta {max(1, int(co2_total/50))} árboles para compensar")
    return recomendaciones

def verificar_conexion():
    """Verifica si la conexión a MongoDB está activa"""
    try:
        if coleccion is not None:
            coleccion.find_one()
            return True
        return False
    except:
        return False

@app.route('/')
def index():
    """Página principal"""
    try:
        if not verificar_conexion():
            flash('⚠️ Base de datos no disponible', 'warning')
            return render_template('index.html', registros=[], total_registros=0, promedio_co2=0, mejor_registro=None, total_co2=0)
        
        registros = list(coleccion.find().sort("fecha_creacion", -1))
        print(f"📊 Se encontraron {len(registros)} registros")
        
        # Calcular estadísticas
        total_registros = len(registros)
        
        if total_registros > 0:
            # Calcular promedio CO2
            suma_co2 = sum(registro.get('co2_total', 0) for registro in registros)
            promedio_co2 = round(suma_co2 / total_registros, 2)
            
            # Encontrar mejor registro (menor CO2)
            mejor_registro = min(registros, key=lambda x: x.get('co2_total', float('inf')))
            
            # Calcular total CO2
            total_co2 = round(suma_co2, 2)
        else:
            promedio_co2 = 0
            mejor_registro = None
            total_co2 = 0
            
        return render_template('index.html', 
                             registros=registros,
                             total_registros=total_registros,
                             promedio_co2=promedio_co2,
                             mejor_registro=mejor_registro,
                             total_co2=total_co2)
                             
    except Exception as e:
        print(f"❌ Error en index: {e}")
        flash('Error al cargar los datos', 'error')
        return render_template('index.html', registros=[], total_registros=0, promedio_co2=0, mejor_registro=None, total_co2=0)

@app.route('/create', methods=['GET', 'POST'])
def create():
    """Crear nuevo registro"""
    if request.method == 'POST':
        try:
            print("📨 Formulario recibido...")
            
            if not verificar_conexion():
                flash('❌ Error: Base de datos no disponible', 'error')
                return render_template('create.html')
            
            # Obtener datos del formulario
            nombre = request.form.get('nombre', '').strip()
            correo = request.form.get('correo', '').strip()
            energia = request.form.get('energia', '0')
            agua = request.form.get('agua', '0')
            transporte = request.form.get('transporte', '0')
            
            print(f"📝 Datos recibidos: {nombre}, {correo}, {energia}, {agua}, {transporte}")
            
            # Validaciones básicas
            if not nombre or not correo:
                flash('❌ Nombre y correo son obligatorios', 'error')
                return render_template('create.html')
            
            try:
                energia = float(energia)
                agua = float(agua)
                transporte = float(transporte)
            except ValueError:
                flash('❌ Los valores numéricos deben ser válidos', 'error')
                return render_template('create.html')
            
            # Cálculos
            co2_total = calcular_huella_co2(energia, agua, transporte)
            recomendaciones = generar_recomendaciones(co2_total, energia, agua, transporte)
            
            # Crear documento
            nuevo_registro = {
                "nombre": nombre,
                "correo": correo,
                "energia": energia,
                "agua": agua,
                "transporte": transporte,
                "co2_total": co2_total,
                "recomendaciones": recomendaciones,
                "fecha_creacion": datetime.now(),
                "fecha_actualizacion": datetime.now()
            }
            
            print(f"💾 Intentando guardar en MongoDB: {nuevo_registro}")
            
            # Insertar en MongoDB
            resultado = coleccion.insert_one(nuevo_registro)
            print(f"✅ Registro guardado con ID: {resultado.inserted_id}")
            
            flash('🎉 ¡Registro creado exitosamente!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"❌ ERROR al crear registro: {e}")
            flash(f'❌ Error al crear registro: {str(e)}', 'error')
            return render_template('create.html')
    
    # GET request - mostrar formulario
    return render_template('create.html')

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    """Editar registro existente"""
    try:
        if not verificar_conexion():
            flash('❌ Error: Base de datos no disponible', 'error')
            return redirect(url_for('index'))
        
        registro = coleccion.find_one({"_id": ObjectId(id)})
        if not registro:
            flash('❌ Registro no encontrado', 'error')
            return redirect(url_for('index'))

        if request.method == 'POST':
            # Obtener datos del formulario
            nombre = request.form.get('nombre', '').strip()
            correo = request.form.get('correo', '').strip()
            energia = request.form.get('energia', '0')
            agua = request.form.get('agua', '0')
            transporte = request.form.get('transporte', '0')
            
            print(f"✏️ Editando registro {id}: {nombre}, {correo}")
            
            # Validaciones
            if not nombre or not correo:
                flash('❌ Nombre y correo son obligatorios', 'error')
                return render_template('edit.html', registro=registro)
            
            try:
                energia = float(energia)
                agua = float(agua)
                transporte = float(transporte)
            except ValueError:
                flash('❌ Los valores numéricos deben ser válidos', 'error')
                return render_template('edit.html', registro=registro)
            
            # Recalcular CO2
            co2_total = calcular_huella_co2(energia, agua, transporte)
            recomendaciones = generar_recomendaciones(co2_total, energia, agua, transporte)
            
            # Actualizar en MongoDB
            coleccion.update_one(
                {"_id": ObjectId(id)}, 
                {"$set": {
                    "nombre": nombre,
                    "correo": correo,
                    "energia": energia,
                    "agua": agua,
                    "transporte": transporte,
                    "co2_total": co2_total,
                    "recomendaciones": recomendaciones,
                    "fecha_actualizacion": datetime.now()
                }}
            )
            
            flash('✅ Registro actualizado exitosamente!', 'success')
            return redirect(url_for('index'))

        return render_template('edit.html', registro=registro)
    
    except Exception as e:
        print(f"❌ ERROR al editar registro: {e}")
        flash('❌ Error al editar el registro', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<id>')
def delete(id):
    """Eliminar registro"""
    try:
        if not verificar_conexion():
            flash('❌ Error de conexión', 'error')
            return redirect(url_for('index'))
        
        resultado = coleccion.delete_one({"_id": ObjectId(id)})
        if resultado.deleted_count > 0:
            flash('✅ Registro eliminado', 'success')
        else:
            flash('❌ Registro no encontrado', 'error')
    except Exception as e:
        print(f"❌ Error al eliminar: {e}")
        flash('❌ Error al eliminar', 'error')
    
    return redirect(url_for('index'))

@app.route('/view/<id>')
def view(id):
    """Ver detalles de un registro"""
    try:
        if not verificar_conexion():
            flash('❌ Error de conexión', 'error')
            return redirect(url_for('index'))
        
        registro = coleccion.find_one({"_id": ObjectId(id)})
        if not registro:
            flash('❌ Registro no encontrado', 'error')
            return redirect(url_for('index'))
            
        return render_template('view.html', registro=registro)
    except Exception as e:
        print(f"❌ Error al ver registro: {e}")
        flash('❌ Error al cargar el registro', 'error')
        return redirect(url_for('index'))

@app.route('/debug')
def debug():
    """Página de debug"""
    try:
        if verificar_conexion():
            total = coleccion.count_documents({})
            registros = list(coleccion.find().limit(3))
            return {
                "status": "✅ CONECTADO",
                "total_registros": total,
                "ejemplos": str(registros)
            }
        else:
            return {"status": "❌ DESCONECTADO"}
    except Exception as e:
        return {"status": f"❌ ERROR: {str(e)}"}

@app.route('/test-insert')
def test_insert():
    """Ruta para probar la inserción"""
    try:
        if not verificar_conexion():
            return {"status": "❌ Base de datos no disponible"}
        
        test_data = {
            "nombre": "Usuario Test",
            "correo": "test@ejemplo.com",
            "energia": 100,
            "agua": 150,
            "transporte": 30,
            "co2_total": calcular_huella_co2(100, 150, 30),
            "recomendaciones": ["Test recomendación"],
            "fecha_creacion": datetime.now(),
            "fecha_actualizacion": datetime.now()
        }
        
        resultado = coleccion.insert_one(test_data)
        return {
            "status": "✅ Inserción exitosa",
            "id": str(resultado.inserted_id)
        }
    except Exception as e:
        return {"status": f"❌ Error: {str(e)}"}

if __name__ == '__main__':
    print("🚀 Iniciando EL TRACKR...")
    print("📍 URL: http://localhost:5000")
    print("🔍 Debug: http://localhost:5000/debug")
    print("🧪 Test Insert: http://localhost:5000/test-insert")
    app.run(debug=True, host='0.0.0.0', port=5000)
