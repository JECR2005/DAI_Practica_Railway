# 🚂 Agente de Soporte con Python, Gemini y Railway

> **Práctica 4 – DAI**: Despliegue en la nube del Agente de Soporte mediante **Railway**, con ejecución continua 24/7, variables de entorno seguras y sin necesidad de mantener un servidor propio.

---

## 📋 Descripción General

Este proyecto despliega un **agente de soporte basado en Inteligencia Artificial** directamente en la nube usando **Railway**. El agente supervisa en tiempo real una hoja de cálculo de Google Sheets con quejas y comentarios de clientes, analizando cada entrada mediante **Google Gemini 2.5 Flash** para:

1. **Clasificar el departamento responsable**: `Ventas`, `Soporte Técnico` o `Logística`.
2. **Detectar el sentimiento**: `Positivo`, `Negativo` o `Neutro`.
3. **Actualizar automáticamente la base de datos** en Google Sheets con los resultados obtenidos.
4. **Ejecutarse de forma continua 24/7 en la nube** sin depender de una PC encendida ni de cron jobs externos.

---

## 🏗️ Arquitectura en la Nube (Railway)

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Railway (Nube)                               │
│                                                                       │
│   Variables de entorno (Railway Dashboard):                           │
│   ├── GEMINI_API_KEY      ──▶ API Key de Google Gemini                │
│   └── GOOGLE_TOKEN_JSON   ──▶ Token OAuth de Google Sheets            │
│                    │                      │                           │
│                    ▼                      ▼                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Servicio Railway: agente-soporte-ia                │  │
│  │                                                                 │  │
│  │   Imagen Docker (python:3.12-slim) construida desde Dockerfile  │  │
│  │   Directorio: /app  |  Restart automático ante fallos           │  │
│  │                                                                 │  │
│  │   ┌─────────────────────────────────────────────────────────┐   │  │
│  │   │                   agente_soporte.py                     │   │  │
│  │   │                                                         │   │  │
│  │   │  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │   │  │
│  │   │  │Google Sheets │◀─▶│  Bucle cada  │──▶│  Gemini    │  │   │  │
│  │   │  │  (gspread)   │   │  1 minuto    │   │ 2.5 Flash  │  │   │  │
│  │   │  └──────────────┘   └──────────────┘   └────────────┘  │   │  │
│  │   └─────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                         │                                             │
│              railway logs │ Registros en vivo                         │
│                         ▼                                             │
│                Terminal / Railway Dashboard                           │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Repositorio

```
DAI_Practica_Railway/
│
├── Dockerfile                        # Receta de construcción de la imagen Docker
├── railway.json                      # Configuración de despliegue en Railway
├── .dockerignore                     # Excluye credenciales y caché de la imagen
├── .gitignore                        # Protege archivos sensibles de Git
├── agente_soporte.py                 # Script principal del agente autónomo
├── requirements.txt                  # Dependencias de Python
├── Practica4_Agente_Railway.pdf      # Guía oficial de la Práctica 4
├── README.md                         # Documentación del proyecto
│
├── .github/
│   └── workflows/
│       └── agente.yml                # Workflow de GitHub Actions (Práctica 2)
│
├── docs/                             # Sitio web del proyecto (GitHub Pages)
│   ├── index.html
│   ├── privacidad.html
│   ├── terminos.html
│   └── style.css
│
├── .env.example                      # Plantilla pública de variables de entorno
│
├── .env                              # [PRIVADO] API Key de Gemini (ignorado por Git)
├── token.env                         # [PRIVADO] Token OAuth de Google (ignorado por Git)
└── client_secrets.json               # [PRIVADO] Credencial inicial de Google (ignorado)
```

---

## ⚙️ Configuración de Railway (`railway.json`)

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python agente_soporte.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### ¿Por qué Railway?
- **Sin servidor propio**: Railway gestiona la infraestructura completa (VM, red, escalado).
- **Deploy automático**: Cada `git push` a `main` redespliega el agente automáticamente.
- **Logs en vivo**: Visibles en el dashboard o con `railway logs` desde la terminal.
- **Reinicio automático**: Si el agente falla, Railway lo reinicia solo (hasta 10 intentos).
- **Variables seguras**: Las credenciales se gestionan como variables de entorno cifradas en el dashboard.

---

## 🔐 Seguridad y Protección de Secretos

El principio fundamental es que **ninguna credencial debe estar en el código ni en la imagen Docker**. Railway gestiona los secretos como variables de entorno cifradas que se inyectan en tiempo de ejecución.

### 1. `.gitignore` — Protege el repositorio
```text
.env
token.env
client_secrets.json
```

### 2. `.dockerignore` — Protege la imagen Docker
```text
.env
token.env
client_secrets.json
.git
__pycache__/
```

### 3. Variables de Entorno en Railway
Las credenciales se configuran **una sola vez** en el dashboard de Railway:

| Variable | Descripción |
|----------|-------------|
| `GEMINI_API_KEY` | API Key de Google Gemini AI Studio |
| `GOOGLE_TOKEN_JSON` | Token OAuth 2.0 de Google Sheets (JSON en una línea) |

---

## 🚀 Guía de Despliegue en Railway

### Requisitos Previos
- Cuenta en [railway.com](https://railway.com) (plan Trial con $5 USD gratuitos)
- [Node.js](https://nodejs.org/) instalado (para el CLI de Railway)
- Repositorio Git inicializado

### Paso 1 — Instalar el CLI de Railway
```bash
npm install -g @railway/cli
```

### Paso 2 — Autenticarse
```bash
railway login
```
Se abrirá el navegador para iniciar sesión con tu cuenta de Railway.

### Paso 3 — Crear el proyecto en Railway
```bash
railway init --name "agente-soporte-ia"
```

### Paso 4 — Configurar las variables de entorno
```bash
# Variable 1: API Key de Gemini
railway variables --set "GEMINI_API_KEY=tu_api_key_aqui"

# Variable 2: Token OAuth de Google (JSON en una sola línea)
railway variables --set 'GOOGLE_TOKEN_JSON={"refresh_token":"...","token_uri":"..."}'
```

> También puedes configurarlas visualmente en: `railway open` → Variables

### Paso 5 — Desplegar el agente
```bash
railway up
```
Railway construirá la imagen Docker y desplegará el agente en la nube.

### Paso 6 — Ver los logs en tiempo real
```bash
railway logs
```

### Paso 7 — Abrir el dashboard del proyecto
```bash
railway open
```

---

## 🖥️ Comandos Útiles del CLI

| Comando | Descripción |
|---------|-------------|
| `railway whoami` | Ver el usuario autenticado |
| `railway status` | Estado del proyecto vinculado |
| `railway up` | Desplegar el proyecto |
| `railway logs` | Ver logs en tiempo real |
| `railway open` | Abrir el dashboard en el navegador |
| `railway variables` | Listar variables de entorno |
| `railway variables --set "CLAVE=valor"` | Definir una variable |
| `railway project list` | Listar todos los proyectos |
| `railway down` | Detener el servicio |

---

## 📊 Matriz Comparativa: Evolución de las Prácticas

| Característica | Práctica 1 (Local) | Práctica 2 (GitHub Actions) | Práctica 3 (Docker) | Práctica 4 (Railway) |
|---|---|---|---|---|
| **Entorno de ejecución** | PC del desarrollador | Runner efímero en la nube | Contenedor en cualquier SO | Nube gestionada (Railway) |
| **Disponibilidad** | Solo con la PC encendida | Solo cuando dispara el cron | Mientras el host esté activo | 24/7 en la nube |
| **Instalación dependencias** | Manual con `pip` | En cada corrida del runner | Una vez en el `build` | Una vez en el `build` (Railway) |
| **Persistencia / Bucle** | Script activo en terminal | Tarea cron programada | Demonio continuo con `schedule` | Servicio continuo en la nube |
| **Gestión de credenciales** | Archivos `.env` y OAuth | GitHub Secrets cifrados | Inyección con `--env-file` | Variables de entorno en Railway |
| **Observabilidad** | Terminal abierta | Consola de GitHub Actions | `docker logs -f` | `railway logs` / Dashboard web |
| **Tolerancia a fallos** | Manual si se cierra | Se espera al siguiente cron | `--restart unless-stopped` | `restartPolicyType: ON_FAILURE` |
| **Costo de infraestructura** | Electricidad del host | Gratuito (límite de minutos) | Host o VPS externo | Trial $5 USD / mes desde ~$5 |

---

## 💡 Preguntas de Reflexión

1. **¿Qué ventaja ofrece Railway frente a ejecutar Docker localmente?**
   Railway gestiona toda la infraestructura: el servidor, la red, la disponibilidad y los reinicios automáticos. Con Docker local, si la PC se apaga o falla, el agente deja de funcionar. En Railway, el agente corre 24/7 sin ninguna intervención manual.

2. **¿Por qué no se sube `token.env` ni `.env` al repositorio?**
   Porque contienen credenciales privadas (API keys y tokens OAuth). Si se subieran a GitHub, cualquier persona con acceso al repositorio (incluso si es público) podría robar las claves y acceder a los servicios de Google y Gemini con nuestras cuotas y datos.

3. **¿Cómo gestiona Railway las actualizaciones del código?**
   Cada vez que se hace `railway up` o se conecta el repositorio de GitHub a Railway, la plataforma detecta los cambios, reconstruye la imagen Docker automáticamente y redespliega el servicio con cero tiempo de inactividad.

4. **¿Qué hace `restartPolicyType: ON_FAILURE` en `railway.json`?**
   Indica a Railway que si el proceso del agente termina con un código de error (crash), debe reiniciarlo automáticamente hasta un máximo de 10 intentos. Esto garantiza alta disponibilidad sin intervención manual.

5. **¿Cuándo conviene usar Railway vs. GitHub Actions?**
   - **GitHub Actions**: Ideal para tareas periódicas de baja frecuencia (cada 1-2 horas), sin costo de servidor, pero limitado a 6 horas por ejecución.
   - **Railway**: Ideal para agentes que deben estar siempre activos, con monitoreo de alta frecuencia (cada minuto o menos), sin depender de cron jobs externos ni tener una PC encendida.

6. **¿Qué pasa si el `GOOGLE_TOKEN_JSON` caduca en Railway?**
   El agente fallará al intentar conectarse a Google Sheets. Hay que renovar el token ejecutando el flujo OAuth localmente, copiar el nuevo JSON y actualizar la variable en Railway con `railway variables --set "GOOGLE_TOKEN_JSON={...nuevo token...}"`. Railway reiniciará el servicio automáticamente con el token actualizado.
