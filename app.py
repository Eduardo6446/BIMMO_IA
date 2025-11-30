# -*- coding: utf-8 -*-
"""
Este script es la versión 5 y FINAL de la Fase 1.
Características:
1. Carga la base de conocimiento desde un archivo JSON externo ('base_conocimiento.json').
2. Implementa Autenticación Básica (Basic Auth) para proteger la API.
3. Mantiene la lógica del Sistema Experto.

Autor: Tu Nombre/Nombre del Proyecto
Fecha: 20/10/2025
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os

import dotenv
dotenv.load_dotenv()

AUTH_USERNAME = os.getenv("AUTH_USERNAME")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")

app = Flask(__name__)


# --- CARGA DE DATOS ---
def cargar_base_conocimiento():
    """Carga los datos desde el archivo JSON."""
    jsonData = 'base.json'
    if not os.path.exists(jsonData):
        print(f"Error Crítico: No se encontró {jsonData}")
        return {}
    with open(jsonData, 'r', encoding='utf-8') as f:
        return json.load(f)

# Cargamos los datos al iniciar el servidor
datos_motos = cargar_base_conocimiento()
print(f"Base de conocimiento cargada: {len(datos_motos)} modelos disponibles.")


# --- DECORADOR DE AUTENTICACIÓN ---
def auth_required(f):
    """
    Decorador para proteger las rutas con Basic Auth.
    Verifica si la solicitud tiene el header 'Authorization' correcto.
    """
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
        # Fallback inteligente
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
    """Ruta simple para verificar que el servidor corre."""
    return "Servidor de Mantenimiento Motos IA (v5) - Activo y Protegido."

@app.route('/predict', methods=['POST'])
@auth_required
def predict_maintenance():
    try:
        data = request.get_json()
        
        # Validaciones
        if not data:
            return jsonify({"error": "Cuerpo de solicitud vacío"}), 400
            
        modelo_id = data.get('modelo_id')
        cilindrada = data.get('cilindrada')
        km_actual = data.get('km_actual')

        if not all([modelo_id, cilindrada, km_actual is not None]):
            return jsonify({"error": "Faltan datos: modelo_id, cilindrada, km_actual"}), 400
        
        # Ejecución
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
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)