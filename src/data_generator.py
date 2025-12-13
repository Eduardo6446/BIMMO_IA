# -*- coding: utf-8 -*-
"""
Script Generador de Datos Sintéticos V6 (Estrategia Balanceada).
Mejora CRÍTICA: Elimina la simulación de perfiles de usuario que causaba
un desbalance de clases (75% normal). Ahora fuerza una distribución
perfecta (25% por clase) para que la IA aprenda a distinguir los casos raros.
"""

import json
import random
import uuid
import os
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
CANTIDAD_REGISTROS = 50000 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_SALIDA = os.path.join(BASE_DIR, '../data/datos_entrenamiento_fase5.jsonl')
ARCHIVO_BASE_CONOCIMIENTO = os.path.join(BASE_DIR, '../data/base.json')

def cargar_base_conocimiento():
    print(ARCHIVO_BASE_CONOCIMIENTO)
    try:
        with open(ARCHIVO_BASE_CONOCIMIENTO, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        try:
            with open('../data/base.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            print(f"❌ Error: No se encontró base_conocimiento.json")
            exit()

def generar_fecha_aleatoria():
    return datetime.now().isoformat()

def simular_reporte_balanceado(moto_key, moto_data, usuario_id):
    tareas = moto_data.get("tareas_mantenimiento", [])
    if not tareas: return None
    
    # 1. Agrupar tareas por componente
    tareas_por_comp = {}
    for t in tareas:
        comp_id = t["componente_id"]
        intervalo = t["intervalo"].get("kilometros")
        if intervalo:
            if comp_id not in tareas_por_comp:
                tareas_por_comp[comp_id] = []
            tareas_por_comp[comp_id].append(t)
    
    if not tareas_por_comp: return None

    # 2. Elegir componente y filtrar intervalo mayor (Fix Despegue)
    comp_elegido = random.choice(list(tareas_por_comp.keys()))
    posibles_tareas = tareas_por_comp[comp_elegido]
    tarea = max(posibles_tareas, key=lambda x: x["intervalo"]["kilometros"])
    intervalo_base = tarea["intervalo"]["kilometros"]
    
    # 3. Generar Ciclos (1 a 8 cambios)
    ciclo = random.randint(1, 8)
    
    # --- CAMBIO V6: INGENIERÍA INVERSA DESDE LA ETIQUETA ---
    # En lugar de simular un usuario y ver qué pasa, elegimos qué queremos enseñar
    # y generamos los datos matemáticos para que cuadren.
    
    clases_posibles = ["como_nuevo", "desgaste_normal", "muy_desgastado", "fallo_critico"]
    condicion_objetivo = random.choice(clases_posibles)
    
    # Definimos el ratio exacto según la clase que queremos forzar
    if condicion_objetivo == "como_nuevo":
        # Ratios bajos (ej. acaba de cambiarlo hace poco)
        ratio = random.uniform(0.10, 0.90)
        
    elif condicion_objetivo == "desgaste_normal":
        # Ratios ideales
        ratio = random.uniform(0.91, 1.10)
        
    elif condicion_objetivo == "muy_desgastado":
        # Se pasó un poco
        ratio = random.uniform(1.11, 1.30)
        
    else: # fallo_critico
        # Se pasó bastante (hasta el doble del intervalo a veces)
        ratio = random.uniform(1.31, 2.00)

    # 4. Calcular Kilometraje Real Matemáticamente
    # Formula: (Ciclos Completos * Intervalo) + (Fracción del Ciclo Actual * Intervalo)
    km_realizado = int((intervalo_base * (ciclo - 1)) + (intervalo_base * ratio))
    
    # El "recomendado" siempre es el final del ciclo actual
    km_objetivo = intervalo_base * ciclo

    return {
        "fecha_reporte": generar_fecha_aleatoria(),
        "usuario_id_hash": usuario_id,
        "modelo_id": moto_key,
        "componente_id": tarea["componente_id"],
        "accion_realizada": tarea["accion"],
        "km_recomendacion_app": km_objetivo,
        "km_realizado_usuario": km_realizado,
        "condicion_reportada": condicion_objetivo, # Etiqueta perfectamente alineada
        "fecha_servidor": datetime.now().isoformat()
    }

def main():
    print("--- GENERADOR V6: BALANCEO DE CLASES PERFECTO ---")
    print("Generando dataset diseñado para romper el estancamiento del 75%...")
    
    datos = cargar_base_conocimiento()
    keys = list(datos.keys())
    usuarios = [uuid.uuid4().hex[:8] for _ in range(500)]
    
    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)
    
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        conteo_clases = {"como_nuevo": 0, "desgaste_normal": 0, "muy_desgastado": 0, "fallo_critico": 0}
        
        for i in range(CANTIDAD_REGISTROS):
            key = random.choice(keys)
            reporte = simular_reporte_balanceado(key, datos[key], random.choice(usuarios))
            if reporte:
                conteo_clases[reporte["condicion_reportada"]] += 1
                f.write(json.dumps(reporte) + "\n")
            if (i+1) % 5000 == 0: print(f"   -> {i+1} registros...")

    print(f"✅ Listo: {ARCHIVO_SALIDA}")
    print("📊 Distribución generada (debería ser ~25% c/u):")
    for k, v in conteo_clases.items():
        pct = (v / CANTIDAD_REGISTROS) * 100
        print(f"   - {k}: {v} ({pct:.1f}%)")

if __name__ == "__main__":
    main()