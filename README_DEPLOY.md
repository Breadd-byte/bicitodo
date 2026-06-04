# Guía de Despliegue Oficial de BiciTodo

Esta guía detalla los pasos para realizar la limpieza de tu repositorio de Git (para evitar el error **"Timed out"** en Render) y configurar los despliegues de producción.

---

## 📋 Requisitos Previos

1. Una cuenta de [GitHub](https://github.com) con tu repositorio de BiciTodo sincronizado.
2. Una cuenta en [Supabase](https://supabase.com) (gratuita).
3. Una cuenta en [Render](https://render.com) (gratuita).
4. Una cuenta en [Cloudflare](https://dash.cloudflare.com) (gratuita).

---

## Paso 1: Limpieza Crucial de Archivos Pesados en Git (Local)

El error **"Timed out"** en Render ocurre porque tu repositorio de Git actualmente tiene registradas miles de imágenes locales y copias de base de datos `.db` pesadas. 

Ejecuta los siguientes comandos en la terminal de tu computadora en la raíz de tu proyecto para quitar esos archivos de la historia de Git **sin borrarlos de tu computadora**:

```bash
# 1. Quitar las imágenes descargadas por el scraper del rastreo de Git
git rm -r --cached fronted/assets/bikes/

# 2. Quitar las bases de datos de respaldo y local del rastreo de Git
git rm --cached backend/database/*.db

# 3. Guardar los cambios en un commit
git commit -m "chore: eliminar imágenes y bases de datos locales del rastreo de Git"

# 4. Enviar los cambios a tu repositorio de GitHub
git push origin main
```

*Nota: Gracias al archivo `.gitignore` ya modificado, en adelante Git ignorará estos archivos y nunca más intentará subirlos.*

---

## Paso 2: Configuración de Base de Datos en Supabase (Gratis)

1. Regístrate en [Supabase.com](https://supabase.com).
2. Crea un nuevo proyecto llamado `bicitodo-db`.
3. Ve a la pestaña **SQL Editor** (`>_`) en la barra lateral izquierda.
4. Si ves una consulta predeterminada llamada **Welcome**, selecciónala, bórrala y pega el contenido de [backend/database/schema_supabase.sql](file:///c:/Users/basti/Downloads/bicitodo-main/bicitodo-main/backend/database/schema_supabase.sql).
5. Haz clic en **Run** (botón verde abajo a la derecha) para crear la tabla de alertas.
6. Ve a **Project Settings** (el icono de engranaje) > **API** y copia:
   - **Project URL**
   - **anon public API key**

---

## Paso 3: Despliegue del Backend en Render

1. Ve a [Render.com](https://render.com).
2. Haz clic en **New +** > **Web Service** y conecta tu repositorio `Breadd-byte/bicitodo`.
3. Configura los siguientes parámetros exactos:
   - **Name:** `bicitodo-api`
   - **Language:** `Python 3`
   - **Region:** La más cercana (ej. Oregon u Ohio)
   - **Branch:** `main`
   - **Root Directory:** `backend` *(¡Muy importante! Indica a Render que trabaje solo con la subcarpeta del backend)*
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Abre la sección **Advanced** y añade las siguientes Variables de Entorno:
   - `SUPABASE_URL` = (La URL de tu proyecto de Supabase)
   - `SUPABASE_KEY` = (La clave "anon public" de Supabase)
5. Haz clic en **Create Web Service**. Espera a que termine de compilar y copia la URL que te genera (ej. `https://bicitodo-api.onrender.com`).

---

## Paso 4: Configuración del Frontend en Cloudflare Pages

1. Abre tu archivo local [fronted/config.js](file:///c:/Users/basti/Downloads/bicitodo-main/bicitodo-main/fronted/config.js).
2. Cambia la URL para que apunte a tu nuevo backend de Render:
   ```javascript
   window.API_BASE_URL = "https://tu-backend-api.onrender.com"; // URL de la Fase 3
   ```
3. Guarda los cambios, realiza un commit y súbelo a GitHub:
   ```bash
   git add fronted/config.js
   git commit -m "config: actualizar URL del backend para producción"
   git push origin main
   ```
4. Inicia sesión en el panel de [Cloudflare](https://dash.cloudflare.com).
5. En la barra lateral, ve a **Workers & Pages** > **Pages** > **Connect to Git**.
6. Selecciona tu repositorio `bicitodo`.
7. En la configuración del despliegue:
   - **Framework preset:** `None`
   - **Build command:** (dejar completamente vacío)
   - **Build output directory:** `fronted` *(¡Muy importante! Indica a Cloudflare que sirva solo esta carpeta)*
8. Haz clic en **Save and Deploy**. En segundos, Cloudflare publicará tu frontend con un dominio seguro gratuito.

---

## Paso 5: Automatización del Scraper Diario de Precios

Para mantener los precios al día de forma gratuita sin saturar tu servidor en Render, puedes usar **GitHub Actions**:

1. En la raíz de tu proyecto local, crea la carpeta `.github/workflows/` (si no existe).
2. Crea un archivo llamado `scraper.yml` y pega el siguiente contenido:
   ```yaml
   name: Bicitodo Daily Scraper

   on:
     schedule:
       - cron: '0 6 * * *' # Ejecuta todos los días a las 2:00 AM hora de Chile
     workflow_dispatch:

   jobs:
     scrape:
       runs-on: ubuntu-latest
       steps:
         - name: Check out repo
           uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.10'

         - name: Install dependencies
           run: |
             pip install -r backend/requirements.txt
             pip install cloudscraper beautifulsoup4 lxml

         - name: Run Scraper
           run: |
             python backend/fast_scraper.py

         - name: Commit and Push changes
           run: |
             git config --global user.name "Bicitodo Scraper Bot"
             git config --global user.email "bot@bicitodo.cl"
             git add fronted/data.json
             git commit -m "Auto-update prices via scraper" || exit 0
             git push
   ```
3. Sube este archivo a GitHub. Desde la pestaña **Actions** en tu repositorio de GitHub podrás correr el scraper manualmente cuando quieras o dejarlo correr de forma automática cada noche.
