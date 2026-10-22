# ============================================================
#  agente_soporte.py
#  Practica 2: Agente de Soporte con GitHub Actions
#  Construccion de un Agente de Soporte con Python y Gemini
# ============================================================

# ---------------------
# PASO 4.2 - Importaciones
# ---------------------
import json
import os
import sys
import time

import schedule
import gspread
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Carga las variables definidas en el archivo .env
load_dotenv()

# ---------------------
# PASO 4.3 - Configuracion
# ---------------------

# Nombre del archivo de credenciales OAuth 2.0
ARCHIVO_CREDENCIALES = "client_secrets.json"

# Nombre de la hoja de calculo en Google Sheets
NOMBRE_HOJA = "Respuestas de Quejas (Base de Datos)"

# API Key de Gemini leida desde el archivo .env (nunca hardcodeada en el codigo)
# https://aistudio.google.com/app/api-keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Cada cuantos minutos el agente revisara si hay nuevas quejas
INTERVALO_MINUTOS = 1

# Indices de columna en Google Sheets (basado en 1)
COL_CLASIFICACION = 4   # Columna D
COL_SENTIMIENTO   = 5   # Columna E
COL_EJECUTADO     = 6   # Columna F

# Scopes de Google necesarios para leer/escribir en Sheets
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Variable global para el cliente de Gemini
cliente_gemini = None


# ---------------------
# PASO 4.4 - Funcion: Conectar con Google Sheets
# ---------------------
def conectar_sheets():
    """
    Autentica el script con Google usando OAuth 2.0 y retorna
    la primera hoja de la hoja de calculo configurada en NOMBRE_HOJA.

    En GitHub Actions: usa la variable de entorno GOOGLE_TOKEN_JSON.
    En local: usa el flujo OAuth normal con client_secrets.json.
    """
    # --- Fase 1.2: Modo nube (GitHub Actions) ---
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json:
        token_dict = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
        # Renovar el token si esta vencido (usa el refresh_token almacenado)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        cliente_sheets = gspread.authorize(creds)
        hoja_calculo = cliente_sheets.open(NOMBRE_HOJA)
        return hoja_calculo.sheet1

    # --- Modo local: inicio de sesion con navegador ---
    cliente_sheets = gspread.oauth(credentials_filename=ARCHIVO_CREDENCIALES)
    hoja_calculo = cliente_sheets.open(NOMBRE_HOJA)
    return hoja_calculo.sheet1


# ---------------------
# PASO 4.5 - Funcion: Analizar con Gemini
# ---------------------
def analizar_con_gemini(comentario: str) -> dict:
    """
    Envia el comentario a la API de Gemini y retorna un diccionario con:
        - 'clasificacion': 'Ventas' | 'Soporte Tecnico' | 'Logistica'
        - 'sentimiento':   'Positivo' | 'Negativo' | 'Neutro'
    """
    instruccion_sistema = (
        "Eres un analista experto de soporte al cliente. "
        "Tu unica tarea es analizar el comentario recibido y devolver "
        "una respuesta EXCLUSIVAMENTE en formato JSON puro, sin texto adicional, "
        "sin explicaciones y sin bloques de codigo markdown. "
        "El JSON debe contener exactamente dos claves: "
        "\"clasificacion\" (valores posibles: \"Ventas\", \"Soporte Tecnico\" o \"Logistica\") "
        "y \"sentimiento\" (valores posibles: \"Positivo\", \"Negativo\" o \"Neutro\")."
    )

    instruccion_usuario = (
        f"Clasifica el siguiente comentario de un cliente y detecta su sentimiento:\n\n"
        f"\"{comentario}\""
    )

    respuesta = cliente_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=instruccion_usuario,
        config=types.GenerateContentConfig(
            system_instruction=instruccion_sistema
        )
    )

    texto = respuesta.text.strip()
    texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    return json.loads(texto)


# ---------------------
# PASO 4.6 - Funcion: Agente Principal
# ---------------------
def ejecutar_agente():
    """
    Orquesta el ciclo completo del agente:
      1. Conectar con Google Sheets.
      2. Leer todas las filas.
      3. Filtrar las filas no procesadas (columna F vacia).
      4. Analizar cada fila con Gemini.
      5. Escribir los resultados en las columnas D, E y F.

    Retorna True si el ciclo termino correctamente, False si hubo error de conexion.
    """
    print("\n" + "=" * 55)
    print("  Agente de Soporte iniciando ciclo de revision...")
    print("=" * 55)

    try:
        hoja = conectar_sheets()
        print("Conexion con Google Sheets establecida.")
    except Exception as error_conexion:
        print(f"Error al conectar con Google Sheets: {error_conexion}")
        return False

    todas_las_filas = hoja.get_all_values()
    filas_de_datos = todas_las_filas[1:]

    if not filas_de_datos:
        print("No hay filas de datos en la hoja.")
        return True

    filas_nuevas = 0

    for indice, fila in enumerate(filas_de_datos, start=2):
        valor_ejecutado = fila[5] if len(fila) > 5 else ""
        if valor_ejecutado.strip().upper() == "SI":
            continue

        nombre_cliente = fila[1] if len(fila) > 1 else "(sin nombre)"
        comentario     = fila[2] if len(fila) > 2 else ""

        if not comentario.strip():
            print(f"Fila {indice}: comentario vacio, omitiendo.")
            continue

        print(f"\nProcesando fila {indice} - Cliente: {nombre_cliente}")
        print(f"Comentario: {comentario[:80]}")

        try:
            resultado = analizar_con_gemini(comentario)
            clasificacion = resultado.get("clasificacion", "Desconocida")
            sentimiento   = resultado.get("sentimiento",   "Desconocido")
            print(f"Clasificacion: {clasificacion}")
            print(f"Sentimiento:   {sentimiento}")
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError en fila {indice}: {e}. Continuando...")
            continue
        except Exception as e:
            print(f"Error al analizar fila {indice} con Gemini: {e}. Continuando...")
            continue

        try:
            hoja.update_cell(indice, COL_CLASIFICACION, clasificacion)
            hoja.update_cell(indice, COL_SENTIMIENTO,   sentimiento)
            hoja.update_cell(indice, COL_EJECUTADO,     "SI")
            print(f"Resultados escritos en Google Sheets (fila {indice}).")
            filas_nuevas += 1
        except Exception as e:
            print(f"Error al escribir en Google Sheets (fila {indice}): {e}")

    if filas_nuevas == 0:
        print("\nNo se encontraron filas nuevas para procesar.")
    else:
        print(f"\nCiclo completado. Se procesaron {filas_nuevas} fila(s) nueva(s).")

    return True


# ---------------------
# PASO 4.7 - Punto de Entrada del Script
# ---------------------
if __name__ == "__main__":

    # Validar la API Key de Gemini siempre
    if not GEMINI_API_KEY:
        print(
            "ERROR: No se encontro la variable GEMINI_API_KEY.\n"
            "Crea un archivo .env en esta carpeta con el contenido:\n"
            "  GEMINI_API_KEY=tu_api_key_aqui\n"
            "Obten tu clave en: https://aistudio.google.com/app/api-keys"
        )
        exit(1)

    # Fase 1.4: Validar client_secrets.json solo si NO estamos en modo nube
    google_token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if not google_token_json and not os.path.exists(ARCHIVO_CREDENCIALES):
        print(
            f"ERROR: No se encontro el archivo {ARCHIVO_CREDENCIALES}.\n"
            f"Asegurate de colocarlo en la misma carpeta que este script.\n"
            "Descargalo desde Google Cloud Console > APIs y servicios > Credenciales."
        )
        exit(1)

    cliente_gemini = genai.Client(api_key=GEMINI_API_KEY)
    print("Cliente de Gemini inicializado correctamente.")

    # Fase 1.3: Modo --una-vez para GitHub Actions
    if "--una-vez" in sys.argv:
        print("\nModo: una sola ejecucion (--una-vez)")
        print(f"Hoja de calculo: {NOMBRE_HOJA}")
        exito = ejecutar_agente()
        exit(0 if exito else 1)

    # Modo normal: bucle infinito (Practica 1)
    print(f"\nAgente de Soporte arrancando...")
    print(f"Hoja de calculo: {NOMBRE_HOJA}")
    print(f"Intervalo: cada {INTERVALO_MINUTOS} minutos")

    ejecutar_agente()

    schedule.every(INTERVALO_MINUTOS).minutes.do(ejecutar_agente)

    print("\nAgente en modo continuo. Presiona Ctrl+C para detener.")
    while True:
        schedule.run_pending()
        time.sleep(30)
