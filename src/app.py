# -*- coding: utf-8 -*-
"""
SERVIDOR FINAL (FASE 4 - CORREGIDO): CEREBRO HÍBRIDO + HISTORIAL
Combina:
1. Sistema Experto (Reglas del Manual)
2. Inteligencia Artificial (Red Neuronal)
3. [NUEVO] Historial personalizado del usuario (Sobrescribe el cálculo teórico)
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os
import numpy as np
import tensorflow as tf
import joblib
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

AUTH_USERNAME = os.getenv("AUTH_USERNAME")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")
ARCHIVO_ENTRENAMIENTO = '../data/datos_usuarios.jsonl'

# --- CARGAR IA ---
print("\n⏳ Cargando Librerias y modelos\n")

try:
    model = tf.keras.models.load_model('../models/30112025e7OK/modelo_mantenimiento_v1.h5')
    scaler_km = joblib.load('../models/30112025e7OK/scaler_km.pkl')
    le_condicion = joblib.load('../models/30112025e7OK/encoder_condicion.pkl')
    feature_columns = joblib.load('../models/30112025e7OK/feature_columns.pkl')
    
    print("✅ Librerias y modelos cargados correctamente.")
    
except Exception as e:
    print(f"\n⚠️ Advertencia: No se cargó la IA ({e}). Se usará solo modo manual.\n")
    model = None

# --- CARGAR BASE DE DATOS ---
def cargar_base_conocimiento():
    if not os.path.exists('../data/base.json'): return {}
    with open('../data/base.json', 'r', encoding='utf-8') as f:
        return json.load(f)

datos_motos = cargar_base_conocimiento()

# --- FUNCIONES DE CÁLCULO ---

def consultar_ia(modelo_id, componente_id, km_actual):
    """Pregunta a la red neuronal."""
    if model is None: return "IA_NO_DISPONIBLE", 0.0
    try:
        input_vector = np.zeros(len(feature_columns))
        
        col_mod = f"modelo_id_{modelo_id}"
        col_comp = f"componente_id_{componente_id}"
        
        if col_mod in feature_columns: input_vector[feature_columns.index(col_mod)] = 1
        if col_comp in feature_columns: input_vector[feature_columns.index(col_comp)] = 1
            
        km_scl = scaler_km.transform(np.array([[float(km_actual)]]))[0][0]
        final_features = np.hstack(([km_scl], input_vector)).reshape(1, -1)
        
        prediccion = model.predict(final_features, verbose=0)
        
        clase_ganadora = np.argmax(prediccion)
        estado = le_condicion.inverse_transform([clase_ganadora])[0]
        confianza = float(np.max(prediccion))
        return estado, confianza
    except Exception:
        return "ERROR_IA", 0.0

def analizar_mantenimiento_completo(perfil_moto, km_actual_moto, historial_usuario):
    """
    Analiza el mantenimiento considerando el historial real del usuario si existe.
    historial_usuario: Diccionario { 'aceite_motor': 11000, 'bujias': 10000 }
    """
    if perfil_moto not in datos_motos: return []
    
    tareas = datos_motos[perfil_moto]["tareas_mantenimiento"]
    resultados = []

    for tarea in tareas:
        comp_id = tarea["componente_id"]
        intervalo_km = tarea["intervalo"].get("kilometros")
        
        urgencia_manual = 0.0
        km_recorridos_pieza = 0
        origen_calculo = "teorico" # o "real"

        if intervalo_km:
            # LÓGICA CORREGIDA: ¿Tenemos dato real del usuario?
            if comp_id in historial_usuario:
                # El usuario nos dijo cuándo lo cambió por última vez
                km_ultimo_cambio = historial_usuario[comp_id]
                km_recorridos_pieza = km_actual_moto - km_ultimo_cambio
                
                # Evitamos números negativos si el usuario se equivocó
                if km_recorridos_pieza < 0: km_recorridos_pieza = 0
                
                urgencia_manual = km_recorridos_pieza / intervalo_km
                origen_calculo = "basado_en_historial"
            else:
                # No sabemos nada, asumimos cálculo teórico (ciclos perfectos)
                if km_actual_moto % intervalo_km == 0 and km_actual_moto > 0:
                    urgencia_manual = 1.0
                    km_recorridos_pieza = intervalo_km
                else:
                    km_recorridos_pieza = km_actual_moto % intervalo_km
                    urgencia_manual = km_recorridos_pieza / intervalo_km

        # Consultamos a la IA (siempre basada en el KM total de la moto para predecir desgaste global)
        estado_ia, confianza_ia = consultar_ia(perfil_moto, comp_id, km_actual_moto)
        
        resultados.append({
            "componente": tarea["componente_nombre_comun"],
            "componente_id": comp_id, # Útil para que la app sepa qué ID enviar de vuelta
            "accion": tarea["accion"],
            "calculo": {
                "urgencia": round(urgencia_manual, 2), # 0.5 = 50%, 1.0 = 100% (Vencido)
                "km_recorridos_pieza": km_recorridos_pieza,
                "intervalo_fabricante": intervalo_km,
                "origen_dato": origen_calculo
            },
            "prediccion_ia": {
                "estado_probable": estado_ia,
                "confianza": round(confianza_ia, 2)
            },
            "notas": tarea.get("notas_tecnicas", "")
        })

    # Ordenamiento inteligente
    def factor_ordenamiento(item):
        score = item['calculo']['urgencia']
        if item['prediccion_ia']['estado_probable'] == 'fallo_critico': score += 2.0
        return score

    return sorted(resultados, key=factor_ordenamiento, reverse=True)


# --- RUTAS ---
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == AUTH_USERNAME and auth.password == AUTH_PASSWORD:
            return f(*args, **kwargs)
        return make_response('Login Required', 401, {'WWW-Authenticate': 'Basic'})
    return decorated

#@app.route('/predict', methods=['POST'])
#@auth_required
# def predict():
#     try:
#         # Usamos force=True para evitar el error 415 si faltan headers
#         data = request.get_json(force=True) 
#         mod_id = data.get('modelo_id')
#         cil = data.get('cilindrada')
#         km = data.get('km_actual')
        
#         # Recibimos el historial como una lista de objetos y lo convertimos a diccionario para búsqueda rápida
#         # Entrada: [ {"componente_id": "aceite", "km_mantenimiento": 1000} ]
#         # Salida:  { "aceite": 1000 }
#         historial_raw = data.get('historial_usuario', [])
#         historial_dict = { item['componente_id']: item['km_mantenimiento'] for item in historial_raw }
        
#         perfil = mod_id if mod_id in datos_motos else ("Generica_Trabajo_150cc" if int(cil) <= 150 else "Generica_Urbana_250cc")
        
#         recomendaciones = analizar_mantenimiento_completo(perfil, int(km), historial_dict)
        
#         return jsonify({
#             "status": "success",
#             "moto_analizada": perfil,
#             "analisis": recomendaciones
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['POST'])
@auth_required
def predict():
    if not model:
        return jsonify({"error": "La IA no está disponible."}), 500

    try:
        # 1. Obtener datos (Formato Simple)
        # Esperamos: {"modelo": "Bajaj...", "componente": "bujias", "km": 12500}
        data = request.get_json(force=True)
        
        modelo_nombre = data.get('modelo')
        componente_nombre = data.get('componente')
        km_usuario = data.get('km')

        if not all([modelo_nombre, componente_nombre, km_usuario is not None]):
            return jsonify({"error": "Faltan datos. Enviar: modelo, componente, km"}), 400

        # 2. Construir Vector One-Hot (Igual que en Colab Celda 8)
        input_vector = np.zeros(len(feature_columns))
        
        col_modelo = f"modelo_id_{modelo_nombre}"
        col_componente = f"componente_id_{componente_nombre}"
        
        # Activar interruptores si existen en el mapa
        if col_modelo in feature_columns:
            input_vector[feature_columns.index(col_modelo)] = 1
        
        if col_componente in feature_columns:
            input_vector[feature_columns.index(col_componente)] = 1

        # 3. Escalar Kilometraje
        km_scl = scaler_km.transform(np.array([[float(km_usuario)]]))[0][0]
        
        # 4. Unir todo para la red neuronal
        final_features = np.hstack(([km_scl], input_vector)).reshape(1, -1)
        
        # 5. Predecir
        prediccion = model.predict(final_features, verbose=0)
        
        # 6. Interpretar
        clase_ganadora = np.argmax(prediccion)
        estado_texto = le_condicion.inverse_transform([clase_ganadora])[0]
        confianza = float(np.max(prediccion)) * 100

        return jsonify({
            "status": "success",
            "modelo": modelo_nombre,
            "componente": componente_nombre,
            "km_analizado": km_usuario,
            "prediccion_ia": estado_texto,
            "confianza": f"{confianza:.2f}%"
        })

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/reportar_mantenimiento', methods=['POST'])
@auth_required
def reportar():
    """
    Guarda datos enriquecidos con la lógica del manual en un orden específico.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data: return jsonify({"error": "JSON vacío"}), 400

        # 1. Extraer datos del request
        usuario_id_hash = data.get('usuario_id_hash')
        modelo_id = data.get('modelo_id')
        componente_id = data.get('componente_id')
        accion_realizada = data.get('accion_realizada', 'REEMPLAZAR') # Valor por defecto
        km_realizado = data.get('km_realizado_usuario')
        condicion_reportada = data.get('condicion_reportada')

        # 2. Calcular KM Recomendado (Lógica de Negocio)
        km_teorico = 0
        if modelo_id in datos_motos:
            tareas = datos_motos[modelo_id].get('tareas_mantenimiento', [])
            tarea = next((t for t in tareas if t['componente_id'] == componente_id), None)
            
            if tarea and 'intervalo' in tarea:
                intervalo = tarea['intervalo'].get('kilometros', 0)
                if intervalo > 0 and km_realizado:
                    ciclo = round(km_realizado / intervalo)
                    if ciclo < 1: ciclo = 1
                    km_teorico = intervalo * ciclo

        # 3. Construir Diccionario Ordenado (Para que el JSONL quede bonito)
        ahora = datetime.now().isoformat()
        
        registro_ordenado = {
            "fecha_reporte": now_iso(), # Función auxiliar o repetimos ahora
            "usuario_id_hash": usuario_id_hash,
            "modelo_id": modelo_id,
            "componente_id": componente_id,
            "accion_realizada": accion_realizada,
            "km_recomendacion_app": km_teorico,
            "km_realizado_usuario": km_realizado,
            "condicion_reportada": condicion_reportada,
        }
        # Nota: usé la misma variable 'ahora' para fecha_reporte y fecha_servidor por consistencia,
        # pero puedes generar una nueva si quieres microsegundos de diferencia.
        registro_ordenado['fecha_servidor'] = datetime.now().isoformat()

        # 4. Guardar
        os.makedirs(os.path.dirname(ARCHIVO_ENTRENAMIENTO), exist_ok=True)
        with open(ARCHIVO_ENTRENAMIENTO, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro_ordenado) + "\n")
            
        return jsonify({"status": "saved", "enriched_data": registro_ordenado}), 201

    except Exception as e:
        print(f"Error guardando reporte: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/actualizar_kilometraje', methods=['POST'])
@auth_required
def actualizar_kilometraje():
    """
    Registra solo el avance del odómetro (sin mantenimiento).
    Útil para que la IA sepa el ritmo de uso de la moto.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data: return jsonify({"error": "JSON vacío"}), 400

        # 1. Extraer datos
        usuario_id_hash = data.get('usuario_id_hash')
        modelo_id = data.get('modelo_id')
        km_actual = data.get('km_actual')

        if not all([modelo_id, km_actual is not None]):
             return jsonify({"error": "Faltan datos: modelo_id, km_actual"}), 400

        # 2. Construir Registro (Compatible con el dataset de entrenamiento)
        ahora = datetime.now().isoformat()
        
        registro_ordenado = {
            "fecha_reporte": ahora,
            "usuario_id_hash": usuario_id_hash,
            "modelo_id": modelo_id,
            "componente_id": "N/A",           # No aplica a una pieza específica
            "accion_realizada": "ACTUALIZACION_KM", # Marcador especial
            "km_recomendacion_app": 0,        # No hay recomendación aquí
            "km_realizado_usuario": km_actual,
            "condicion_reportada": "operativo", # Asumimos que sigue rodando
            "fecha_servidor": now_iso()
        }

        # 3. Guardar
        os.makedirs(os.path.dirname(ARCHIVO_ENTRENAMIENTO), exist_ok=True)
        with open(ARCHIVO_ENTRENAMIENTO, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro_ordenado) + "\n")
            
        return jsonify({"status": "saved", "message": "Kilometraje registrado"}), 201

    except Exception as e:
        print(f"Error actualizando km: {e}")
        return jsonify({"error": str(e)}), 500

def now_iso():
    return datetime.now().isoformat()
    
# saludo
@app.route('/', methods=['GET'])
def home():
    return "Servidor de Mantenimiento de Motos con IA y Historial - En línea"

if __name__ == '__main__':
    app.run()