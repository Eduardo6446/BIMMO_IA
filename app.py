# -*- coding: utf-8 -*-
"""
Este script es la versión 5 y FINAL de la Fase 1 + INICIO FASE 2.
Características:
1. Carga la base de conocimiento desde 'base_conocimiento.json'.
2. Seguridad: Implementa Basic Auth usando variables de entorno (.env).
3. Datos: Implementa recolección de datos en JSON Lines (.jsonl) para flexibilidad.

Autor: Tu Nombre/Nombre del Proyecto
Fecha: 20/10/2025
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os
from datetime import datetime
from dotenv import load_dotenv # Importamos la librería para leer .env

# 1. Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Ahora leemos las credenciales del entorno. Si no existen, usamos valores por defecto seguros o fallamos.
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin_fallback")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "secure_password_fallback")

# --- FASE 2: CONFIGURACIÓN DE DATOS (JSONL) ---
# Mantenemos .jsonl porque es superior para datos que pueden cambiar de estructura
ARCHIVO_ENTRENAMIENTO = 'datos_entrenamiento_fase2.jsonl'

# --- CARGA DE DATOS (FASE 1) ---
def cargar_base_conocimiento():
    """Carga los datos desde el archivo JSON."""
    nombre_archivo = 'base_conocimiento.json'
    if not os.path.exists(nombre_archivo):
        print(f"Error Crítico: No se encontró {nombre_archivo}")
        return {}
    
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        return json.load(f)

datos_motos = cargar_base_conocimiento()
print(f"Base de conocimiento cargada: {len(datos_motos)} modelos disponibles.")
print(f"Modo de autenticación activo para usuario: {AUTH_USERNAME}")


# --- DECORADOR DE AUTENTICACIÓN ---
def auth_required(f):
    """Protege las rutas verificando User/Pass contra las variables de entorno."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == AUTH_USERNAME and auth.password == AUTH_PASSWORD:
            return f(*args, **kwargs)
        
        return make_response('No autenticado', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated


# --- LÓGICA DEL SISTEMA EXPERTO ---
def seleccionar_perfil_moto(modelo_buscado, cilindrada):
    if modelo_buscado in datos_motos:
        return modelo_buscado
    else:
        if cilindrada <= 150:
            return "Generica_Trabajo_150cc"
        else:
            return "Generica_Urbana_250cc"

def calcular_probabilidad_mantenimiento(perfil_moto, kilometraje_actual):
    if perfil_moto not in datos_motos:
        return []
        
    tareas = datos_motos[perfil_moto]["tareas_mantenimiento"]
    resultados = []

    for tarea in tareas:
        intervalo_km = tarea["intervalo"].get("kilometros")
        
        if intervalo_km is not None and intervalo_km > 0:
            if kilometraje_actual % intervalo_km == 0 and kilometraje_actual > 0:
                probabilidad = 1.0
            else:
                km_en_ciclo_actual = kilometraje_actual % intervalo_km
                probabilidad = km_en_ciclo_actual / intervalo_km
            
            resultados.append({
                "componente": tarea["componente_nombre_comun"],
                "accion": tarea["accion"],
                "probabilidad": round(probabilidad, 2),
                "notas": tarea.get("notas_tecnicas", "")
            })

    return sorted(resultados, key=lambda x: x["probabilidad"], reverse=True)


# --- RUTAS DE LA API ---

@app.route('/')
def home():
    return "Servidor de Mantenimiento Motos IA (v5 Safe) - Activo."

@app.route('/predict', methods=['POST'])
@auth_required
def predict_maintenance():
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "Cuerpo vacío"}), 400
            
        modelo_id = data.get('modelo_id')
        cilindrada = data.get('cilindrada')
        km_actual = data.get('km_actual')

        if not all([modelo_id, cilindrada, km_actual is not None]):
            return jsonify({"error": "Faltan datos requeridos"}), 400
        
        perfil_seleccionado = seleccionar_perfil_moto(modelo_id, int(cilindrada))
        recomendaciones = calcular_probabilidad_mantenimiento(perfil_seleccionado, int(km_actual))
        info_moto_usada = datos_motos[perfil_seleccionado]['info_moto']

        return jsonify({
            "status": "success",
            "perfil_usado": perfil_seleccionado,
            "info_perfil": info_moto_usada,
            "km_analizado": km_actual,
            "recomendaciones": recomendaciones
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reportar_mantenimiento', methods=['POST'])
@auth_required
def reportar_mantenimiento():
    """Guarda reporte en JSONL (Append Mode)."""
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "Cuerpo vacío"}), 400

        campos_requeridos = ['usuario_id_hash', 'modelo_id', 'componente_id', 'condicion_reportada']
        if not all(k in data for k in campos_requeridos):
            return jsonify({"error": f"Faltan campos: {campos_requeridos}"}), 400

        registro = data.copy()
        registro['fecha_servidor'] = datetime.now().isoformat()

        # Guardamos en JSONL
        with open(ARCHIVO_ENTRENAMIENTO, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro) + "\n")
            
        return jsonify({"status": "success", "mensaje": "Dato guardado."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)