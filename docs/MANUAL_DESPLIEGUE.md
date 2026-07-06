# Manual de Despliegue en la Nube

Proyecto: Detector de Spam / Clasificador de Texto
Fase 2 — Gestión de Proyectos de Inteligencia Artificial

## 1. Requerimientos técnicos

### 1.1 Para desarrollo y ejecución local

- Python 3.11+
- Docker Desktop (o Docker Engine + Docker Compose) 24+
- Git
- 1 GB de espacio libre en disco aproximadamente (imagen + dependencias)
- Puerto `8000` disponible en `localhost`

### 1.2 Para el despliegue en la nube

- Cuenta en [Render](https://render.com) (capa gratuita es suficiente)
- Repositorio en GitHub con este proyecto (público o privado)
- El repositorio debe contener, en la raíz: `Dockerfile`, `requirements.txt`, `app/`, `model/`, `frontend/`

## 2. Estrategia de despliegue

### 2.1 Opciones consideradas

| Estrategia | Ejemplos | Ventajas | Desventajas para este proyecto |
|---|---|---|---|
| **PaaS sobre contenedores** (elegida) | Render, Railway | Despliegue directo desde `Dockerfile`, HTTPS y dominio gratis, sin gestionar servidores, capa gratuita | Menor control de infraestructura de bajo nivel |
| IaaS / VM | AWS EC2, GCP Compute Engine | Control total del servidor | Requiere administrar SO, parches, escalado manual; mayor curva y costo operativo para un proyecto académico |
| Contenedores gestionados (serverless) | AWS ECS/Fargate, Google Cloud Run | Escalado automático a cero, muy usado en producción real | Más pasos de configuración (registry, IAM, VPC) para un mismo resultado funcional |
| PaaS nativo (sin Docker) | Heroku, Render (runtime nativo) | Muy simple | No ejercita explícitamente la competencia de "contenerización" pedida en la rúbrica |

### 2.2 Decisión

Se eligió **Render como PaaS basado en contenedores** porque: despliega
directamente a partir del `Dockerfile` del repositorio (mismo artefacto
validado en local, sin reescribir nada para la nube); ofrece HTTPS,
dominio público y CI/CD (redeploy automático en cada `git push`) sin costo
para un proyecto académico; y mantiene consistencia entre entorno local y
de nube (principio de portabilidad exigido por la rúbrica).

> El mismo `Dockerfile` de este repositorio es compatible, sin cambios,
> con Google Cloud Run, AWS App Runner/ECS Fargate o Azure Container Apps,
> ya que todos aceptan una imagen OCI estándar. La sección 5 incluye notas
> de cómo migrar a esas alternativas.

## 3. Proceso paso a paso (Render)

### Paso 0 — Subir el repositorio a GitHub

```bash
git init
git add .
git commit -m "Fase 2: contenerización, API e integración frontend/backend"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/spam-classifier.git
git push -u origin main
```

### Paso 1 — Crear cuenta y conectar el repositorio

1. Entra a [dashboard.render.com](https://dashboard.render.com) y crea una cuenta (puedes usar tu cuenta de GitHub).
2. Autoriza a Render a acceder a tu cuenta/repositorios de GitHub.

### Paso 2 — Crear el Web Service

1. Clic en **New** → **Web Service**.
2. Selecciona el repositorio `spam-classifier`.
3. En el formulario de configuración:
   - **Name**: `spam-classifier` (o el nombre que prefieras; define tu subdominio `https://<name>.onrender.com`).
   - **Region**: la más cercana a tus usuarios.
   - **Branch**: `main`.
   - **Language / Runtime**: selecciona **Docker** (Render detecta el `Dockerfile` automáticamente).
   - **Dockerfile Path**: `./Dockerfile` (ya es el valor por defecto).
4. **Instance Type**: `Free`.
5. En **Advanced**:
   - **Health Check Path**: `/api/health`
   - Variables de entorno opcionales (no son obligatorias; `PORT` la gestiona Render automáticamente).
6. Clic en **Create Web Service**.

### Paso 3 — Build y despliegue

Render ejecuta automáticamente (usando BuildKit):

```bash
docker build -t <interno> .     # incluye "RUN python -m model.train"
# y luego levanta el contenedor equivalente a:
docker run -p $PORT:$PORT <interno>
```

El progreso se observa en la pestaña **Events**/**Logs** del servicio. El
primer build tarda unos minutos (instalación de scikit-learn/pandas +
entrenamiento del modelo). Al finalizar, el servicio queda disponible en
`https://<name>.onrender.com`.

### Paso 4 — Verificar el despliegue

```bash
curl https://<name>.onrender.com/api/health

curl -X POST https://<name>.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Felicidades, ganaste un premio, reclama en http://bit.ly/premio"}'
```

Y abre `https://<name>.onrender.com/` en el navegador para probar el
frontend, y `https://<name>.onrender.com/docs` para la documentación
interactiva (Swagger UI) de la API.

### Paso 5 — Redeploys posteriores

Cada `git push` a la rama `main` dispara automáticamente un nuevo build y
despliegue sin downtime (*zero-downtime deploys*). También puede
redesplegarse manualmente desde el botón **Manual Deploy** en el dashboard.

### Alternativa: despliegue por Blueprint (IaC)

Este repositorio incluye `render.yaml`. En lugar del Paso 2, puede usarse
**New → Blueprint**, seleccionar el repositorio y Render leerá `render.yaml`
para crear el servicio automáticamente con la configuración ya definida
(incluye `healthCheckPath`). Es el equivalente "como código" del proceso
manual, útil para reproducibilidad.

## 4. Ejecución local (previa al despliegue)

```bash
# Opción A: Docker directo
docker build -t spam-detector:local .
docker run --rm -p 8000:8000 --name spam-detector spam-detector:local

# Opción B: Docker Compose
docker compose up --build
```

Verificar:

```bash
curl http://localhost:8000/api/health
open http://localhost:8000        # o visita la URL en el navegador
```

Detener:

```bash
docker stop spam-detector    # opción A
docker compose down          # opción B
```

## 5. Notas de portabilidad a otras nubes

El `Dockerfile` no usa nada específico de Render, por lo que la misma
imagen puede desplegarse en:

- **Google Cloud Run**: `gcloud run deploy --source .` (Cloud Run detecta el Dockerfile y respeta la variable `PORT` igual que Render).
- **AWS App Runner**: conectar el repo o una imagen en Amazon ECR; App Runner también inyecta `PORT`.
- **Azure Container Apps**: `az containerapp up --source .`.

En todos los casos, el contrato es el mismo: la aplicación debe escuchar en
`0.0.0.0:$PORT`, lo cual ya está implementado en este proyecto (ver
`Dockerfile`, `CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT`).

## 6. Uso de herramientas de documentación e IA

Este proyecto (código, Dockerfile, pruebas y la documentación de las
fases 1-4 de esta rúbrica) se desarrolló con asistencia de **Claude**
(Anthropic), usado como copiloto de desarrollo de forma análoga a
herramientas como GitHub Copilot: generación y revisión de boilerplate
(esquemas Pydantic, endpoints FastAPI, Dockerfile), redacción de casos de
prueba y primer borrador de esta documentación técnica. Todo el código
generado fue revisado, ejecutado/verificado y ajustado manualmente antes
de incluirse en el repositorio; las decisiones de arquitectura (elección
de Render como PaaS, entrenamiento del modelo durante el build de Docker,
diseño de la API) están explicadas y justificadas en este documento y en
`README.md`.

Recomendación si continúas este proyecto: usar **GitHub Copilot** (o
Claude vía su extensión de IDE) directamente en tu editor para iterar
sobre `app/`, `model/` y `tests/`, y para mantener esta documentación
sincronizada cuando el código cambie.
