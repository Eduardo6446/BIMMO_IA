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
import matplotlib.pyplot as plt # <--- Importamos Matplotlib

# Configuración de Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '../../models/prod')
METADATA_FILE = os.path.join(MODEL_DIR, 'metadata.yaml')

# DEFINIMOS MÚLTIPLES FUENTES DE DATOS
SYNTHETIC_DATA = os.path.join(BASE_DIR, '../data/datos_entrenamiento_fasev3.jsonl')
REAL_DATA = os.path.join(BASE_DIR, '../data/datos_usuarios.jsonl')

def cargar_datos():
    print("1. 📥 Cargando fuentes de datos...")
    dataframes = []

    if os.path.exists(SYNTHETIC_DATA):
        try:
            df_syn = pd.read_json(SYNTHETIC_DATA, lines=True)
            df_syn['origen'] = 'sintetico'
            dataframes.append(df_syn)
            print(f"   ✅ Base Sintética: {len(df_syn)} registros.")
        except Exception as e:
            print(f"   ⚠️ Error leyendo sintéticos: {e}")

    if os.path.exists(REAL_DATA):
        try:
            df_real = pd.read_json(REAL_DATA, lines=True)
            df_real['origen'] = 'real'
            dataframes.append(df_real)
            print(f"   ✅ Datos Reales (Usuarios): {len(df_real)} registros.")
        except Exception as e:
            print(f"   ⚠️ Error leyendo reales: {e}")
    else:
        print("   ℹ️ Aún no hay archivo de datos reales separado.")

    if not dataframes:
        print("   ❌ No hay datos para entrenar.")
        return None

    df_final = pd.concat(dataframes, ignore_index=True)
    print(f"   📊 Total combinado para entrenamiento: {len(df_final)} registros.")
    return df_final

def entrenar_nuevo_modelo(df):
    print("2. 🧠 Entrenando modelo retador...")
    
    # --- PREPROCESAMIENTO ---
    le_condicion = LabelEncoder()
    y = le_condicion.fit_transform(df['condicion_reportada'])
    
    scaler_km = StandardScaler()
    km_scaled = scaler_km.fit_transform(df['km_realizado_usuario'].values.reshape(-1, 1))
    df_features = pd.get_dummies(df[['modelo_id', 'componente_id']])
    
    cols_prod_path = os.path.join(MODEL_DIR, 'feature_columns.pkl')
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
    
    # --- ENTRENAMIENTO VISIBLE ---
    print("   ⏳ Iniciando entrenamiento (400 épocas)...")
    history = model.fit(
        X_train, y_train, 
        epochs=400, 
        batch_size=64, 
        validation_data=(X_test, y_test), # Importante para ver la línea naranja en la gráfica
        verbose=1 # ¡Esto hará que veas la barra de progreso!
    )
    
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"   🎯 Precisión final del nuevo modelo: {acc*100:.2f}%")

    # --- GENERAR GRÁFICA ---
    try:
        print("   📊 Generando gráfica de rendimiento...")
        plt.figure(figsize=(12, 5))
        
        # Gráfica de Precisión
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'], label='Entrenamiento')
        plt.plot(history.history['val_accuracy'], label='Validación')
        plt.title('Evolución de la Precisión')
        plt.xlabel('Época')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Gráfica de Pérdida
        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'], label='Entrenamiento')
        plt.plot(history.history['val_loss'], label='Validación')
        plt.title('Evolución de la Pérdida')
        plt.xlabel('Época')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Guardar imagen
        plot_path = os.path.join(BASE_DIR, '../../models/prod', 'resultado_entrenamiento.png')
        plt.tight_layout()
        plt.savefig(plot_path)
        print(f"   🖼️  Gráfica guardada en: {plot_path}")
        # plt.show() # Descomentar si tienes entorno gráfico, en servidores mejor solo guardar
        plt.close()
        
    except Exception as e:
        print(f"   ⚠️ No se pudo crear la gráfica: {e}")
    
    return model, acc, le_condicion, scaler_km, df_features.columns.tolist()

def actualizar_produccion(model, acc, le, scaler, cols):
    print("3. 🚀 Desplegando a Producción...")
    
    model.save(os.path.join(MODEL_DIR, 'modelo_mantenimiento_v1.h5'))
    joblib.dump(le, os.path.join(MODEL_DIR, 'encoder_condicion.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler_km.pkl'))
    joblib.dump(cols, os.path.join(MODEL_DIR, 'feature_columns.pkl'))
    
    meta_content = f"""project: MotoIA
version: 1.1.0 (Auto-Trained)
last_training: {datetime.now().isoformat()}
metrics:
  accuracy: {acc:.4f}
status: active
"""
    with open(METADATA_FILE, 'w') as f:
        f.write(meta_content)
        
    print("   ✅ Modelo actualizado exitosamente.")

if __name__ == "__main__":
    print("\n=== MLOps Pipeline: Reentrenamiento Automático ===")
    df = cargar_datos()
    if df is not None:
        model, acc, le, scaler, cols = entrenar_nuevo_modelo(df)
        
        # Umbral de calidad (0.78 es tu baseline actual)
        if acc >= 0.75: 
            actualizar_produccion(model, acc, le, scaler, cols)
        else:
            print(f"   ⚠️ El modelo nuevo ({acc:.2f}) no superó el estándar de calidad. No se despliega.")