# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL maintainer="kwin" \
      description="Detector de Spam / Clasificador de texto - Fase 2 Gestion de Proyectos de IA"

WORKDIR /app

# Evita .pyc y fuerza salida sin buffer (logs visibles en tiempo real)
# PORT=8000 es el valor por defecto para uso local; Render (y la mayoría
# de los PaaS) inyectan su propia variable PORT en tiempo de ejecución
# (Render usa 10000 por defecto), que sobreescribe este valor automáticamente.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# 1) Dependencias primero -> aprovecha la cache de capas de Docker:
#    si solo cambia el código, esta capa no se reconstruye.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Código fuente de la aplicación
COPY app ./app
COPY model ./model
COPY frontend ./frontend

# 3) Entrena el modelo DURANTE el build. Esto hace que la imagen sea
#    autocontenida y reproducible: cualquiera que construya esta imagen
#    obtiene el mismo modelo entrenado a partir de model/data/spam.csv,
#    sin depender de archivos binarios versionados en git.
RUN python -m model.train

# 4) Buenas practicas de seguridad: no correr como root
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT','8000') + '/api/health')" || exit 1

# Forma shell (no exec-form) para que $PORT se resuelva en tiempo de
# ejecucion: local -> 8000 (por defecto); Render/otro PaaS -> el puerto
# que la plataforma inyecte como variable de entorno.
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
