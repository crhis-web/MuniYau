import os
import random
import pandas as pd
import joblib
from faker import Faker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Initialize Faker
fake = Faker('es_ES')

# Estructura base para evitar envenenamiento de datos
categorias = {
    "Alta": {
        "problemas": ["poste a punto de caer", "hueco profundo en la pista", "tubo de agua roto", "cable eléctrico suelto"],
        "contextos": ["urgente en mi calle", "peligro inminente", "casi causa un accidente"]
    },
    "Media": {
        "problemas": ["basura acumulada", "parque sin podar", "farola apagada", "ruido molesto de vecinos"],
        "contextos": ["por favor solucionar", "hace semanas", "es muy molesto"]
    },
    "Baja": {
        "problemas": ["solicitud de licencia", "pago de arbitrios", "copia de planos", "estado de mi trámite"],
        "contextos": ["para mi negocio", "necesito información", "trámite administrativo"]
    }
}

def generar_datos(muestras_por_clase=666):
    datos = []
    
    for prioridad, contenido in categorias.items():
        for _ in range(muestras_por_clase):
            problema = random.choice(contenido["problemas"])
            contexto = random.choice(contenido["contextos"])
            
            # Construir la descripción de forma realista
            descripcion = f"{problema}, {contexto}."
            
            # Generar datos adicionales
            registro = {
                "ID_Tramite": fake.uuid4(),
                "DNI_Falso": fake.unique.random_number(digits=8, fix_len=True),
                "Email_Falso": fake.email(),
                "Descripcion_Tramite": descripcion,
                "Prioridad": prioridad
            }
            datos.append(registro)
            
    df = pd.DataFrame(datos)
    # Mezclar los datos
    df = df.sample(frac=1).reset_index(drop=True)
    return df

if __name__ == "__main__":
    print("Generando dataset sintético balanceado...")
    df = generar_datos(muestras_por_clase=666)
    print(f"Total de registros generados: {len(df)}")
    print(df["Prioridad"].value_counts())
    
    # Preparar datos para ML
    X = df["Descripcion_Tramite"]
    y = df["Prioridad"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nEntrenando modelo (TF-IDF + Random Forest)...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    pipeline.fit(X_train, y_train)
    
    print("\nEvaluando modelo...")
    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    # Guardar el modelo
    model_path = "modelo_tramites.pkl"
    joblib.dump(pipeline, model_path)
    print(f"\nModelo exportado exitosamente a {model_path}")
