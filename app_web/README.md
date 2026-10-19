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
3. Primero despliega el backend en un proveedor compatible con Python y obtén
   su URL pública HTTPS. La URL aparece al crear el servicio o después de su
   primer despliegue; no se obtiene de GitHub ni de Vercel. Un ejemplo de
   formato es `https://queens-api.example.com`.
4. En Vercel, abre el proyecto y entra en **Settings → Environment Variables**.
   Crea una variable con nombre `API_BASE_URL` y como valor la URL HTTPS que te
   dio el proveedor de la API, sin añadir `/api` ni una barra final. Selecciona
   **Production** y también **Preview** si lo vas a usar allí, y guarda.
5. Haz un nuevo despliegue en Vercel. Las variables se usan al compilar y no
   cambian los despliegues que ya estaban hechos. Vercel usará `build.sh` y
   publicará `build/web` según `vercel.json`.

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
FastAPI. El proveedor asigna o muestra la dirección pública de la API después
de desplegarla; esa es la dirección que debes poner en `API_BASE_URL` en
Settings → Environment Variables del proyecto Vercel. Desde la raíz de
`app_web`, el comando de inicio habitual en un servicio Linux es:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

El backend actual guarda el marcador en `backend/scoreboard.json` y mantiene las
partidas en memoria. Antes de alojarlo en producción, el servicio debe ofrecer
almacenamiento persistente para los récords; una plataforma serverless con disco
efímero no preservará esos datos entre reinicios.

## Coste y límites de los planes gratuitos

El plan Hobby de Vercel cuesta actualmente 0 USD y está dirigido a proyectos
personales; aplica cuotas mensuales y sus condiciones pueden cambiar. Consulta
la [página del plan Hobby](https://vercel.com/docs/plans/hobby). Esto cubre el
frontend, no el servicio FastAPI.

No hay una promesa que permita garantizar que un servicio de terceros vaya a ser
gratuito para siempre. Oracle publica recursos Always Free sin límite de tiempo,
pero exige tarjeta para verificar la cuenta y puede recuperar máquinas gratuitas
que considere inactivas; consulta su
[documentación de recursos Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
y sus [preguntas frecuentes](https://www.oracle.com/cloud/free/faq/). Esto puede
ser especialmente relevante para una API con muy poco tráfico. Antes de elegir
un proveedor, comprueba sus límites, la política de inactividad y si requiere
una tarjeta o cuenta de facturación.

Para evitar depender de un servidor en la nube, habría que cambiar el juego para
que funcione sin API remota; en ese caso, las partidas y récords no serían
compartidos entre dispositivos tal como lo son con un backend. Otra posibilidad
es alojar la API en un equipo propio, teniendo en cuenta el coste de electricidad,
conexión y configuración.
