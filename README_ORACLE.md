# Guía de Despliegue en Oracle Cloud (Siempre Gratis)

Esta guía te guiará paso a paso para desplegar **todo el proyecto BiciTodo (Frontend y Backend unidos)** en un único servidor en la nube de **Oracle Cloud Infrastructure (OCI)** de forma 100% gratuita y activa las 24 horas.

---

## Paso 1: Crear la Instancia Gratis en Oracle Cloud

1. Inicia sesión en tu consola de [Oracle Cloud](https://cloud.oracle.com).
2. En la página de inicio del panel, haz clic en el botón **Create a VM instance** (o ve al menú lateral izquierdo > **Compute** > **Instances** > **Create Instance**).
3. Configura los siguientes campos:
   - **Name:** `bicitodo-server`
   - **Placement:** Deja el predeterminado.
   - **Image and Shape:**
     - **Image:** Haz clic en *Change Image* y selecciona **Ubuntu** (la versión por defecto, ej. `Ubuntu 22.04` o `Ubuntu 24.04`).
     - **Shape:** Deja el predeterminado de **Always Free Eligible** (puede ser el AMD `VM.Standard.E2.1.Micro` de 1 GB RAM, o el ARM `VM.Standard.A1.Flex` de hasta 4 cores y 24 GB de RAM si está disponible).
   - **Networking:** Deja la red predeterminada.
   - **Add SSH Keys:** 
     - Selecciona **Generate a key pair for me**.
     - Haz clic en **Save private key** (¡Súper importante! Descargarás un archivo `.key` o `.pem` a tu computadora. Este archivo es tu única llave de acceso al servidor).
   - **Boot volume:** Deja el predeterminado.
4. Haz clic en **Create** al final de la página. El servidor tardará un par de minutos en pasar al estado verde **Running**. Copia la **Public IP Address** que le sea asignada.

---

## Paso 2: Abrir el Puerto 80 en la Red de Oracle Cloud

Por defecto, Oracle Cloud bloquea todo el tráfico de internet a tu servidor excepto SSH. Debemos abrir el puerto 80 (HTTP) para que la gente pueda entrar a tu web:

1. En la página de detalles de tu instancia en Oracle Cloud, en la sección *Instance information*, haz clic en el enlace al lado de **Virtual cloud network** (tu red virtual).
2. Haz clic en **Security Lists** en el menú izquierdo de la red y luego en la lista predeterminada (Default Security List).
3. Haz clic en el botón azul **Add Ingress Rules** (Reglas de Entrada).
4. Configura la regla de la siguiente forma:
   - **Source Type:** `CIDR`
   - **Source CIDR:** `0.0.0.0/0` (significa todo el tráfico de internet)
   - **IP Protocol:** `TCP`
   - **Source Port Range:** (dejar vacío)
   - **Destination Port Range:** `80` (el puerto web estándar)
   - **Description:** `Permitir acceso web BiciTodo`
5. Haz clic en **Add Ingress Rules**.

---

## Paso 3: Conectarse por SSH desde tu Computadora

1. Abre tu terminal de Windows (PowerShell).
2. Navega con `cd` hasta la carpeta donde descargaste tu archivo de clave privada (por ejemplo, Descargas):
   ```powershell
   cd C:\Users\tu-usuario\Downloads
   ```
3. Conéctate a tu servidor usando el comando `ssh` con tu clave privada y la IP pública que copiaste en el Paso 1 (reemplaza `ip-del-servidor` con la tuya real):
   ```bash
   ssh -i ssh-key-2026-06-04.key ubuntu@ip-del-servidor
   ```
4. Si te pregunta si confías en el servidor, escribe `yes` y presiona Enter. ¡Ya estarás dentro de la terminal de Linux de tu servidor remoto!

---

## Paso 4: Abrir el Cortafuegos Interno de Ubuntu (Paso Crítico ⚠️)

Las máquinas virtuales de Ubuntu en Oracle Cloud traen un cortafuegos interno activo de fábrica que bloquea el puerto 80, incluso si lo abriste en el panel web. Ejecuta estos comandos en la terminal de tu servidor para desbloquearlo:

```bash
# 1. Permitir tráfico de entrada en el puerto 80
sudo iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT

# 2. Guardar las reglas del cortafuegos para que no se borren al reiniciar
sudo netfilter-persistent save
```

---

## Paso 5: Instalar Dependencias y Clonar el Código

Ejecuta estos comandos en la terminal de tu servidor de Oracle Cloud:

```bash
# 1. Actualizar el sistema e instalar Python3, entorno virtual y Git
sudo apt update && sudo apt install git python3-pip python3-venv -y

# 2. Clonar tu repositorio de GitHub directamente en el servidor
git clone https://github.com/Breadd-byte/bicitodo.git

# 3. Entrar a la carpeta del proyecto
cd bicitodo

# 4. Crear un entorno virtual de Python
python3 -m venv venv

# 5. Activar el entorno virtual
source venv/bin/activate

# 6. Instalar las dependencias de BiciTodo
pip install -r backend/requirements.txt
```

---

## Paso 6: Ejecutar la Web en Segundo Plano (Siempre Activa)

Para que tu aplicación no se apague al cerrar la terminal de tu computadora, la configuraremos como un servicio del sistema Linux:

1. Crea el archivo de servicio con el editor nano:
   ```bash
   sudo nano /etc/systemd/system/bicitodo.service
   ```
2. Pega el siguiente contenido completo (asegúrate de que las rutas coincidan con tu usuario, el cual por defecto es `/home/ubuntu`):
   ```ini
   [Unit]
   Description=BiciTodo API y Frontend Unificados
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/home/ubuntu/bicitodo
   ExecStart=/home/ubuntu/bicitodo/venv/bin/uvicorn backend.api:app --host 0.0.0.0 --port 80
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Guarda el archivo presionando `Ctrl + O`, luego Enter, y sal presionando `Ctrl + X`.
4. Inicia y activa el servicio para que corra siempre y arranque automáticamente si el servidor se reinicia:
   ```bash
   sudo systemctl daemon-reload
   ```
   ```bash
   sudo systemctl start bicitodo
   ```
   ```bash
   sudo systemctl enable bicitodo
   ```

¡Felicidades! En este momento, cualquier persona en el mundo puede entrar a tu comparador de ciclismo simplemente escribiendo la **IP pública de tu servidor de Oracle Cloud** en el navegador.

---

## Paso 7: Configurar el Scraper Diario Nocturno

Para que los precios se actualicen de forma totalmente automática todas las noches:

1. Abre las tareas programadas (cron jobs) de root:
   ```bash
   sudo crontab -e
   ```
2. Si te pregunta qué editor usar, presiona `1` (para nano).
3. Desplázate al final del archivo y agrega esta línea (refrescará los precios existentes todas las noches a las 3:00 AM, hará backup automático de la base y guardará un registro de actividad en `price_refresh.log`):
   ```text
   0 3 * * * cd /home/ubuntu/bicitodo && /home/ubuntu/bicitodo/venv/bin/python /home/ubuntu/bicitodo/backend/refresh_existing_prices.py --only-stale-days 1 >> /home/ubuntu/bicitodo/backend/price_refresh.log 2>&1
   ```
4. Guarda el archivo presionando `Ctrl + O`, luego Enter, y sal con `Ctrl + X`.
