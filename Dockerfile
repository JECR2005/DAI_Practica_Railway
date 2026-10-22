# Imagen base: Linux mínimo con Python 3.12
FROM python:3.12-slim

# Evita el almacenamiento en búfer de Python para ver los logs en tiempo real
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias sin guardar archivos temporales
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del agente
COPY agente_soporte.py .

# Comando de inicio del contenedor
ENTRYPOINT ["python", "agente_soporte.py"]
