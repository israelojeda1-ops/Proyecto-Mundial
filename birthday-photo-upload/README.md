# 📸 Fotos del cumple → Google Drive

Web sencilla para que los invitados suban fotos/videos desde el celular y queden
guardados automáticamente en una carpeta de tu Google Drive.

## Cómo funciona

- `public/index.html`: formulario mobile-friendly (nombre + foto/video).
- `server.js`: recibe el archivo y lo sube a la carpeta de Drive que elijas, usando
  una **cuenta de servicio de Google** (no requiere que cada invitado inicie sesión).

## 1. Crear la cuenta de servicio de Google (una sola vez, ~5 min)

1. Entra a https://console.cloud.google.com/ y crea un proyecto (o usa uno existente).
2. Ve a **APIs & Services → Library**, busca "Google Drive API" y actívala.
3. Ve a **APIs & Services → Credentials → Create Credentials → Service Account**.
   - Dale cualquier nombre, ej. `fotos-cumple`.
   - No necesita roles de proyecto, puedes omitir ese paso.
4. Abre la cuenta de servicio creada → pestaña **Keys → Add Key → Create new key → JSON**.
   Se descarga un archivo `.json`.
5. Copia el email de la cuenta de servicio (algo como
   `fotos-cumple@tu-proyecto.iam.gserviceaccount.com`).

## 2. Compartir la carpeta de Drive

1. En tu Google Drive, crea (o elige) la carpeta donde quieres que caigan las fotos.
2. Click derecho → **Compartir** → agrega el email de la cuenta de servicio (paso 1.5)
   con permiso de **Editor**.
3. Copia el ID de la carpeta desde la URL:
   `https://drive.google.com/drive/folders/ESTE_ES_EL_ID`

## 3. Configurar las variables de entorno

```bash
cp .env.example .env
```

Edita `.env`:

- `GOOGLE_SERVICE_ACCOUNT_KEY`: pega el **contenido completo** del JSON descargado
  (todo en una línea).
- `DRIVE_FOLDER_ID`: el ID de la carpeta del paso 2.
- `EVENT_PIN` (opcional): un PIN corto si quieres evitar que gente ajena al link suba fotos.

## 4. Ejecutar

```bash
npm install
npm start
```

Abre http://localhost:3000 para probarlo.

## 5. Compartir el link con los invitados HOY MISMO

La forma más rápida sin desplegar nada: usa un túnel temporal desde tu laptop.

```bash
npx localtunnel --port 3000
# o, si tienes ngrok instalado:
ngrok http 3000
```

Te dará una URL pública (ej. `https://algo.loca.lt`). Compártela por WhatsApp o
genera un QR con esa URL para poner en las mesas.

### Opción permanente (para futuras fiestas)

Puedes desplegar esta carpeta en **Render** o **Railway** (ambos tienen plan gratuito):

1. Sube este repo a GitHub (ya está listo aquí).
2. En Render/Railway: "New Web Service" → conecta el repo →
   Root directory: `birthday-photo-upload` → Build: `npm install` → Start: `npm start`.
3. Agrega las mismas variables de entorno del paso 3 en el panel del servicio.
4. Te dan una URL pública fija.

## Notas

- Límite de archivo: 25 MB por foto/video (configurable en `server.js`).
- Las fotos se guardan con el nombre `NombreInvitado - fecha.ext`.
- El PIN es opcional y solo protege contra gente fuera del link; no es un login real.
