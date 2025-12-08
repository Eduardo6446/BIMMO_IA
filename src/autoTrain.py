import os

# 1. SILENCIAR LOGS DE TENSORFLOW
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import sys
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime
import json
import matplotlib.pyplot as plt
import glob

# Configuración de Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_ROOT = os.path.join(BASE_DIR, '../models/') # Raíz de modelos
PROD_DIR = os.path.join(MODELS_ROOT, 'prod')
METADATA_FILE_PROD = os.path.join(PROD_DIR, 'metadata.yaml')

# DEFINIMOS MÚLTIPLES FUENTES DE DATOS
SYNTHETIC_DATA = os.path.join(BASE_DIR, '../data/datos_entrenamiento_fasev3.jsonl')
REAL_DATA = os.path.join(BASE_DIR, '../data/datos_usuarios.jsonl')

def cargar_datos():
    print("1. 📥 Cargando fuentes de datos...")
    dataframes = []
    tipos_datos = []

    if os.path.exists(SYNTHETIC_DATA):
        try:
            df_syn = pd.read_json(SYNTHETIC_DATA, lines=True)
            if not df_syn.empty:
                df_syn['origen'] = 'sintetico'
                dataframes.append(df_syn)
                tipos_datos.append('s') # s = sintético
                print(f"   ✅ Base Sintética: {len(df_syn)} registros.")
        except Exception as e:
            print(f"   ⚠️ Error leyendo sintéticos: {e}")

    if os.path.exists(REAL_DATA):
        try:
            df_real = pd.read_json(REAL_DATA, lines=True)
            if not df_real.empty:
                df_real['origen'] = 'real'
                dataframes.append(df_real)
                tipos_datos.append('r') # r = real
                print(f"   ✅ Datos Reales (Usuarios): {len(df_real)} registros.")
        except Exception as e:
            print(f"   ⚠️ Error leyendo reales: {e}")
    else:
        print("   ℹ️ Aún no hay archivo de datos reales separado.")

    if not dataframes:
        print("   ❌ No hay datos para entrenar.")
        return None, None

    df_final = pd.concat(dataframes, ignore_index=True)
    
    # Determinar sufijo (sr, s, r)
    sufijo = "".join(sorted(tipos_datos)) # 'rs' -> 'rs', pero queremos 'sr'? ordenemoslo.
    if 's' in tipos_datos and 'r' in tipos_datos: sufijo = 'sr'
    elif 's' in tipos_datos: sufijo = 's'
    elif 'r' in tipos_datos: sufijo = 'r'
    
    print(f"   📊 Total combinado para entrenamiento ({sufijo}): {len(df_final)} registros.")
    return df_final, sufijo

def entrenar_nuevo_modelo(df):
    print("2. 🧠 Entrenando modelo retador...")
    
    # --- PREPROCESAMIENTO ---
    le_condicion = LabelEncoder()
    y = le_condicion.fit_transform(df['condicion_reportada'])
    
    scaler_km = StandardScaler()
    km_scaled = scaler_km.fit_transform(df['km_realizado_usuario'].values.reshape(-1, 1))
    df_features = pd.get_dummies(df[['modelo_id', 'componente_id']])
    
    # Intentar alinear con producción si existe, sino usar lo que hay
    cols_prod_path = os.path.join(PROD_DIR, 'feature_columns.pkl')
    if os.path.exists(cols_prod_path):
        cols_prod = joblib.load(cols_prod_path)
        for col in cols_prod:
            if col not in df_features.columns:
                df_features[col] = 0
        df_features = df_features[cols_prod]
    
    X = np.hstack([km_scaled, df_features.values])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # --- MODELO ---
    num_clases = len(le_condicion.classes_)
    input_dim = X_train.shape[1]
    
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(num_clases, activation='softmax')
    ])
    
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    # Entrenamiento con Verbose 1 para ver progreso
    print("   ⏳ Iniciando entrenamiento (50 épocas)...")
    history = model.fit(
        X_train, y_train, 
        epochs=10, 
        batch_size=64, 
        validation_data=(X_test, y_test),
        verbose=1
    )
    
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"   🎯 Precisión final del nuevo modelo: {acc*100:.2f}%")
    
    return model, acc, le_condicion, scaler_km, df_features.columns.tolist(), history

def generar_nombre_carpeta(sufijo):
    """Genera el nombre ddmmyyyye#sufijo incrementando el número de entrenamiento"""
    fecha_hoy = datetime.now().strftime("%d%m%Y")
    patron = os.path.join(MODELS_ROOT, f"{fecha_hoy}e*#{sufijo}")
    carpetas_existentes = glob.glob(patron)
    
    numero = 1
    if carpetas_existentes:
        # Extraer números de carpetas existentes (ej: ...e1#sr -> 1)
        numeros = []
        for carpeta in carpetas_existentes:
            try:
                nombre = os.path.basename(carpeta)
                parte_num = nombre.split('e')[1]
                numeros.append(int(parte_num))
            except: pass
        if numeros:
            numero = max(numeros) + 1
            
    nombre_carpeta = f"{fecha_hoy}e{numero}{sufijo}"
    ruta_completa = os.path.join(MODELS_ROOT, nombre_carpeta)
    return ruta_completa, nombre_carpeta

def guardar_experimento(ruta_destino, model, acc, le, scaler, cols, history):
    print(f"3. 💾 Guardando experimento en: {ruta_destino}")
    
    os.makedirs(ruta_destino, exist_ok=True)
    
    # Guardar Artefactos
    model.save(os.path.join(ruta_destino, 'modelo_mantenimiento_v1.h5'))
    joblib.dump(le, os.path.join(ruta_destino, 'encoder_condicion.pkl'))
    joblib.dump(scaler, os.path.join(ruta_destino, 'scaler_km.pkl'))
    joblib.dump(cols, os.path.join(ruta_destino, 'feature_columns.pkl'))
    
    # Generar Gráfica
    try:
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'], label='Entrenamiento')
        plt.plot(history.history['val_accuracy'], label='Validación')
        plt.title('Precisión')
        plt.xlabel('Época'); plt.ylabel('Acc'); plt.legend(); plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'], label='Entrenamiento')
        plt.plot(history.history['val_loss'], label='Validación')
        plt.title('Pérdida')
        plt.xlabel('Época'); plt.ylabel('Loss'); plt.legend(); plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(ruta_destino, 'resultado_entrenamiento.png'))
        plt.close()
    except Exception as e:
        print(f"   ⚠️ Error gráfica: {e}")

    # Metadata del Experimento
    meta = {
        "version_name": os.path.basename(ruta_destino),
        "created_at": datetime.now().isoformat(),
        "metrics": {"accuracy": float(acc)},
        "status": "experiment"
    }
    with open(os.path.join(ruta_destino, 'metadata.json'), 'w') as f:
        json.dump(meta, f, indent=4)
        
    print("   ✅ Experimento guardado.")

if __name__ == "__main__":
    print("\n=== MLOps Pipeline: Reentrenamiento Automático ===")
    df, sufijo_datos = cargar_datos()
    
    if df is not None:
        # Entrenar
        model, acc, le, scaler, cols, history = entrenar_nuevo_modelo(df)
        
        # 1. SIEMPRE guardar en carpeta versionada (Historial)
        ruta_exp, nombre_exp = generar_nombre_carpeta(sufijo_datos)
        guardar_experimento(ruta_exp, model, acc, le, scaler, cols, history)
        
        # 2. EVALUAR si actualizamos producción (Umbral 75%)
        # En un sistema real compararíamos contra el modelo en prod actual
        if acc > 0.85:
            print(f"\n🚀 ¡El modelo ({acc:.2%}) es bueno! Actualizando producción...")
            # Copiar archivos a prod/
            import shutil
            for archivo in os.listdir(ruta_exp):
                origen = os.path.join(ruta_exp, archivo)
                destino = os.path.join(PROD_DIR, archivo)
                if os.path.isfile(origen):
                    shutil.copy2(origen, destino)
            print("   ✅ Producción actualizada.")
        else:
            print(f"\n⚠️ El modelo ({acc:.2%}) no superó el estándar (75%). Se guarda solo como experimento.")