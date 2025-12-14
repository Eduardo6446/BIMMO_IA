# -*- coding: utf-8 -*-
"""
SERVIDOR FINAL (FASE 4 - V6): LÓGICA ESTRICTA SECUENCIAL
Cambio Post-Demo: Se elimina la "Tolerancia de Olvido".
Si no hay registro en historial, el mantenimiento se queda pegado en el hito vencido
(ej. 500km) infinitamente, marcando estado CRÍTICO.
Solo avanza al siguiente hito si existe un registro histórico válido.
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os
import numpy as np
import tensorflow as tf
import pickle
import re
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "secret")

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_MODELOS = os.path.join(BASE_DIR, '../../models')
ARCHIVO_BASE = os.path.join(BASE_DIR, '../../data/base.json')
ARCHIVO_ENTRENAMIENTO = os.path.join(BASE_DIR, '../../data/datos_usuarios.jsonl')

# --- CARGAR IA ---
print("\n⏳ Cargando IA...\n")
try:
    path_model = os.path.join(DIR_MODELOS, 'modelo_desgaste_v2.h5')
    model = tf.keras.models.load_model(path_model)
    with open(os.path.join(DIR_MODELOS, 'scaler.pkl'), 'rb') as f: scaler = pickle.load(f)
    with open(os.path.join(DIR_MODELOS, 'encoder.pkl'), 'rb') as f: encoder = pickle.load(f)
    print("✅ IA ONLINE")
except Exception:
    print("⚠️ IA OFFLINE")
    model, scaler, encoder = None, None, None

# --- CARGAR BASE Y NORMALIZAR LLAVES ---
datos_motos = {}
mapa_normalizado = {}

def normalizar_texto(texto):
    if not texto: return ""
    return re.sub(r'[\s_\-\.]+', '', str(texto)).lower()

def cargar_base_conocimiento():
    global datos_motos, mapa_normalizado
    if not os.path.exists(ARCHIVO_BASE): return
    with open(ARCHIVO_BASE, 'r', encoding='utf-8') as f: 
        datos_motos = json.load(f)
        
    mapa_normalizado = {}
    for key in datos_motos.keys():
        norm_key = normalizar_texto(key)
        mapa_normalizado[norm_key] = key
    
    print(f"✅ Base cargada: {len(datos_motos)} modelos indexados.")

cargar_base_conocimiento()

def buscar_modelo_real(input_id):
    if not input_id: return None
    if input_id in datos_motos: return input_id
    input_norm = normalizar_texto(input_id)
    if input_norm in mapa_normalizado:
        return mapa_normalizado[input_norm]
    return None

def now_iso(): return datetime.now().isoformat()

# --- CEREBRO IA ---
def consultar_ia_robusta(km_pieza_actual, intervalo_manual):
    if model is None: return "IA_OFFLINE", 0.0
    try:
        ratio = km_pieza_actual / (intervalo_manual + 1e-6)
        diff = km_pieza_actual - intervalo_manual
        vec = scaler.transform(np.array([[km_pieza_actual, intervalo_manual, ratio, diff]]))
        pred = model.predict(vec, verbose=0)
        return encoder.inverse_transform([np.argmax(pred)])[0], float(np.max(pred))
    except: return "ERROR", 0.0

# --- LÓGICA ESTRICTA V6 ---
def analizar_mantenimiento(perfil_moto_id, km_moto_total, historial_usuario):
    modelo_real = buscar_modelo_real(perfil_moto_id)
    if not modelo_real: return []
    
    tareas = datos_motos[modelo_real]["tareas_mantenimiento"]
    resultados = []

    for tarea in tareas:
        comp_id = tarea["componente_id"]
        intervalo_obj = tarea["intervalo"]
        
        intervalo_std = intervalo_obj.get("kilometros", 5000)
        intervalos_unicos = sorted(intervalo_obj.get("unicos", []))
        
        # 1. Determinar el "Estado Actual" según el Historial
        # Buscamos cuál fue el último km registrado para esta pieza (0 si nunca se tocó)
        km_ultimo_cambio = historial_usuario.get(comp_id, 0)
        
        intervalo_activo = intervalo_std # Por defecto (si superamos los únicos)
        
        # 2. Revisión Secuencial de Hitos (Despegue)
        # Recorremos los hitos únicos (500, 2500...) para ver si ya se cumplieron
        todos_unicos_cumplidos = True
        
        for km_unico in intervalos_unicos:
            # CRITERIO DE CUMPLIMIENTO:
            # Se considera cumplido si el último cambio se hizo cerca o después del hito.
            # Margen de "adelanto" permitido: 10% (ej. cambiar a los 450 cuenta para el de 500)
            margen_adelanto = km_unico * 0.90
            
            if km_ultimo_cambio < margen_adelanto:
                # No hemos superado este hito con un cambio registrado.
                # ESTE es nuestro objetivo actual. Nos quedamos aquí atrapados hasta que se haga.
                intervalo_activo = km_unico
                todos_unicos_cumplidos = False
                break # Rompemos el ciclo, no miramos hitos futuros
        
        # 3. Cálculo de Uso
        origen_dato = "teorico"
        km_recorridos_pieza = 0
        
        if not todos_unicos_cumplidos:
            # Estamos persiguiendo un hito único (ej. 500 km)
            # El uso es absoluto desde el km 0 de la moto (o desde el último cambio si hubo uno fallido intermedio)
            # Simplificación robusta: Uso = ODO actual (para despegue inicial)
            # Pero si ya hubo un cambio previo (ej. al km 100), uso = ODO - 100.
            # Lo más seguro para despegue es comparar contra el ODO absoluto si es el primer hito.
            
            if intervalo_activo == intervalos_unicos[0] and km_ultimo_cambio == 0:
                km_recorridos_pieza = km_moto_total # Uso desde fábrica
                origen_dato = f"pendiente_despegue_{intervalo_activo}km"
            else:
                # Estamos en un hito intermedio (ej. ya pasé el 500, voy por el 2500)
                km_recorridos_pieza = max(0, km_moto_total - km_ultimo_cambio)
                origen_dato = f"pendiente_hito_{intervalo_activo}km"
                
        else:
            # Ya pasamos el despegue, estamos en régimen RECURRENTE (cada 5000 km)
            km_recorridos_pieza = max(0, km_moto_total - km_ultimo_cambio)
            origen_dato = "ciclo_recurrente_normal"
            intervalo_activo = intervalo_std

        # 4. Consultar IA
        estado_ia, conf_ia = consultar_ia_robusta(km_recorridos_pieza, intervalo_activo)
        urgencia = km_recorridos_pieza / intervalo_activo

        resultados.append({
            "componente": tarea["componente_nombre_comun"],
            "componente_id": comp_id,
            "accion": tarea["accion"],
            "datos_tecnicos": {
                "km_pieza_actual": int(km_recorridos_pieza),
                "intervalo_fabricante": intervalo_activo,
                "origen": origen_dato,
                "porcentaje_uso": round(urgencia * 100, 1)
            },
            "analisis_ia": { "diagnostico": estado_ia, "confianza": round(conf_ia * 100, 1) }
        })

    return sorted(resultados, key=lambda x: x['datos_tecnicos']['porcentaje_uso'], reverse=True)

# --- ENDPOINTS (SIN CAMBIOS) ---
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == AUTH_USERNAME and auth.password == AUTH_PASSWORD:
            return f(*args, **kwargs)
        return make_response('Login', 401, {'WWW-Authenticate': 'Basic'})
    return decorated

@app.route('/get_maintenance_options', methods=['GET'])
def get_maintenance_options():
    input_mid = request.args.get('modelo_id')
    real_mid = buscar_modelo_real(input_mid)
    
    if not real_mid:
        return jsonify([{"id": "aceite_motor", "label": "Aceite de Motor (Genérico)"}])

    tareas = datos_motos[real_mid].get("tareas_mantenimiento", [])
    seen = set()
    opts = []
    for t in tareas:
        if t['componente_id'] not in seen:
            opts.append({"id": t['componente_id'], "label": t['componente_nombre_comun']})
            seen.add(t['componente_id'])
    opts.append({"id": "otro", "label": "Otro / Reparación General"})
    return jsonify(opts)

@app.route('/predict_full', methods=['POST'])
@auth_required
def predict_full():
    d = request.get_json(force=True)
    return jsonify({"diagnostico_global": analizar_mantenimiento(d.get('modelo_id'), float(d.get('km_actual')), d.get('historial_usuario', {}))})

@app.route('/reportar_mantenimiento', methods=['POST'])
@auth_required
def reportar():
    d = request.get_json(force=True, silent=True)
    if d:
        d.update({"fecha_reporte": now_iso(), "fecha_servidor": now_iso()})
        os.makedirs(os.path.dirname(ARCHIVO_ENTRENAMIENTO), exist_ok=True)
        with open(ARCHIVO_ENTRENAMIENTO, 'a') as f: f.write(json.dumps(d) + "\n")
    return jsonify({"status": "saved"}), 201

@app.route('/actualizar_kilometraje', methods=['POST'])
@auth_required
def actualizar_km():
    d = request.get_json(force=True, silent=True)
    if d:
        d.update({"accion_realizada": "ACTUALIZACION_KM", "fecha_reporte": now_iso(), "fecha_servidor": now_iso()})
        os.makedirs(os.path.dirname(ARCHIVO_ENTRENAMIENTO), exist_ok=True)
        with open(ARCHIVO_ENTRENAMIENTO, 'a') as f: f.write(json.dumps(d) + "\n")
    return jsonify({"status": "saved"}), 201

@app.route('/', methods=['GET'])
def home():
    return f"API V6 (Strict Sequential) - IA: {'🟢' if model else '🔴'}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)