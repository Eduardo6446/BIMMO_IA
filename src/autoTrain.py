# -*- coding: utf-8 -*-
import json
import numpy as np
import pandas as pd
import tensorflow as tf
import pickle  # <--- NUEVO: Importamos pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_DATOS = os.path.join(BASE_DIR, '../data/datos_entrenamiento_fase5.jsonl')

def cargar_datos(ruta):
    data = []
    print(f"📂 Cargando datos desde: {ruta}")
    with open(ruta, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return pd.DataFrame(data)

def preprocesar_datos(df):
    print("⚙️  Preprocesando e Ingeniería de Características...")
    
    # 1. INGENIERÍA DE CARACTERÍSTICAS
    epsilon = 1e-6
    df['ratio_uso'] = df['km_realizado_usuario'] / (df['km_recomendacion_app'] + epsilon)
    df['diferencia_km'] = df['km_realizado_usuario'] - df['km_recomendacion_app']
    
    features = ['km_realizado_usuario', 'km_recomendacion_app', 'ratio_uso', 'diferencia_km']
    X = df[features].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    encoder = LabelEncoder()
    y_int = encoder.fit_transform(df['condicion_reportada'])
    y_onehot = to_categorical(y_int)
    
    class_names = encoder.classes_
    print(f"   -> Clases detectadas: {class_names}")
    
    # MODIFICACIÓN: Devolvemos también los objetos scaler y encoder para guardarlos
    return X_scaled, y_onehot, class_names, y_int, scaler, encoder

def construir_modelo_robusto(input_dim, num_classes):
    print("🧠 Construyendo Arquitectura Densa...")
    model = Sequential([
        Dense(64, input_dim=input_dim, activation='relu'),
        BatchNormalization(),
        
        Dense(32, activation='relu'),
        Dropout(0.3),
        
        Dense(16, activation='relu'),
        
        Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

def plot_confusion_matrix(y_true, y_pred, classes, out_path):
    # Calcular matriz
    cm = confusion_matrix(y_true, y_pred)
    
    # Normalizar para ver porcentajes (mejor para datasets grandes)
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title('Matriz de Confusión Normalizada')
    plt.ylabel('Verdad (Etiqueta Real)')
    plt.xlabel('Predicción del Modelo')
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"📊 Matriz de confusión guardada: {out_path}")

def main():
    # 1. Cargar
    df = cargar_datos(ARCHIVO_DATOS)
    
    # 2. Preprocesar (Recibimos scaler y encoder)
    X, y_onehot, class_names, y_int_total, scaler, encoder = preprocesar_datos(df)
    
    # 3. Split (Usamos estratificación para mantener balance)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_onehot, test_size=0.2, random_state=42, stratify=y_int_total
    )
    
    # 4. Construir
    model = construir_modelo_robusto(input_dim=X.shape[1], num_classes=y_onehot.shape[1])
    
    # 5. Entrenar
    print("🚀 Iniciando entrenamiento...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=200, 
        batch_size=64,
        verbose=1
    )
    
    # 6. Evaluar
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n🏆 RESULTADO FINAL:")
    print(f"   Precisión (Accuracy): {accuracy*100:.2f}%")
    print(f"   Pérdida (Loss): {loss:.4f}")
    
    # 7. Diagnóstico Detallado (Matriz de Confusión)
    print("\n🔍 Generando diagnóstico de errores...")
    y_pred_probs = model.predict(X_test)
    y_pred_classes = np.argmax(y_pred_probs, axis=1)
    y_true_classes = np.argmax(y_test, axis=1)
    
    # Guardar Gráfico de Matriz
    ruta_matriz = os.path.join(BASE_DIR, 'matriz_confusion.png')
    plot_confusion_matrix(y_true_classes, y_pred_classes, class_names, ruta_matriz)
    
    # Reporte de texto
    print("\n📋 Reporte de Clasificación:")
    print(classification_report(y_true_classes, y_pred_classes, target_names=class_names))

    # 8. Guardar modelo y gráficos de entrenamiento
    ruta_modelo = os.path.join(BASE_DIR, '../models/modelo_desgaste_v2.h5')
    os.makedirs(os.path.dirname(ruta_modelo), exist_ok=True)
    model.save(ruta_modelo)
    print(f"💾 Modelo guardado en: {ruta_modelo}")

    # --- NUEVO: GUARDAR LOS PKL ---
    ruta_scaler = os.path.join(BASE_DIR, '../models/scaler.pkl')
    ruta_encoder = os.path.join(BASE_DIR, '../models/encoder.pkl')
    
    with open(ruta_scaler, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"💾 Scaler guardado en: {ruta_scaler}")
    
    with open(ruta_encoder, 'wb') as f:
        pickle.dump(encoder, f)
    print(f"💾 Encoder guardado en: {ruta_encoder}")
    # -----------------------------

    # Gráfico de historia (Accuracy/Loss)
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Train')
    plt.plot(history.history['val_accuracy'], label='Val')
    plt.title('Precisión del Modelo')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Train')
    plt.plot(history.history['val_loss'], label='Val')
    plt.title('Pérdida')
    plt.legend()
    
    plt.savefig(os.path.join(BASE_DIR, 'resultado_entrenamiento.png'))

if __name__ == "__main__":
    main()