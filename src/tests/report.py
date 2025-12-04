from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv

# Cargar credenciales del archivo .env (si existe) para no escribirlas manual
load_dotenv()

# CONFIGURACIÓN
# ---------------------------------------------------------
URL_API = 'http://127.0.0.1:5000/reportar_mantenimiento'

# Usa las credenciales que definiste en tu .env
# Si no las cambiaste, por defecto en el código anterior eran:
USUARIO = os.getenv("AUTH_USERNAME")
PASSWORD = os.getenv("AUTH_PASSWORD")
# ---------------------------------------------------------

# DATOS DE PRUEBA (El caso de uso)
# Imagina un usuario con una Pulsar NS200 que tiene 12,500 km.
# El manual dice cambiar aceite cada 5,000 km.
# Pero este usuario le cambió el aceite hace poco (a los 11,000 km).
# Datos simulados de un usuario real
payload = {
    "fecha_reporte": f"{datetime.now().isoformat()}",
    "usuario_id_hash": "test_user_123",
    "modelo_id": "Bajaj_Pulsar_NS200",
    "componente_id": "bujias",
    "accion_realizada": "REEMPLAZAR",
    "km_recomendacion_app": 10000,
    "km_realizado_usuario": 12500,
    "condicion_reportada": "muy_desgastado"
}

print("\n🚀 Enviando solicitud de reporte de mantenimiento al servidor IA...\n")

try:
    response = requests.post(
        URL_API, 
        json=payload, 
        auth=(USUARIO, PASSWORD) # Autenticación Básica
    )

    if response.status_code == 201:
        data = response.json()
        print("\n✅ ¡ÉXITO! Respuesta del Servidor:\n")
        print(json.dumps(data, indent=4, ensure_ascii=False))
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   ¿Está el servidor corriendo? (python app_api_flask_ia.py)")