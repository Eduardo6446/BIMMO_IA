# -*- coding: utf-8 -*-
"""
Script Generador de Datos Sintéticos V3 (MODO FÁCIL / DEMO).
Este script genera 20,000 registros con reglas MATEMÁTICAS ESTRICTAS.
Elimina la ambigüedad para que la IA pueda aprender fácilmente y alcanzar >90% de precisión.

Uso:
1. Asegúrate de tener 'base_conocimiento.json' en la misma carpeta.
2. Ejecuta: python generador_datos_ficticios.py
"""

import json
import random
import uuid
import os
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
CANTIDAD_REGISTROS = 20000 
ARCHIVO_SALIDA = 'datos_entrenamiento_fase2.jsonl'
ARCHIVO_BASE_CONOCIMIENTO = 'base_conocimiento.json'

def cargar_base_conocimiento():
    """Carga el archivo JSON de las motos."""
    try:
        with open(ARCHIVO_BASE_CONOCIMIENTO, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró {ARCHIVO_BASE_CONOCIMIENTO}.")
        exit()

def generar_fecha_aleatoria():
    """Genera fecha reciente."""
    return datetime.now().isoformat()

def simular_reporte_demo(moto_key, moto_data, usuario_id):
    """Genera un reporte con lógica determinista (sin azar en la etiqueta)."""
    tareas = moto_data.get("tareas_mantenimiento", [])
    if not tareas: return None
    
    tarea = random.choice(tareas)
    intervalo = tarea["intervalo"].get("kilometros")
    
    # Solo simulamos tareas basadas en kilometraje
    if not intervalo: return None

    # --- LÓGICA V3: REGLAS ESTRICTAS ---
    # Generamos una variación amplia de uso (desde -50% hasta +100%)
    variacion = random.uniform(-0.50, 1.0) 
    
    ciclo = random.randint(1, 2) # 1er o 2do cambio
    km_objetivo = intervalo * ciclo
    km_realizado = int(km_objetivo * (1 + variacion))
    
    # Calculamos el Ratio (Qué tanto cumplió el usuario)
    ratio = km_realizado / km_objetivo
    
    # --- REGLAS DURAS (Cero confusión para la IA) ---
    # Esto facilita enormemente que la IA encuentre las fronteras exactas.
    
    if ratio <= 0.90:
        # Si lo cambia antes del 90% del tiempo -> COMO NUEVO
        condicion = "como_nuevo"
        
    elif 0.90 < ratio <= 1.10:
        # Si lo cambia en el tiempo correcto (+/- 10%) -> NORMAL
        condicion = "desgaste_normal"
        
    elif 1.10 < ratio <= 1.30:
        # Si se pasa hasta un 30% -> MUY DESGASTADO
        condicion = "muy_desgastado"
        
    else: # ratio > 1.30
        # Si se pasa más del 30% -> FALLO CRÍTICO
        condicion = "fallo_critico"

    return {
        "fecha_reporte": generar_fecha_aleatoria(),
        "usuario_id_hash": usuario_id,
        "modelo_id": moto_key,
        "componente_id": tarea["componente_id"],
        "accion_realizada": tarea["accion"],
        "km_recomendacion_app": km_objetivo,
        "km_realizado_usuario": km_realizado,
        "condicion_reportada": condicion,
        "fecha_servidor": datetime.now().isoformat()
    }

def main():
    print("--- INICIANDO GENERADOR V3 (MODO DEMO) ---")
    datos_motos = cargar_base_conocimiento()
    keys_motos = list(datos_motos.keys())
    
    # Simulamos 200 usuarios
    usuarios_ficticios = [uuid.uuid4().hex[:10] for _ in range(200)]
    
    print(f"🚀 Generando {CANTIDAD_REGISTROS} registros claros...")
    
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        for i in range(CANTIDAD_REGISTROS):
            moto_key = random.choice(keys_motos)
            usuario = random.choice(usuarios_ficticios)
            
            reporte = simular_reporte_demo(moto_key, datos_motos[moto_key], usuario)
            
            if reporte:
                f.write(json.dumps(reporte) + "\n")
            
            if (i+1) % 5000 == 0:
                print(f"   -> {i+1} generados...")

    print(f"\n✅ ¡LISTO! Archivo '{ARCHIVO_SALIDA}' generado.")
    print("   Súbelo a Colab (borra el viejo primero) y vuelve a entrenar.")

if __name__ == "__main__":
    main()