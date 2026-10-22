# 🐳 Agente de Soporte con Python, Gemini y Docker (Contenedores)

> **Práctica 3 – DAI**: Empaquetado, distribución y ejecución continua del Agente de Soporte en contenedores Docker con inyección segura de credenciales.

---

## 📋 Descripción General

Este proyecto consiste en la **contenedorización completa** de un agente de soporte basado en Inteligencia Artificial. El agente supervisa en tiempo real una hoja de cálculo de Google Sheets con quejas y comentarios de clientes, analizando cada entrada mediante **Google Gemini 2.5 Flash** para:

1. **Clasificar el departamento responsable**: `Ventas`, `Soporte Técnico` o `Logística`.
2. **Detectar el sentimiento**: `Positivo`, `Negativo` o `Neutro`.
3. **Actualizar automáticamente la base de datos** en Google Sheets con los resultados obtenidos.
4. **Ejecutarse de forma continua o por lotes** dentro de un contenedor **Docker** aislado, reproducible y tolerante a fallas.

---

## 🏗️ Arquitectura del Contenedor

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Máquina Anfitriona (Host)                       │
│                                                                        │
│   Archivos locales con secretos:                                       │
│   ├── .env       ──▶ (GEMINI_API_KEY)                                  │
│   └── token.env  ──▶ (GOOGLE_TOKEN_JSON)                               │
│                           │                  │                         │
│             --env-file .env │                  │ --env-file token.env   │
│                           ▼                  ▼                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               Contenedor Docker: agente-soporte                  │  │
│  │                                                                  │  │
│  │   Linux Debian (python:3.12-slim) + PYTHONUNBUFFERED=1           │  │
│  │   Directorio: /app                                               │  │
│  │                                                                  │  │
│  │   ┌──────────────────────────────────────────────────────────┐   │  │
│  │   │                    agente_soporte.py                     │   │  │
│  │   │                                                          │   │  │
│  │   │   ┌──────────────┐     ┌──────────────┐   ┌───────────┐  │   │  │
│  │   │   │ Google Sheets│◀───▶│   Bucle de   │──▶│  Gemini   │  │   │  │
│  │   │   │  (gspread)   │     │  Revisión    │   │ 2.5 Flash │  │   │  │
│  │   │   └──────────────┘     └──────────────┘   └───────────┘  │   │  │
│  │   └──────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                │                                       │
│                 docker logs -f │ Registros en vivo                     │
│                                ▼                                       │
│                    Terminal / Docker Desktop                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Repositorio

```
DAI_Contenedores/
│
├── Dockerfile                     # Receta de construcción de la imagen Docker
├── .dockerignore                  # Excluye credenciales y basura de la imagen
├── .gitignore                     # Protege archivos sensibles de ser subidos a Git
├── agente_soporte.py              # Script principal del agente autónomo
├── requirements.txt               # Dependencias de Python
├── Practica3_Agente_Docker.pdf    # Guía oficial de la Práctica 3
├── README.md                      # Documentación del proyecto
│
├── .github/
│   └── workflows/
│       └── agente.yml             # Workflow de GitHub Actions (Práctica 2)
│
├── docs/                          # Sitio web del proyecto (GitHub Pages)
│   ├── index.html
│   ├── privacidad.html
│   ├── terminos.html
│   └── style.css
│
├── .env.example                   # Plantilla pública de variables de entorno
│
├── .env                           # [PRIVADO] API Key de Gemini (ignorado por Git y Docker)
├── token.env                      # [PRIVADO] Token OAuth Google (ignorado por Git y Docker)
└── client_secrets.json            # [PRIVADO] Credencial inicial de Google (ignorado)
```

---

## ⚙️ Especificación del `Dockerfile`

El [Dockerfile](file:///c:/Users/ecrui/OneDrive/DAI_Contenedores/Dockerfile) fue construido siguiendo las mejores prácticas de optimización por capas:

```dockerfile
# 1. Imagen base oficial ligera
FROM python:3.12-slim

# 2. Salida directa en consola para ver los logs en tiempo real
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo aislado
WORKDIR /app

# 4. Copiar e instalar dependencias primero (aprovecha la caché de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar únicamente el script del agente
COPY agente_soporte.py .

# 6. Punto de entrada flexible para admitir argumentos (ej. --una-vez)
ENTRYPOINT ["python", "agente_soporte.py"]
```

### ¿Por qué esta estructura?
- **Caché eficiente**: Si el código fuente (`agente_soporte.py`) cambia, Docker no reinstala las librerías de Python; reutiliza la capa de `pip install` en cuestión de segundos.
- **`PYTHONUNBUFFERED=1`**: En contenedores, Python normalmente guarda los mensajes de `print()` en un búfer. Esta variable asegura que cada registro se imprima inmediatamente al consultar `docker logs`.
- **`ENTRYPOINT` flexible**: Permite ejecutar el contenedor tanto en modo continuo (por defecto) como en ejecuciones puntuales añadiendo `--una-vez` al final del comando.

---

## 🔐 Seguridad y Protección de Secretos

El principio fundamental de Docker es que **las imágenes nunca deben contener credenciales privadas**, ya que cualquier usuario con acceso a la imagen podría extraerlas.

### 1. `.dockerignore`
Garantiza que ningún archivo confidencial sea enviado al contexto de construcción de la imagen:
```text
.env
token.env
client_secrets.json
.git
__pycache__/
```

### 2. Verificación de la Imagen Limpia
Para corroborar que la imagen no almacena secretos:
```bash
docker run --rm --entrypoint ls agente-soporte -A /app
```
**Salida esperada:**
```text
agente_soporte.py
requirements.txt
```

### 3. Inyección de Credenciales en Runtime
Las credenciales se entregan al contenedor únicamente en el momento de arranque mediante `--env-file`:
- `.env`: contiene `GEMINI_API_KEY=tu_api_key`
- `token.env`: contiene `GOOGLE_TOKEN_JSON={"token": "...", ...}` en una sola línea

---

## 🚀 Guía de Uso y Comandos

### 1. Construir la Imagen
```bash
docker build -t agente-soporte .
```

### 2. Ejecución Única (Modo Batch)
Procesa todas las filas pendientes en la hoja de cálculo y finaliza el contenedor liberando memoria:
```bash
docker run --rm --env-file .env --env-file token.env agente-soporte --una-vez
```

### 3. Ejecución Continua en Segundo Plano (Daemon)
Corre el agente de forma persistente como un microservicio que revisa la hoja cada intervalo programado:
```bash
docker run -d --name agente --restart unless-stopped --env-file .env --env-file token.env agente-soporte
```

### 4. Monitoreo y Administración
- **Ver logs en tiempo real**:
  ```bash
  docker logs -f agente
  ```
- **Detener el contenedor**:
  ```bash
  docker stop agente
  ```
- **Volver a iniciarlo**:
  ```bash
  docker start agente
  ```
- **Eliminar el contenedor**:
  ```bash
  docker rm -f agente
  ```

---

## 📊 Matriz Comparativa: Evolución de las Prácticas

| Característica | Práctica 1 (Local) | Práctica 2 (GitHub Actions) | Práctica 3 (Docker) |
|---|---|---|---|
| **Entorno de ejecución** | PC del desarrollador | Runner efímero en la nube | Contenedor reproducible en cualquier SO |
| **Instalación de dependencias** | Manual con `pip` | En cada corrida del runner | Una sola vez durante el `build` |
| **Persistencia / Bucle** | Script activo en terminal | Tarea cron programada | Demonio continuo con `schedule` |
| **Gestión de credenciales** | Archivos `.env` y OAuth | GitHub Secrets cifrados | Inyección segura con `--env-file` |
| **Observabilidad** | Terminal abierta | Consola de GitHub Actions | `docker logs -f` / Docker Desktop |
| **Tolerancia a fallos** | Manual si se cierra | Se espera al siguiente cron | `--restart unless-stopped` automático |

---

## 💡 Preguntas de Reflexión

1. **Diferencia entre una imagen y un contenedor:**  
   La *imagen* es el molde o plantilla inmutable de solo lectura que contiene el sistema operativo base, las dependencias y el código empaquetado. El *contenedor* es la instancia viva en ejecución creada a partir de esa imagen, con su propio espacio de memoria y aislamiento de procesos.

2. **Riesgo de omitir `.env` en `.dockerignore`:**  
   Si se publica la imagen en un registro público como Docker Hub, cualquier persona podría descargarla (`docker pull`) y leer el contenido del `.env`, comprometiendo la API Key de Gemini y consumiendo cuotas o generando costos.

3. **Por qué copiar `requirements.txt` antes del script:**  
   Para optimizar el uso de la caché por capas. Instalar paquetes de Python es un proceso lento; al separar las dependencias del código, cualquier cambio futuro en `agente_soporte.py` se reconstruye en menos de dos segundos sin tener que descargar ni compilar librerías nuevamente.

4. **Por qué la misma imagen soporta modo continuo y `--una-vez`:**  
   Gracias al uso de `ENTRYPOINT ["python", "agente_soporte.py"]`. Docker concatena cualquier parámetro adicional al final del entrypoint; por lo tanto, pasar `--una-vez` invoca `python agente_soporte.py --una-vez` sin necesidad de crear imágenes separadas.

5. **Por qué no basta `docker restart` al renovar el token:**  
   Porque las variables inyectadas mediante `--env-file` quedan fijadas en la creación del contenedor. Para cargar un token nuevo es indispensable remover el contenedor (`docker rm -f agente`) y ejecutar de nuevo `docker run` con el archivo actualizado.

6. **GitHub Actions vs. Contenedor en Servidor:**  
   - **GitHub Actions:** Óptimo para tareas periódicas poco frecuentes (por ejemplo cada 1 o 2 horas) con bajo consumo y sin costo de servidor.  
   - **Contenedores (Docker):** Indispensable cuando se requiere monitoreo de alta frecuencia (segundos o minutos), baja latencia de respuesta inmediata, y despliegue estándar en nubes como GCP Cloud Run, AWS ECS o VPS privados.
