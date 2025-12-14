# -*- coding: utf-8 -*-
"""
SERVIDOR FINAL (FASE 4 - V3): CEREBRO MATEMÁTICO & LOGICA ESTRICTA
Actualizado para eliminar reseteos fantasma ("Modulo Problem").
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os
import numpy as np
import tensorflow as tf
import pickle
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "secret")

# --- RUTAS DE ARCHIVOS (Dinámicas) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_MODELOS = os.path.join(BASE_DIR, '../models/07122025e1sr/')
ARCHIVO_BASE = os.path.join(BASE_DIR, '../data/base.json')
ARCHIVO_HISTORIAL = os.path.join(BASE_DIR, '../data/datos_usuarios.jsonl')
ARCHIVO_ENTRENAMIENTO = ARCHIVO_HISTORIAL

# --- CARGAR IA ---
print("\n⏳ Cargando Nueva IA Robusta (V2)...\n")

try:
    path_model = os.path.join(DIR_MODELOS, 'modelo_desgaste_v2.h5')
    model = tf.keras.models.load_model(path_model)
    
    path_scaler = os.path.join(DIR_MODELOS, 'scaler.pkl')
    with open(path_scaler, 'rb') as f:
        scaler = pickle.load(f)
        
    path_encoder = os.path.join(DIR_MODELOS, 'encoder.pkl')
    with open(path_encoder, 'rb') as f:
        encoder = pickle.load(f)
        
    print(f"✅ SISTEMA OPERATIVO: Modelo cargado desde {path_model}")
    
except Exception as e:
    print(f"\n⚠️ ERROR CRÍTICO IA: {e}")
    model = None
    scaler = None
    encoder = None

# --- CARGAR BASE DE CONOCIMIENTO ---
def cargar_base_conocimiento():
    if not os.path.exists(ARCHIVO_BASE): return {}
    with open(ARCHIVO_BASE, 'r', encoding='utf-8') as f:
        return json.load(f)

datos_motos = cargar_base_conocimiento()

# --- LÓGICA DE PREDICCIÓN ---

def consultar_ia_robusta(km_pieza_actual, intervalo_manual):
    if model is None or scaler is None: return "IA_OFFLINE", 0.0
    
    try:
        epsilon = 1e-6
        ratio = km_pieza_actual / (intervalo_manual + epsilon)
        diff = km_pieza_actual - intervalo_manual
        
        vector_crudo = np.array([[
            km_pieza_actual,
            intervalo_manual,
            ratio,
            diff
        ]])
        
        vector_scaled = scaler.transform(vector_crudo)
        prediccion = model.predict(vector_scaled, verbose=0)
        
        clase_idx = np.argmax(prediccion)
        estado = encoder.inverse_transform([clase_idx])[0]
        confianza = float(np.max(prediccion))
        
        return estado, confianza
        
    except Exception as e:
        print(f"Error IA: {e}")
        return "ERROR_CALCULO", 0.0

def analizar_mantenimiento(perfil_moto_id, km_moto_total, historial_usuario):
    """
    Cruza datos del manual, historial del usuario y predicciones de la IA.
    CORRECCIÓN CRÍTICA: Eliminado el operador módulo (%) para evitar reseteos automáticos.
    """
    if perfil_moto_id not in datos_motos: return []
    
    tareas = datos_motos[perfil_moto_id]["tareas_mantenimiento"]
    resultados = []

    for tarea in tareas:
        comp_id = tarea["componente_id"]
        intervalo_manual = tarea["intervalo"].get("kilometros")
        
        if not intervalo_manual: continue
        
        # A. DETERMINAR EL ESTADO REAL DE LA PIEZA (Lógica Estricta)
        origen_dato = "teorico"
        km_recorridos_pieza = 0
        
        if comp_id in historial_usuario:
            # CASO 1: Tenemos historial real
            # La pieza tiene el desgaste desde el último cambio hasta hoy.
            km_ultimo_cambio = historial_usuario[comp_id]
            km_recorridos_pieza = km_moto_total - km_ultimo_cambio
            origen_dato = "historial_real"
        else:

            km_recorridos_pieza = km_moto_total

        
        # Evitar negativos
        km_recorridos_pieza = max(0, km_recorridos_pieza)

        # B. CONSULTAR A LA IA
        estado_ia, confianza_ia = consultar_ia_robusta(km_recorridos_pieza, intervalo_manual)
        
        # C. CÁLCULO DE URGENCIA
        urgencia_matematica = km_recorridos_pieza / intervalo_manual
        
        resultados.append({
            "componente": tarea["componente_nombre_comun"],
            "componente_id": comp_id,
            "accion": tarea["accion"],
            "datos_tecnicos": {
                "km_pieza_actual": km_recorridos_pieza,
                "intervalo_fabricante": intervalo_manual,
                "origen": origen_dato,
                "porcentaje_uso": round(urgencia_matematica * 100, 1)
            },
            "analisis_ia": {
                "diagnostico": estado_ia,
                "confianza": round(confianza_ia * 100, 1)
            },
            "alerta_nivel": 1 if estado_ia in ['fallo_critico', 'muy_desgastado'] else 0
        })

    # Ordenar por gravedad
    def factor_orden(item):
        prioridad = item['datos_tecnicos']['porcentaje_uso']
        if item['analisis_ia']['diagnostico'] == 'fallo_critico': prioridad += 200
        elif item['analisis_ia']['diagnostico'] == 'muy_desgastado': prioridad += 100
        return prioridad

    return sorted(resultados, key=factor_orden, reverse=True)


# --- SEGURIDAD ---
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == AUTH_USERNAME and auth.password == AUTH_PASSWORD:
            return f(*args, **kwargs)
        return make_response('Login Required', 401, {'WWW-Authenticate': 'Basic'})
    return decorated

# --- ENDPOINTS ---

@app.route('/predict_full', methods=['POST'])
@auth_required
def predict_full():
    try:
        data = request.get_json(force=True)
        modelo_id = data.get('modelo_id')
        km_actual = data.get('km_actual')
        historial = data.get('historial_usuario', {}) 
        
        if not modelo_id or km_actual is None:
            return jsonify({"error": "Faltan datos"}), 400

        analisis = analizar_mantenimiento(modelo_id, float(km_actual), historial)
        
        return jsonify({
            "moto": modelo_id,
            "km_total": km_actual,
            "diagnostico_global": analisis
        })

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/test_single', methods=['POST'])
@auth_required
def test_single():
    try:
        data = request.get_json(force=True)
        km_pieza = data.get('km_pieza')
        intervalo = data.get('intervalo_manual')
        
        if km_pieza is None or intervalo is None:
            return jsonify({"error": "Faltan datos"}), 400
            
        estado, conf = consultar_ia_robusta(float(km_pieza), float(intervalo))
        
        return jsonify({
            "input": {"km": km_pieza, "target": intervalo},
            "ia_output": estado,
            "confianza": f"{conf*100:.2f}%"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    estado_ia = "ONLINE 🟢" if model else "OFFLINE 🔴"
    return f"Servidor de Mantenimiento Inteligente V3 (Strict Mode)<br>Estado IA: {estado_ia}"

@app.route('/get_maintenance_options', methods=['GET'])
def get_maintenance_options():
    modelo_id = request.args.get('modelo_id')
    
    if not modelo_id or modelo_id not in datos_motos:
        return jsonify([
            {"id": "aceite_motor", "label": "Aceite de Motor (Genérico)"},
            {"id": "frenos", "label": "Frenos (Genérico)"},
            {"id": "cadena", "label": "Cadena (Genérico)"},
            {"id": "neumaticos", "label": "Neumáticos (Genérico)"}
        ])

    tareas = datos_motos[modelo_id].get("tareas_mantenimiento", [])
    opciones_unicas = {}
    
    for t in tareas:
        cid = t['componente_id']
        label = t['componente_nombre_comun']
        if cid not in opciones_unicas:
            opciones_unicas[cid] = label
    
    lista_final = [{"id": k, "label": v} for k, v in opciones_unicas.items()]
    lista_final.append({"id": "otro_mantenimiento", "label": "Otro / Reparación General"})
    
    return jsonify(lista_final)

@app.route('/reportar_mantenimiento', methods=['POST'])
@auth_required
def reportar():
    try:
        data = request.get_json(force=True, silent=True)
        if not data: return jsonify({"error": "JSON vacío"}), 400

        usuario_id_hash = data.get('usuario_id_hash')
        modelo_id = data.get('modelo_id')
        componente_id = data.get('componente_id')
        accion_realizada = data.get('accion_realizada', 'REEMPLAZAR')
        km_realizado = data.get('km_realizado_usuario')
        condicion_reportada = data.get('condicion_reportada')

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

        registro_ordenado = {
            "fecha_reporte": now_iso(),
            "usuario_id_hash": usuario_id_hash,
            "modelo_id": modelo_id,
            "componente_id": componente_id,
            "accion_realizada": accion_realizada,
            "km_recomendacion_app": km_teorico,
            "km_realizado_usuario": km_realizado,
            "condicion_reportada": condicion_reportada,
            "fecha_servidor": now_iso()
        }

        os.makedirs(os.path.dirname(ARCHIVO_ENTRENAMIENTO), exist_ok=True)
        with open(ARCHIVO_ENTRENAMIENTO, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro_ordenado) + "\n")
            
        return jsonify({"status": "saved", "enriched_data": registro_ordenado}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def now_iso():
    return datetime.now().isoformat()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)