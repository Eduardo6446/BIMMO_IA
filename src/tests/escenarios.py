import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# CONFIGURACIÓN
URL_BASE = 'http://127.0.0.1:5000'
URL_PREDICT = f'{URL_BASE}/predict_full'
URL_OPTIONS = f'{URL_BASE}/get_maintenance_options'
AUTH = (os.getenv("AUTH_USERNAME", "admin"), os.getenv("AUTH_PASSWORD", "secret"))

def verificar_existencia_modelo(modelo_id):
    """
    Pregunta a la API si reconoce el modelo antes de intentar predecir.
    """
    try:
        resp = requests.get(URL_OPTIONS, params={'modelo_id': modelo_id}, timeout=2)
        if resp.status_code == 200:
            opciones = resp.json()
            # Si devuelve opciones genéricas (o solo 'otro'), es que no encontró la moto
            if len(opciones) <= 2 and opciones[0]['id'] in ['aceite_motor', 'gen']:
                # Verificamos si es el fallback
                if opciones[0]['label'].endswith("(Genérico)"):
                    return False
            return True
    except:
        return False
    return False

def imprimir_resultado(titulo, payload_enviado, data_recibida):
    print(f"\n--- {titulo} ---")
    
    if "error" in data_recibida:
        print(f"❌ ERROR API: {data_recibida['error']}")
        return

    nombre_moto = data_recibida.get('moto') or payload_enviado.get('modelo_id')
    km_moto = data_recibida.get('km_total') or payload_enviado.get('km_actual')

    print(f"🏍️  Moto: {nombre_moto} | ODO: {km_moto} km")
    
    diagnosticos = data_recibida.get("diagnostico_global", [])
    
    if not diagnosticos:
        print("   ⚠️  ALERTA: Lista vacía. El servidor no devolvió tareas.")
        
        # Diagnóstico de Nombres
        modelo_buscado = payload_enviado.get('modelo_id')
        existe = verificar_existencia_modelo(modelo_buscado)
        
        if not existe:
            print(f"   ❌ DIAGNÓSTICO: El modelo '{modelo_buscado}' NO EXISTE en 'base.json'.")
            print("      -> Revisa que el ID en el archivo JSON sea idéntico.")
            print("      -> Recuerda reiniciar el servidor (app.py) si editaste el archivo.")
        else:
            print("   ❓ DIAGNÓSTICO: El modelo existe pero no tiene tareas asignadas.")
        return

    # Filtramos para mostrar solo Aceite de Motor como referencia
    aceite = next((d for d in diagnosticos if "aceite" in d['componente_id'].lower()), None)
    
    if aceite:
        tec = aceite['datos_tecnicos']
        ia = aceite['analisis_ia']
        
        print(f"   🔧 Componente: {aceite['componente']}")
        print(f"   📊 Estado IA: {ia['diagnostico'].upper()} (Confianza: {ia['confianza']}%)")
        print(f"   📉 Uso Calculado: {tec['porcentaje_uso']}%")
        print(f"   🎯 Meta Actual: {tec['intervalo_fabricante']} km")
        print(f"   ℹ️  Origen Lógica: {tec['origen']}")
    else:
        print("   ✅ Datos recibidos correctamente (Aceite no encontrado en la lista, mostrando primer item):")
        if diagnosticos:
            primero = diagnosticos[0]
            print(f"   🔧 Componente: {primero['componente']}")
            print(f"   📊 Estado: {primero['analisis_ia']['diagnostico']}")

def correr_tests():
    print("🚀 INICIANDO PRUEBAS DE LÓGICA V6 (ESTRICTA + HÍBRIDA)\n")

    # ---------------------------------------------------------
    # CASO 1: DESPEGUE NORMAL (Genesis KA 150)
    # ---------------------------------------------------------
    payload_1 = {
        "modelo_id": "Genesis_KA_150",
        "km_actual": 450,
        "historial_usuario": {} 
    }
    try:
        resp = requests.post(URL_PREDICT, json=payload_1, auth=AUTH)
        imprimir_resultado("CASO 1: Despegue Normal (450/500km)", payload_1, resp.json())
    except Exception as e: print(f"Error Caso 1: {e}")

    # ---------------------------------------------------------
    # CASO 2: OLVIDO DE DESPEGUE (Genesis KA 150)
    # ---------------------------------------------------------
    payload_2 = {
        "modelo_id": "Genesis_KA_150",
        "km_actual": 1200,
        "historial_usuario": {} 
    }
    try:
        resp = requests.post(URL_PREDICT, json=payload_2, auth=AUTH)
        imprimir_resultado("CASO 2: Despegue Olvidado (1200/500km)", payload_2, resp.json())
    except Exception as e: print(f"Error Caso 2: {e}")

    # ---------------------------------------------------------
    # CASO 3: RUTINA NORMAL (Hero Hunk 160R 4V)
    # ---------------------------------------------------------
    payload_3 = {
        "modelo_id": "Hero_Hunk_160R_4V",
        "km_actual": 5000,
        "historial_usuario": {
            "aceite_motor": 2000 
        }
    }
    try:
        resp = requests.post(URL_PREDICT, json=payload_3, auth=AUTH)
        imprimir_resultado("CASO 3: Rutina con Historial", payload_3, resp.json())
    except Exception as e: print(f"Error Caso 3: {e}")

    # ---------------------------------------------------------
    # CASO 4: PRUEBA DE BÚSQUEDA INTELIGENTE
    # ---------------------------------------------------------
    payload_4 = {
        "modelo_id": "Hero Hunk 160R 4V", # <--- Nombre sucio (con espacios)
        "km_actual": 100,
        "historial_usuario": {}
    }
    try:
        resp = requests.post(URL_PREDICT, json=payload_4, auth=AUTH)
        imprimir_resultado("CASO 4: Búsqueda Inteligente (Nombre Sucio)", payload_4, resp.json())
    except Exception as e: print(f"Error Caso 4: {e}")

if __name__ == "__main__":
    # Verificar que el servidor esté corriendo
    try:
        requests.get(URL_BASE)
        correr_tests()
    except:
        print("❌ ERROR: El servidor Flask no está corriendo.")
        print("   Ejecuta primero: python src/api/app.py")