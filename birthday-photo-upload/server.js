require('dotenv').config();
const express = require('express');
const multer = require('multer');
const { google } = require('googleapis');
const path = require('path');
const stream = require('stream');

const PORT = process.env.PORT || 3000;
const DRIVE_FOLDER_ID = process.env.DRIVE_FOLDER_ID;
const EVENT_PIN = process.env.EVENT_PIN || '';

if (!DRIVE_FOLDER_ID) {
  console.error('Falta DRIVE_FOLDER_ID en las variables de entorno. Revisa el README.');
  process.exit(1);
}

function loadServiceAccountCredentials() {
  if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
    return JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_KEY);
  }
  if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    return require(path.resolve(process.env.GOOGLE_APPLICATION_CREDENTIALS));
  }
  throw new Error(
    'Falta GOOGLE_SERVICE_ACCOUNT_KEY o GOOGLE_APPLICATION_CREDENTIALS en las variables de entorno.'
  );
}

const auth = new google.auth.GoogleAuth({
  credentials: loadServiceAccountCredentials(),
  scopes: ['https://www.googleapis.com/auth/drive'],
});
const drive = google.drive({ version: 'v3', auth });

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/') || file.mimetype.startsWith('video/')) {
      cb(null, true);
    } else {
      cb(new Error('Solo se permiten fotos o videos'));
    }
  },
});

const app = express();
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

app.get('/api/config', (req, res) => {
  res.json({ pinRequired: Boolean(EVENT_PIN) });
});

app.post('/api/upload', upload.single('photo'), async (req, res) => {
  try {
    if (EVENT_PIN && req.body.pin !== EVENT_PIN) {
      return res.status(401).json({ error: 'PIN incorrecto' });
    }
    if (!req.file) {
      return res.status(400).json({ error: 'No se recibio ningun archivo' });
    }

    const guestName = (req.body.guestName || 'Invitado').trim().slice(0, 60);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const safeName = guestName.replace(/[^a-zA-Z0-9 _-]/g, '') || 'Invitado';
    const extension = path.extname(req.file.originalname) || '';
    const fileName = `${safeName} - ${timestamp}${extension}`;

    const bufferStream = new stream.PassThrough();
    bufferStream.end(req.file.buffer);

    const driveResponse = await drive.files.create({
      requestBody: {
        name: fileName,
        parents: [DRIVE_FOLDER_ID],
      },
      media: {
        mimeType: req.file.mimetype,
        body: bufferStream,
      },
      fields: 'id, name',
    });

    res.json({ ok: true, fileId: driveResponse.data.id, fileName: driveResponse.data.name });
  } catch (err) {
    console.error('Error subiendo a Drive:', err);
    res.status(500).json({ error: 'No se pudo subir la foto. Intenta de nuevo.' });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor listo en http://localhost:${PORT}`);
});
