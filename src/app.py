# -*- coding: utf-8 -*-
"""
SERVIDOR FINAL (FASE 4 - V2): CEREBRO MATEMÁTICO
Actualizado para consumir el modelo 'modelo_desgaste_v2.h5'.
Cambio principal: La IA ya no usa IDs, usa FISICA (Km vs Intervalo).
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import json
import os
import numpy as np
import tensorflow as tf
import pickle # IMPORTANTE: Usamos pickle para los nuevos transformadores
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
ARCHIVO_ENTRENAMIENTO = ARCHIVO_HISTORIAL # Alias para claridad

# --- CARGAR IA (EL NUEVO CEREBRO) ---
print("\n⏳ Cargando Nueva IA Robusta (V2)...\n")

try:
    # 1. Cargar el modelo neuronal (.h5)
    path_model = os.path.join(DIR_MODELOS, 'modelo_desgaste_v2.h5')
    model = tf.keras.models.load_model(path_model)
    
    # 2. Cargar el Scaler (.pkl) - VITAL para que la IA entienda los números
    path_scaler = os.path.join(DIR_MODELOS, 'scaler.pkl')
    with open(path_scaler, 'rb') as f:
        scaler = pickle.load(f)
        
    # 3. Cargar el Encoder (.pkl) - VITAL para traducir la respuesta
    path_encoder = os.path.join(DIR_MODELOS, 'encoder.pkl')
    with open(path_encoder, 'rb') as f:
        encoder = pickle.load(f)
        
    print(f"✅ SISTEMA OPERATIVO: Modelo cargado desde {path_model}")
    
except Exception as e:
    print(f"\n⚠️ ERROR CRÍTICO: No se cargó la IA ({e}).\nRevisa que ejecutaste train_model.py primero.")
    model = None
    scaler = None
    encoder = None

# --- CARGAR BASE DE CONOCIMIENTO (MANUALES) ---
def cargar_base_conocimiento():
    if not os.path.exists(ARCHIVO_BASE): return {}
    with open(ARCHIVO_BASE, 'r', encoding='utf-8') as f:
        return json.load(f)

datos_motos = cargar_base_conocimiento()

# --- NUEVA LÓGICA DE PREDICCIÓN (MATEMÁTICA) ---

def consultar_ia_robusta(km_pieza_actual, intervalo_manual):
    """
    Prepara los datos EXACTAMENTE como se hizo en el entrenamiento.
    Features esperados: [km_realizado, km_recomendado, ratio, diferencia]
    """
    if model is None or scaler is None: return "IA_OFFLINE", 0.0
    
    try:
        # 1. Ingeniería de Características (Feature Engineering) en tiempo real
        # Calculamos los mismos valores derivados que usamos al entrenar
        epsilon = 1e-6
        ratio = km_pieza_actual / (intervalo_manual + epsilon)
        diff = km_pieza_actual - intervalo_manual
        
        # 2. Construir el vector de entrada (4 valores)
        # OJO: El orden debe ser IDÉNTICO a train_model.py
        # features = ['km_realizado_usuario', 'km_recomendacion_app', 'ratio_uso', 'diferencia_km']
        vector_crudo = np.array([[
            km_pieza_actual,
            intervalo_manual,
            ratio,
            diff
        ]])
        
        # 3. Escalar (Traducir a lenguaje IA)
        vector_scaled = scaler.transform(vector_crudo)
        
        # 4. Predecir
        prediccion = model.predict(vector_scaled, verbose=0)
        
        # 5. Interpretar
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
    """
    if perfil_moto_id not in datos_motos: return []
    
    tareas = datos_motos[perfil_moto_id]["tareas_mantenimiento"]
    resultados = []

    for tarea in tareas:
        comp_id = tarea["componente_id"]
        intervalo_manual = tarea["intervalo"].get("kilometros")
        
        if not intervalo_manual: continue # Ignorar tareas sin KM definido
        
        # A. DETERMINAR EL ESTADO REAL DE LA PIEZA
        origen_dato = "teorico"
        km_recorridos_pieza = 0
        
        if comp_id in historial_usuario:
            # Opción 1: Tenemos historial real
            km_ultimo_cambio = historial_usuario[comp_id]
            km_recorridos_pieza = km_moto_total - km_ultimo_cambio
            origen_dato = "historial_real"
        else:
            # Opción 2: Cálculo teórico (asumimos mantenimientos perfectos previos)
            km_recorridos_pieza = km_moto_total % intervalo_manual
            # Corrección: Si el modulo es 0 pero la moto tiene km, la pieza tiene el intervalo completo
            if km_recorridos_pieza == 0 and km_moto_total > 0:
                km_recorridos_pieza = intervalo_manual
        
        # Evitar negativos por errores de usuario
        km_recorridos_pieza = max(0, km_recorridos_pieza)

        # B. CONSULTAR A LA NUEVA IA
        # Ahora le pasamos (KM Real vs Intervalo Manual)
        estado_ia, confianza_ia = consultar_ia_robusta(km_recorridos_pieza, intervalo_manual)
        
        # C. CÁLCULO DE URGENCIA MANUAL (Para comparar/ordenar)
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

    # Ordenar por gravedad (primero lo que la IA dice que es crítico)
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
    """
    Endpoint principal: Recibe estado de la moto y devuelve análisis completo de TODAS las piezas.
    """
    try:
        data = request.get_json(force=True)
        modelo_id = data.get('modelo_id')
        km_actual = data.get('km_actual')
        
        # Historial opcional: { "aceite": 10500, "frenos": 12000 }
        historial = data.get('historial_usuario', {}) 
        
        if not modelo_id or km_actual is None:
            return jsonify({"error": "Faltan datos (modelo_id, km_actual)"}), 400

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
    """
    Para pruebas rápidas: ¿Cómo ve la IA una pieza específica?
    """
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
    return f"Servidor de Mantenimiento Inteligente V2<br>Estado IA: {estado_ia}"


@app.route('/get_maintenance_options', methods=['GET'])
#@auth_required  <-- Podemos dejarlo abierto o protegido, usaremos auth por consistencia
def get_maintenance_options():
    """
    Devuelve la lista de componentes válidos para un modelo específico.
    Usado para llenar el <select> del frontend.
    """
    modelo_id = request.args.get('modelo_id')
    
    if not modelo_id or modelo_id not in datos_motos:
        # Fallback genérico si no encontramos el modelo exacto
        return jsonify([
            {"id": "aceite_motor", "label": "Aceite de Motor (Genérico)"},
            {"id": "frenos", "label": "Frenos (Genérico)"},
            {"id": "cadena", "label": "Cadena (Genérico)"},
            {"id": "neumaticos", "label": "Neumáticos (Genérico)"}
        ])

    tareas = datos_motos[modelo_id].get("tareas_mantenimiento", [])
    
    # Deduplicación: Si hay 'aceite' a los 500km y 'aceite' a los 5000km, solo queremos una opción en el menú
    opciones_unicas = {}
    
    for t in tareas:
        cid = t['componente_id']
        label = t['componente_nombre_comun']
        
        # Guardamos en diccionario para sobreescribir duplicados (mismo ID)
        # Preferimos el nombre más corto o genérico si varía, pero aquí tomamos el último.
        if cid not in opciones_unicas:
            opciones_unicas[cid] = label
    
    # Convertir a lista de objetos para el JSON
    lista_final = [{"id": k, "label": v} for k, v in opciones_unicas.items()]
    
    # Añadir siempre una opción de "Otro"
    lista_final.append({"id": "otro_mantenimiento", "label": "Otro / Reparación General"})
    
    return jsonify(lista_final)

@app.route('/reportar_mantenimiento', methods=['POST'])
@auth_required
def reportar():
    """
    Recibe el reporte del usuario y lo guarda para re-entrenar la IA.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data: return jsonify({"error": "JSON vacío"}), 400

        # 1. Extraer datos del request
        usuario_id_hash = data.get('usuario_id_hash')
        modelo_id = data.get('modelo_id')
        componente_id = data.get('componente_id')
        accion_realizada = data.get('accion_realizada', 'REEMPLAZAR')
        km_realizado = data.get('km_realizado_usuario')
        condicion_reportada = data.get('condicion_reportada')

        # 2. Calcular KM Recomendado (Lógica de Negocio)
        # Necesitamos saber cuál era el intervalo teórico para guardarlo como referencia
        km_teorico = 0
        if modelo_id in datos_motos:
            tareas = datos_motos[modelo_id].get('tareas_mantenimiento', [])
            tarea = next((t for t in tareas if t['componente_id'] == componente_id), None)
            
            if tarea and 'intervalo' in tarea:
                intervalo = tarea['intervalo'].get('kilometros', 0)
                if intervalo > 0 and km_realizado:
                    # Estimamos cuántos ciclos completos llevaba
                    ciclo = round(km_realizado / intervalo)
                    if ciclo < 1: ciclo = 1
                    km_teorico = intervalo * ciclo

        # 3. Construir registro para el dataset
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

        # 4. Guardar en disco (JSONL)
        os.makedirs(os.path.dirname(ARCHIVO_ENTRENAMIENTO), exist_ok=True)
        with open(ARCHIVO_ENTRENAMIENTO, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro_ordenado) + "\n")
            
        print(f"💾 Reporte guardado: {modelo_id} - {componente_id} ({condicion_reportada})")
        return jsonify({"status": "saved", "enriched_data": registro_ordenado}), 201

    except Exception as e:
        print(f"Error guardando reporte: {e}")
        return jsonify({"error": str(e)}), 500
    
def now_iso():
    return datetime.now().isoformat()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)