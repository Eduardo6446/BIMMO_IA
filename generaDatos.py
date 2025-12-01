# -*- coding: utf-8 -*-
"""
Script Generador de Datos Sintéticos para Fase 3.
Genera un archivo .jsonl con miles de reportes de mantenimiento simulados
pero con lógica realista basada en los intervalos del fabricante.

Uso:
1. Asegúrate de tener 'base_conocimiento.json' en la misma carpeta.
2. Ejecuta: python generaDatos.py
"""

import json
import random
import uuid
from datetime import datetime, timedelta

# Configuración
CANTIDAD_REGISTROS = 15000  # ¡Cambia esto si quieres más datos!
ARCHIVO_SALIDA = 'datos_entrenamiento_fase2.jsonl'
ARCHIVO_BASE_CONOCIMIENTO = 'base.json'

# Posibles condiciones reportadas por el usuario
CONDICIONES = ["como_nuevo", "desgaste_normal", "muy_desgastado", "fallo_critico"]

def cargar_base_conocimiento():
    try:
        with open(ARCHIVO_BASE_CONOCIMIENTO, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró {ARCHIVO_BASE_CONOCIMIENTO}. Asegúrate de haberlo creado en el paso anterior.")
        exit()

def generar_fecha_aleatoria():
    """Genera una fecha en el último año."""
    fin = datetime.now()
    inicio = fin - timedelta(days=365)
    random_seconds = random.randint(0, int((fin - inicio).total_seconds()))
    return (inicio + timedelta(seconds=random_seconds)).isoformat()

def simular_reporte(moto_key, moto_data, usuario_id):
    """Crea un reporte único basado en la lógica de la moto."""
    
    # 1. Elegir una tarea de mantenimiento al azar de esta moto
    tareas = moto_data.get("tareas_mantenimiento", [])
    if not tareas: return None
    
    tarea = random.choice(tareas)
    intervalo = tarea["intervalo"].get("kilometros")
    
    # Solo simulamos tareas basadas en KM
    if not intervalo: return None

    # 2. Simular el comportamiento del usuario
    # El usuario debería haberlo hecho al cumplir el intervalo (ej. 5000km)
    # Pero a veces lo hace antes (-10%) o después (+30%)
    variacion = random.uniform(-0.15, 0.40) 
    km_realizado = int(intervalo * (1 + variacion))
    
    # A veces el usuario reporta mantenimientos acumulados (ej. a los 10,000 en vez de 5,000)
    ciclo = random.randint(1, 4) # 1er cambio, 2do cambio, etc.
    km_objetivo_real = intervalo * ciclo
    km_realizado_total = int(km_objetivo_real * (1 + variacion))

    # 3. Determinar la condición lógica basada en el retraso
    # Si se pasó del kilometraje, es más probable que esté desgastado
    ratio = km_realizado_total / km_objetivo_real
    
    if ratio < 0.90:
        condicion = random.choices(["como_nuevo", "desgaste_normal"], weights=[0.7, 0.3])[0]
    elif 0.90 <= ratio <= 1.10:
        condicion = random.choices(["como_nuevo", "desgaste_normal", "muy_desgastado"], weights=[0.1, 0.8, 0.1])[0]
    elif 1.10 < ratio <= 1.40:
        condicion = random.choices(["desgaste_normal", "muy_desgastado"], weights=[0.3, 0.7])[0]
    else: # Se pasó por mucho (> 40%)
        condicion = random.choices(["muy_desgastado", "fallo_critico"], weights=[0.6, 0.4])[0]

    return {
        "fecha_reporte": generar_fecha_aleatoria(),
        "usuario_id_hash": usuario_id,
        "modelo_id": moto_key,
        "componente_id": tarea["componente_id"],
        "accion_realizada": tarea["accion"],
        "km_recomendacion_app": km_objetivo_real,
        "km_realizado_usuario": km_realizado_total,
        "condicion_reportada": condicion,
        "fecha_servidor": datetime.now().isoformat()
    }

def main():
    datos_motos = cargar_base_conocimiento()
    keys_motos = list(datos_motos.keys())
    
    # Generamos unos 500 usuarios ficticios
    usuarios_ficticios = [uuid.uuid4().hex[:10] for _ in range(500)]
    
    print(f"Generando {CANTIDAD_REGISTROS} registros sintéticos...")
    
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        for _ in range(CANTIDAD_REGISTROS):
            # Elegir moto y usuario al azar
            moto_key = random.choice(keys_motos)
            usuario = random.choice(usuarios_ficticios)
            
            reporte = simular_reporte(moto_key, datos_motos[moto_key], usuario)
            
            if reporte:
                f.write(json.dumps(reporte) + "\n")

    print(f"¡Listo! Archivo '{ARCHIVO_SALIDA}' generado con éxito.")

if __name__ == "__main__":
    main()