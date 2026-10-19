# Queens — preparación para publicación web

Esta carpeta es una copia independiente de los archivos necesarios para publicar
el cliente Flutter web y conservar junto a él el código de su API. No incluye
Android, compilaciones existentes, entornos virtuales ni cachés.

## Contenido

- `lib/`, `web/`, `pubspec.yaml` y `pubspec.lock`: código y recursos del cliente
  Flutter web.
- `build.sh` y `vercel.json`: compilación de Flutter web para Vercel. Si Flutter
  no está instalado en el entorno, el script descarga el canal estable.
- `backend/`: código FastAPI y sus dependencias. El cliente necesita una API
  pública para crear partidas y consultar récords.
- `.gitignore`: excluye artefactos de compilación, cachés y archivos locales.

## Publicar en GitHub

Si vas a subir el repositorio actual, incluye esta carpeta en el commit:

```bash
git add app_web
git commit -m "Prepare standalone web app"
git push
```

Si prefieres un repositorio separado, copia el contenido de `app_web` como raíz
de ese repositorio. Publica el código fuente y los archivos de configuración;
`build/web/` se genera durante la compilación y no es necesario subirlo.

## Publicar el frontend en Vercel

1. Importa el repositorio en Vercel.
2. Selecciona `app_web` como **Root Directory**.
3. Configura la variable de entorno `API_BASE_URL` con la URL HTTPS pública de
   la API, por ejemplo `https://mi-api.example.com`. Añádela a los entornos de
   Preview y Production que vayas a utilizar.
4. Vercel usará `build.sh` y publicará `build/web` según `vercel.json`.

`API_BASE_URL` se incorpora al cliente compilado y no es un secreto: no pongas
credenciales ni claves privadas en esa variable.

Para compilar manualmente con Flutter instalado:

```bash
flutter pub get
flutter build web --release --dart-define="API_BASE_URL=https://mi-api.example.com"
```

## API backend

Vercel sirve aquí el frontend estático; no despliega automáticamente el
directorio `backend/`. Aloja esa API por separado en un servicio compatible con
FastAPI y configura `API_BASE_URL` con su URL pública. Desde la raíz de
`app_web`, el comando de inicio habitual en un servicio Linux es:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

El backend actual guarda el marcador en `backend/scoreboard.json` y mantiene las
partidas en memoria. Antes de alojarlo en producción, el servicio debe ofrecer
almacenamiento persistente para los récords; una plataforma serverless con disco
efímero no preservará esos datos entre reinicios.

Incluye el código Flutter y sus recursos web en lib/ y web/, las dependencias en pubspec.yaml y pubspec.lock, y la API FastAPI con sus dependencias en backend/. Añadí README.md, vercel.json, build.sh y .gitignore para documentar y preparar la publicación. No incluí compilaciones Android, cachés ni entornos virtuales.

Para GitHub: desde la raíz del repositorio, puedes preparar solo esta carpeta con git add app_web y luego hacer commit y push. Si quieres un repositorio separado, usa el contenido de app_web como su raíz.

Para Vercel: importa el repositorio, selecciona app_web como Root Directory y configura API_BASE_URL con la URL HTTPS pública de tu API. Vercel usará la configuración para compilar Flutter y publicar build/web. El backend debe alojarse por separado; tal como está, guarda récords en un archivo local y partidas en memoria, por lo que necesita almacenamiento persistente para producción.

Verifiqué que la compilación web termina correctamente y que los archivos de salida están presentes. No publiqué ni desplegué el proyecto. Las modificaciones que ya existían fuera de app_web quedaron intactas