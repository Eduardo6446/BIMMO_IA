import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
# Ahora apuntamos al endpoint principal que analiza TODA la moto
URL_API = 'http://127.0.0.1:5000/predict_full'

USUARIO = os.getenv("AUTH_USERNAME", "admin")
PASSWORD = os.getenv("AUTH_PASSWORD", "secret")

# Payload Actualizado:
# Ya no enviamos "componente" individual.
# Enviamos el modelo y el KM total, y la IA revisará todo el manual.
payload = {
    "modelo_id": "Hero_Hunk_160R_4V", # Asegúrate que este ID exista en tu base.json
    "km_actual": 7500,                # Simula un kilometraje
    "historial_usuario": {}            # Opcional: Historial real si lo tuvieras
}

print(f"\n🚀 Enviando solicitud a {URL_API}...")
print(f"📋 Datos: Moto {payload['modelo_id']} con {payload['km_actual']} km\n")

try:    
    response = requests.post(
        URL_API, 
        json=payload, 
        auth=(USUARIO, PASSWORD)
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ ¡ÉXITO! Análisis Completo Recibido:\n")
        
        # Mostramos el resumen global
        print(f"Diagnóstico para: {data.get('moto')}")
        print("-" * 50)
        
        # Iteramos sobre las recomendaciones
        resultados = data.get("diagnostico_global", [])
        
        for item in resultados:
            comp = item['componente']
            estado_ia = item['analisis_ia']['diagnostico']
            confianza = item['analisis_ia']['confianza']
            uso = item['datos_tecnicos']['porcentaje_uso']
            
            # Icono según gravedad
            icono = "🟢"
            if estado_ia == "muy_desgastado": icono = "🟠"
            if estado_ia == "fallo_critico": icono = "🔴"
            
            print(f"{icono} {comp.ljust(20)} | Uso: {str(uso)+'%'.ljust(6)} | IA: {estado_ia} ({confianza}%)")
            
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   ¿Está corriendo 'python src/api/app.py'?")