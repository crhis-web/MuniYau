# 🏛️ Municipalidad Inteligente - MVP de Gestión de Trámites

Sistema integral de gestión de trámites municipales diseñado para resolver cuellos de botella burocráticos mediante **Inteligencia Artificial (Machine Learning)** y una arquitectura backend de alta eficiencia.

## 🎯 El Problema
La Municipalidad Provincial de Yau enfrenta largas colas, procesamiento manual propenso a errores y falta de transparencia. Este MVP automatiza la recepción de reportes ciudadanos y clasifica instantáneamente la **prioridad** de cada incidente para agilizar la respuesta gubernamental.

## 🏗️ Arquitectura de la Solución

El proyecto sigue una arquitectura desacoplada y orientada a servicios:

1.  **Cerebro Predictivo (Scikit-Learn):** Un modelo de Machine Learning (`modelo_tramites.pkl`) entrenado localmente.
2.  **Motor Backend (FastAPI):** Una API asíncrona de alto rendimiento que integra el modelo predictivo, gestiona la base de datos (SQLite) y dispara alertas en segundo plano (simulación SMTP).
3.  **Interfaz Ciudadana (React + Tailwind CSS):** Una Single Page Application diseñada bajo el principio de **utilidad institucional y accesibilidad extrema**, garantizando compatibilidad con dispositivos de gama baja en escenarios de calle.

## 🧠 Decisiones de Diseño de Inteligencia Artificial

### ¿Por qué Random Forest + TF-IDF y no Redes Neuronales?
Para un entorno municipal (con presupuestos limitados y sin granjas de GPUs), una red neuronal profunda (como BERT o LLMs modernos) es un sobre-despliegue innecesario ("overkill") para clasificar texto simple.
*   **Velocidad y Explicabilidad:** Random Forest es extremadamente rápido en inferencia y, sobre todo, no es una "caja negra" absoluta. Las decisiones en la gestión pública requieren transparencia.
*   **Eficiencia:** TF-IDF vectoriza texto basándose en la frecuencia de términos, lo que es ideal para captar palabras clave críticas (ej. "poste", "agua", "roto").

### El Espejismo del F1-Score Perfecto (1.00)
Nuestro script `train_model.py` genera datos sintéticos lógicos y balanceados para evitar el envenenamiento del modelo. Durante el entrenamiento, el algoritmo alcanza un **F1-Score de 1.00**. 
**Aclaración Técnica Importante:** En un entorno de producción real, este 1.00 es una señal de que el dataset es "demasiado limpio" (ortografía perfecta). En fases posteriores, se deberá implementar un preprocesamiento agresivo (corrección fonética, lematización avanzada) para manejar jergas, dialectos locales y errores ortográficos propios de un reporte ciudadano de urgencia, garantizando así la resiliencia del modelo "en la calle".

## 🛡️ Seguridad y Pruebas de Estrés
La API está protegida por `Pydantic` contra ataques de denegación de servicio (DoS) por payload. 
*   Se han configurado límites estrictos de caracteres en todos los campos. Un intento de inyectar un texto de 5,000 palabras es bloqueado en milisegundos devolviendo un `HTTP 422 Unprocessable Entity` antes de que el texto llegue al modelo predictivo, salvaguardando la CPU del servidor.
*   Credenciales y URLs críticas están segregadas en variables de entorno `.env` (no harcodeadas).

## 🚀 Instalación y Ejecución Local (Getting Started)

Sigue estos pasos para clonar y ejecutar el proyecto en tu entorno local.

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/municipalidad-mvp.git
cd municipalidad-mvp
```

### 2. Configurar el Entorno Backend (Python)
Crea y activa tu entorno virtual:
```bash
# En Windows:
python -m venv venv
.\venv\Scripts\Activate.ps1

# En Mac/Linux:
python3 -m venv venv
source venv/bin/activate
```
Instala las dependencias:
```bash
pip install -r requirements.txt
```

### 3. Variables de Entorno y Entrenamiento del Modelo
Crea un archivo `.env` en la raíz del proyecto basándote en la plantilla `.env.example`. El sistema requiere este archivo para ejecutarse de forma segura:
```env
# .env
FRONTEND_URL=http://localhost:5173
SMTP_USER=correo_municipalidad_pruebas@gmail.com
SMTP_PASSWORD=tu_password_seguro_aqui
```

Luego, genera el dataset sintético y entrena el modelo de Machine Learning (creará el archivo `modelo_tramites.pkl`):
```bash
python train_model.py
```

### 4. Configurar el Frontend (React)
Abre **otra terminal** en la raíz de tu proyecto y entra a la carpeta del frontend:
```bash
cd frontend
npm install
```

### 5. Encender los Servidores
**Terminal 1 (Raíz del proyecto - Backend):**
```bash
uvicorn main:app --reload
```
**Terminal 2 (Carpeta frontend):**
```bash
npm run dev
```

El frontend estará disponible en `http://localhost:5173` y la API en `http://localhost:8000`.

### 🔑 Credenciales de Prueba (Modo Evaluador/Profesor)
Dado que el panel de funcionarios está altamente protegido por un sistema de **Autenticación con JWT (JSON Web Tokens)**, la API creará automáticamente un usuario administrador por defecto en la base de datos al encenderse por primera vez. Esto facilitará las pruebas en el entorno académico.

Utilice las siguientes credenciales para acceder al **Panel Funcionario** en el frontend:
* **Usuario:** `admin`
* **Contraseña:** `admin123`

## 🌐 Pase a Producción (Siguientes Pasos)
Para un despliegue real en oficinas gubernamentales (fuera de localhost):
*   Empaquetar el backend en contenedores **Docker** usando `Gunicorn` como servidor de producción.
*   Compilar el frontend (`npm run build`) y servir mediante **Nginx** o un CDN.
*   Migrar de la base de datos local SQLite a **PostgreSQL**.

## Mejora de Seguridad (Fase 6): Protección Anti-Trolls y Spam

A solicitud del usuario, implementaremos medidas de grado de producción en el MVP para evitar ataques y basura de "chistosos".

> [!IMPORTANT]
> **Revisión del Usuario Requerida**
> Por favor revisa las tácticas de protección descritas abajo. Si apruebas, modificaré los códigos del modelo y de la API.

### 1. El Filtro Heurístico (Pre-Machine Learning)
*   **El Punto Ciego de la IA:** El TF-IDF vectoriza palabras conocidas. Si un troll escribe `"asdfghj"`, la IA recibe un vector vacío y fallaría silenciosamente.
*   **La Solución:** Antes de invocar al modelo `.pkl`, la API ejecuta una función Regex (expresiones regulares) que detecta patrones anómalos (ej. 6 consonantes seguidas, risas repetitivas). Si el texto es basura, se descarta sin gastar ciclos de CPU de inferencia.

### 2. "Shadow Banning" Perfecto en la Base de Datos
*   Cuando el filtro Heurístico detecta "Spam", el backend **NO** guarda el registro en SQLite y **NO** activa la notificación SMTP.
*   Para que la mentira sea creíble y el frontend de React no crashee, la API devuelve un **ID de ticket falso (ej. 98321)**. Al troll se le muestra el mensaje de éxito, creyendo que su broma funcionó, evitando que busque vulnerabilidades más complejas.

### 3. Límite de Peticiones (Rate Limiting) y el Problema del CGNAT
*   Hemos instalado la librería `slowapi` limitando a **3 peticiones por minuto por IP** para evitar ataques automatizados (DoS).
*   **Consideración Arquitectónica para Producción:** En provincias del Perú, los proveedores de telecomunicaciones usan agresivamente **CGNAT**, donde cientos de vecinos comparten una misma IP pública. Bloquear por IP en producción aislaría a ciudadanos legítimos. En una fase posterior de escalamiento, este bloqueo debe reemplazarse por **Browser Fingerprinting** o **Tokens de Sesión (JWT)** vinculados a la RENIEC.

## 📸 Documentación de API Autogenerada
FastAPI provee documentación interactiva automática bajo el estándar OpenAPI.
*(Adjuntar capturas de pantalla de `http://localhost:8000/docs` mostrando el Swagger UI aquí).*
