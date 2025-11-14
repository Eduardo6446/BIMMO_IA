# -*- coding: utf-8 -*-
"""
Este script es la versión 4 del proyecto.
Convierte nuestro "Sistema Experto" (v3) en una API web usando Flask.
Este es el "backend" que la aplicación móvil consumirá.

Autor: Tu Nombre/Nombre del Proyecto
Fecha: 20/10/2025

---
Para ejecutarlo localmente:
1. Asegúrate de tener Flask: pip install Flask
2. Ejecuta el script: python app_api_flask.py
3. El servidor estará corriendo en http://127.0.0.1:5000
---
"""

from flask import Flask, request, jsonify
import json

# PASO 1: Crear la aplicación Flask
app = Flask(__name__)

# PASO 2: Base de Conocimiento Completa (Todos los JSON recolectados)
# (Esta es la misma base de datos de mantenimiento_motos_ia_v3.py)
datos_motos = {
    # --- MODELOS ESPECÍFICOS ---
    "Bajaj_Pulsar_NS200": {
      "info_moto": { "marca": "Bajaj", "modelo": "Pulsar NS200" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor y Tamiz", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 5000 } },
        { "componente_id": "filtro_aceite", "componente_nombre_comun": "Filtro de Aceite (Papel)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 10000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 15000 } },
        { "componente_id": "bujias", "componente_nombre_comun": "Bujías (3)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 10000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } }
      ]
    },
    "Bajaj_Pulsar_NS160": {
      "info_moto": { "marca": "Bajaj", "modelo": "Pulsar NS160" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 5000 } },
        { "componente_id": "tamiz_aceite", "componente_nombre_comun": "Tamiz / Cedazo de Aceite", "accion": "LIMPIAR", "intervalo": { "kilometros": 5000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire", "accion": "LIMPIAR", "intervalo": { "kilometros": 5000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 15000 } },
        { "componente_id": "bujias", "componente_nombre_comun": "Bujías", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 5000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 750 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 5000 } },
        { "componente_id": "liquido_frenos", "componente_nombre_comun": "Líquido de Frenos", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 5000 } }
      ]
    },
    "Genesis_HJ-125_RK125": {
      "info_moto": { "marca": "Genesis", "modelo": "HJ-125 (conocida como RK125)" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "tamiz_aceite", "componente_nombre_comun": "Tamiz / Cedazo de Aceite", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Espuma)", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "zapatas_freno_trasero", "componente_nombre_comun": "Zapatas de Freno Trasero (Tambor)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "carburador", "componente_nombre_comun": "Carburador", "accion": "LIMPIAR", "intervalo": { "kilometros": 10000 } }
      ]
    },
    "Keeway_RKS_125": {
      "info_moto": { "marca": "Keeway", "modelo": "RKS 125" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "tamiz_aceite", "componente_nombre_comun": "Tamiz / Cedazo de Aceite", "accion": "LIMPIAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Espuma)", "accion": "LIMPIAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "liquido_frenos", "componente_nombre_comun": "Líquido de Frenos (Delantero)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "zapatas_freno_trasero", "componente_nombre_comun": "Zapatas de Freno Trasero (Tambor)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } }
      ]
    },
    "Hero_Eco_150": {
      "info_moto": { "marca": "Hero", "modelo": "Eco 150" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "tamiz_aceite", "componente_nombre_comun": "Tamiz / Cedazo de Aceite", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Espuma)", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "zapatas_freno_delantero", "componente_nombre_comun": "Zapatas de Freno Delantero (Tambor)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "zapatas_freno_trasero", "componente_nombre_comun": "Zapatas de Freno Trasero (Tambor)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 5000 } }
      ]
    },
    "Hero_Hunk_150_SD": {
      "info_moto": { "marca": "Hero", "modelo": "Hunk 150 SD" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "tamiz_aceite", "componente_nombre_comun": "Tamiz / Cedazo de Aceite", "accion": "LIMPIAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Viscoso/Papel)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 12000 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 12000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "pastillas_freno_delantero", "componente_nombre_comun": "Pastillas de Freno Delantero (Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "liquido_frenos", "componente_nombre_comun": "Líquido de Frenos (Delantero)", "accion": "REEMPLAZAR", "intervalo": { "meses": 24 } },
        { "componente_id": "zapatas_freno_trasero", "componente_nombre_comun": "Zapatas de Freno Trasero (Tambor)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 3000 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 6000 } }
      ]
    },
    "Hero_Hunk_160R": {
      "info_moto": { "marca": "Hero", "modelo": "Hunk 160R" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 750 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "filtro_aceite", "componente_nombre_comun": "Filtro de Aceite", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 8000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Papel)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 15000 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 12000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 700 } },
        { "componente_id": "pastillas_freno_delantero", "componente_nombre_comun": "Pastillas de Freno Delantero (Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "pastillas_freno_trasero", "componente_nombre_comun": "Pastillas de Freno Trasero (Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "liquido_frenos", "componente_nombre_comun": "Líquido de Frenos", "accion": "REEMPLAZAR", "intervalo": { "meses": 24 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } }
      ]
    },
    "Hero_Hunk_160R_4V": {
      "info_moto": { "marca": "Hero", "modelo": "Hunk 160R 4V" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 750 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "filtro_aceite", "componente_nombre_comun": "Filtro de Aceite", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 8000 } },
        { "componente_id": "radiador_aceite", "componente_nombre_comun": "Radiador de Aceite", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Papel)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 15000 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 12000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 700 } },
        { "componente_id": "pastillas_freno_delantero", "componente_nombre_comun": "Pastillas de Freno Delantero (Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "pastillas_freno_trasero", "componente_nombre_comun": "Pastillas de Freno Trasero (Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } },
        { "componente_id": "liquido_frenos", "componente_nombre_comun": "Líquido de Frenos", "accion": "REEMPLAZAR", "intervalo": { "meses": 24 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas (4V)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 4000 } }
      ]
    },
    "Genesis_KA_150": {
      "info_moto": { "marca": "Genesis", "modelo": "KA 150" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "tamiz_aceite", "componente_nombre_comun": "Tamiz / Cedazo de Aceite", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Espuma)", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 10000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "pastillas_freno_delantero", "componente_nombre_comun": "Pastillas de Freno Delantero (Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "liquido_frenos", "componente_nombre_comun": "Líquido de Frenos (Delantero)", "accion": "REEMPLAZAR", "intervalo": { "meses": 24 } },
        { "componente_id": "zapatas_freno_trasero", "componente_nombre_comun": "Zapatas de Freno Trasero (Tambor)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "ajuste_valvulas", "componente_nombre_comun": "Holgura de Válvulas", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 5000 } }
      ]
    },
    
    # --- PERFILES GENÉRICOS ---
    "Generica_Trabajo_150cc": {
      "info_moto": { "marca": "Genérica", "modelo": "Moto de Trabajo 125-150cc (Carburada)" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 2500 }, "notas_tecnicas": "Recomendación general. Consulta tu manual." },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Espuma)", "accion": "LIMPIAR", "intervalo": { "kilometros": 2500 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 8000 } },
        { "componente_id": "kit_arrastre", "componente_nombre_comun": "Cadena de Transmisión", "accion": "LUBRICAR", "intervalo": { "kilometros": 500 } },
        { "componente_id": "frenos", "componente_nombre_comun": "Frenos (Tambor/Disco)", "accion": "INSPECCIONAR", "intervalo": { "kilometros": 2500 } }
      ]
    },
    "Generica_Urbana_250cc": {
      "info_moto": { "marca": "Genérica", "modelo": "Moto Urbana 160-250cc (Inyectada)" },
      "tareas_mantenimiento": [
        { "componente_id": "aceite_motor", "componente_nombre_comun": "Aceite del Motor", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 4000 }, "notas_tecnicas": "Recomendación general. Consulta tu manual." },
        { "componente_id": "filtro_aceite", "componente_nombre_comun": "Filtro de Aceite", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 8000 } },
        { "componente_id": "filtro_aire", "componente_nombre_comun": "Filtro de Aire (Papel)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 12000 } },
        { "componente_id": "bujia", "componente_nombre_comun": "Bujía (Iridio/Cobre)", "accion": "REEMPLAZAR", "intervalo": { "kilometros": 12000 } },
      ]
    }
}


# PASO 3: Lógica del Sistema Experto (Nuestras funciones)
# (Estas funciones son copiadas de mantenimiento_motos_ia_v3.py)

def seleccionar_perfil_moto(modelo_buscado, cilindrada):
    """
    Busca un modelo específico y, si no lo encuentra, retorna un perfil genérico
    basado en la cilindrada.
    """
    if modelo_buscado in datos_motos:
        return modelo_buscado
    else:
        if cilindrada <= 150:
            return "Generica_Trabajo_150cc"
        else:
            return "Generica_Urbana_250cc"

def calcular_probabilidad_mantenimiento(perfil_moto, kilometraje_actual):
    """
    Calcula la probabilidad o "Índice de Urgencia" de mantenimiento para
    el perfil de moto seleccionado.
    """
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
                "probabilidad": round(probabilidad, 2)
            })

    return sorted(resultados, key=lambda x: x["probabilidad"], reverse=True)

# PASO 4: Crear el Endpoint (la "ruta" de la API)
@app.route('/predict', methods=['POST'])
def predict_maintenance():
    """
    Esta es la función que se ejecuta cuando la app móvil llama a nuestra API.
    Espera recibir un JSON con:
    {
        "modelo_id": "Bajaj_Pulsar_NS200",
        "cilindrada": 200,
        "km_actual": 9850
    }
    """
    try:
        # 1. Obtener los datos de la solicitud
        data = request.get_json()
        
        modelo_id = data.get('modelo_id')
        cilindrada = data.get('cilindrada')
        km_actual = data.get('km_actual')

        # 2. Validar los datos de entrada
        if not all([modelo_id, cilindrada, km_actual is not None]):
            return jsonify({"error": "Faltan datos requeridos: modelo_id, cilindrada, km_actual"}), 400
        
        # 3. Ejecutar nuestra lógica
        perfil_seleccionado = seleccionar_perfil_moto(modelo_id, int(cilindrada))
        recomendaciones = calcular_probabilidad_mantenimiento(perfil_seleccionado, int(km_actual))
        
        # 4. Devolver la respuesta
        info_moto_usada = datos_motos[perfil_seleccionado]['info_moto']

        return jsonify({
            "perfil_usado": perfil_seleccionado,
            "info_perfil": info_moto_usada,
            "km_analizado": km_actual,
            "recomendaciones": recomendaciones
        }), 200

    except Exception as e:
        # Capturar cualquier error inesperado
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# PASO 5: Correr el servidor
if __name__ == '__main__':
    # El host '0.0.0.0' hace que el servidor sea accesible en tu red local
    app.run(host='0.0.0.0', port=5000, debug=True)