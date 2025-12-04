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
# ---------------------------------------------------------

# DATOS DE PRUEBA (El caso de uso)
# Imagina un usuario con una Pulsar NS200 que tiene 12,500 km.
# El manual dice cambiar aceite cada 5,000 km.
# Pero este usuario le cambió el aceite hace poco (a los 11,000 km).
payload = {
    "modelo_id": "Bajaj_Pulsar_NS200",
    "cilindrada": 200,
    "km_actual": 12500,
    "historial_usuario": [
        {
            "componente_id": "bugia",
            "km_mantenimiento": 11000  # Lo cambió hace 1,500 km
        }
    ]
}

print("\n🚀 Enviando solicitud de análisis de mantenimiento al servidor IA...\n")



try:
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
        analisis = data.get("analisis", [])
        print(f"{'COMPONENTE':<30} | {'URGENCIA':<10} | {'IA DICE':<15} | {'FUENTE'}")
        print("-" * 85)
        
        for item in analisis:
            comp = item['componente']
            urgencia = item['calculo']['urgencia'] # 0.0 a 1.0+
            ia_estado = item['prediccion_ia']['estado_probable']
            origen = item['calculo']['origen_dato']
            
            # Barra visual de urgencia
            barra = "█" * int(urgencia * 10)
            
            print(f"{comp:<30} | {urgencia:<4.2f} {barra:<5} | {ia_estado:<15} | {origen}")
            
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   ¿Está el servidor corriendo? (python app_api_flask_ia.py)")