import requests
import json
import os
from dotenv import load_dotenv

# Cargar credenciales del archivo .env (si existe) para no escribirlas manual
load_dotenv()

# CONFIGURACIÓN
# ---------------------------------------------------------
URL_API = 'http://127.0.0.1:5000/predict'

# Usa las credenciales que definiste en tu .env
# Si no las cambiaste, por defecto en el código anterior eran:
USUARIO = os.getenv("AUTH_USERNAME")
PASSWORD = os.getenv("AUTH_PASSWORD")

payload = {
    "modelo": "Bajaj_Pulsar_NS200",
    "componente": "bujias",
    "km": 10000
}

print("\n🚀 Enviando solicitud de análisis de mantenimiento al servidor IA...\n")

try:    
    # Enviamos petición POST simulada
    response = requests.post(
        URL_API, 
        json=payload, 
        auth=(USUARIO, PASSWORD) # Autenticación Básica
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ ¡ÉXITO! Respuesta del Servidor:\n")
        
        print(json.dumps(data, indent=4, ensure_ascii=False))
        
        # Mostramos los resultados bonitos
        analisis = data.get("analisis", {})
            
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   ¿Está el servidor corriendo? (python app_api_flask_ia.py)")