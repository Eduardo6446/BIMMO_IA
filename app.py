# -*- coding: utf-8 -*-
"""
Este script es la versión 5 y FINAL de la Fase 1 + INICIO FASE 2.
Características:
1. Carga la base de conocimiento desde un archivo JSON externo ('base_conocimiento.json').
2. Implementa Autenticación Básica (Basic Auth) para proteger la API.
3. Mantiene la lógica del Sistema Experto.
4. [NUEVO] Implementa endpoint de recolección de datos para entrenamiento (Fase 2).

Autor: Tu Nombre/Nombre del Proyecto
Fecha: 20/10/2025
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os
import csv
from datetime import datetime
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

# --- CONFIGURACIÓN DE SEGURIDAD ---
# En producción, estas credenciales deberían estar en variables de entorno.

AUTH_USERNAME = os.getenv("AUTH_USERNAME")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")

# --- FASE 2: CONFIGURACIÓN DE RECOLECCIÓN DE DATOS ---
ARCHIVO_ENTRENAMIENTO = 'datos_entrenamiento_fase2.csv'

def inicializar_archivo_entrenamiento():
    """
    Crea el archivo CSV con cabeceras si no existe.
    Este archivo acumulará la 'sabiduría' del mundo real para entrenar la IA futura.
    """
    if not os.path.exists(ARCHIVO_ENTRENAMIENTO):
        try:
            with open(ARCHIVO_ENTRENAMIENTO, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'fecha_reporte',
                    'usuario_id_hash',      # Identificador anónimo del usuario
                    'modelo_id',            # Ej: Bajaj_Pulsar_NS200
                    'componente_id',        # Ej: bujias
                    'accion_realizada',     # Ej: REEMPLAZAR
                    'km_recomendacion_app', # Qué dijo el manual (Fase 1)
                    'km_realizado_usuario', # Qué hizo el usuario (Realidad)
                    'condicion_reportada'   # ¡EL DATO CLAVE! (ej: "muy_desgastado", "normal")
                ])
            print(f"-> Archivo de entrenamiento '{ARCHIVO_ENTRENAMIENTO}' creado exitosamente.")
        except Exception as e:
            print(f"Error al crear archivo de entrenamiento: {e}")

# Inicializamos el sistema de almacenamiento al arrancar
inicializar_archivo_entrenamiento()

# --- CARGA DE DATOS (FASE 1) ---
def cargar_base_conocimiento():
    """Carga los datos desde el archivo JSON."""
    nombre_archivo = 'base_conocimiento.json'
    if not os.path.exists(nombre_archivo):
        print(f"Error Crítico: No se encontró {nombre_archivo}")
        return {}
    
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
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
    return "Servidor de Mantenimiento Motos IA (v5 + Fase 2) - Activo y Protegido."

@app.route('/predict', methods=['POST'])
@auth_required  # Endpoint de Fase 1: Predicción basada en reglas
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

@app.route('/reportar_mantenimiento', methods=['POST'])
@auth_required  # Endpoint de Fase 2: Recolección de Datos Reales
def reportar_mantenimiento():
    """
    Este endpoint recibe el feedback real cuando un usuario completa un mantenimiento.
    Guarda la información en un CSV para el futuro entrenamiento de Machine Learning.
    
    JSON Esperado:
    {
        "usuario_id_hash": "user_123_abc",
        "modelo_id": "Bajaj_Pulsar_NS200",
        "componente_id": "bujias",
        "accion_realizada": "REEMPLAZAR",
        "km_recomendacion_app": 10000,
        "km_realizado_usuario": 10250,
        "condicion_reportada": "muy_desgastado" 
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Cuerpo de solicitud vacío"}), 400

        # Validar campos mínimos necesarios para un dato de entrenamiento útil
        campos_requeridos = ['usuario_id_hash', 'modelo_id', 'componente_id', 'km_realizado_usuario', 'condicion_reportada']
        if not all(k in data for k in campos_requeridos):
            return jsonify({"error": f"Faltan campos requeridos. Necesarios: {campos_requeridos}"}), 400

        # Guardar en el archivo de entrenamiento (CSV)
        with open(ARCHIVO_ENTRENAMIENTO, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                data['usuario_id_hash'],
                data['modelo_id'],
                data['componente_id'],
                data.get('accion_realizada', 'DESCONOCIDA'),
                data.get('km_recomendacion_app', 0),
                data['km_realizado_usuario'],
                data['condicion_reportada'] # Este será nuestro 'target' o etiqueta para la IA
            ])
            
        return jsonify({
            "status": "success",
            "mensaje": "Datos de entrenamiento guardados exitosamente. ¡Gracias por contribuir a la IA!"
        }), 201

    except Exception as e:
        return jsonify({"error": f"Error al guardar datos de entrenamiento: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)