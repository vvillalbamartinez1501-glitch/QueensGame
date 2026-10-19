# Queens en Cloudflare (Pages + Functions + D1)

Este proyecto migra el cliente Flutter web y la API FastAPI a un despliegue
integrado en Cloudflare:

- **Pages** publica el cliente Flutter y asigna una dirección HTTPS gratuita
  bajo `pages.dev`.
- **Pages Functions**, que se ejecuta sobre Cloudflare Workers, implementa las
  rutas `/api/...` del juego.
- **D1** guarda partidas, historial de movimientos y récords en SQLite remoto.

El navegador llama a `/api` en el mismo dominio. No hace falta definir
`API_BASE_URL` ni configurar CORS para el despliegue normal.

## Antes de empezar: cuenta y coste

1. Crea o usa una cuenta gratuita de Cloudflare.
2. Sigue únicamente el flujo gratuito. **No añadas tarjeta, cuenta bancaria ni
   método de pago; no cambies a Workers Paid ni a otro plan de pago.** Si
   Cloudflare te pide un método de pago para continuar, detente: no completes
   ese paso y no despliegues bajo este requisito.
3. Usa la dirección gratuita `*.pages.dev`. No compres ni añadas un dominio
   propio.

Las cuotas y condiciones pueden cambiar; ningún proveedor puede garantizar que
el nivel gratuito vaya a existir para siempre. En las condiciones publicadas
actualmente, Workers Free permite 100.000 solicitudes diarias y 10 ms de CPU por
solicitud. D1 incluye cuotas gratuitas de lectura, escritura y almacenamiento.
Pages Free publica hasta 500 builds al mes y ejecuta uno a la vez.
Al exceder cuotas gratuitas, la API puede dejar de responder hasta que se
restablezcan; no pases a un plan de pago para resolverlo. Consulta las
[cuotas y precios de Workers](https://developers.cloudflare.com/workers/platform/pricing/)
y [cuotas de D1](https://developers.cloudflare.com/d1/platform/pricing/).

## Qué se ha migrado y qué cambia

- Se conservan los endpoints usados por Flutter: salud, reglas, partidas,
  casillas, deshacer, reiniciar, Auto-X, pistas, validación y clasificación.
- El estado de las partidas y los récords se guarda en D1, así que sobrevive a
  nuevos despliegues. No se pierde al reiniciar una instancia.
- El backend de Python se ha reescrito como TypeScript para Pages Functions.
- La generación de niveles de Python podía tardar decenas o centenares de
  milisegundos (hasta más de medio segundo en pruebas locales para algunos
  tamaños), por encima del límite gratuito de CPU de Workers. Por eso `puzzles.json`
  contiene un banco de veinte tableros por tamaño (4x4 a 12x12) generado fuera de
  Cloudflare. Al iniciar partida se elige uno al azar. Se conservan las reglas,
  niveles de tamaño variable, Auto-X, deshacer, cronómetro, pistas y récords,
  pero no se crea un tablero matemáticamente nuevo en cada partida. El banco
  puede ampliarse antes de desplegar.
- La fecha de los récords se guarda en UTC con el mismo formato que usaba la
  interfaz.

## Archivos principales

- `lib/`, `web/`, `pubspec.yaml` y `pubspec.lock`: cliente Flutter web.
- `functions/api/`: implementación de los endpoints de la API.
- `migrations/0001_initial.sql`: tablas de partidas y récords.
- `puzzles.json`: niveles precomputados para el límite de CPU gratuito.
- `wrangler.jsonc`: configuración de Pages y binding D1 `DB`.
- `build.sh`: compila Flutter Web; si no encuentra Flutter, descarga el canal
  estable durante la compilación.

## Publicar desde GitHub sin añadir método de pago

### 1. Subir el proyecto a GitHub

Desde la raíz de este repositorio:

```bash
git add app_cloudfare
git commit -m "Add Cloudflare-hosted Queens web app"
git push
```

Comprueba que `app_cloudfare/` está en la rama que vas a desplegar. Si quieres
usar un repositorio separado, copia el contenido de esta carpeta a la raíz del
repositorio nuevo.

### 2. Crear la base D1

1. En el panel de Cloudflare abre **Workers & Pages → D1 SQL Database**.
2. Crea una base de datos llamada `queens-game`.
3. Copia el **Database ID** mostrado en sus detalles.
4. En GitHub, edita `app_cloudfare/wrangler.jsonc` y sustituye el valor
   `00000000000000000000000000000000` de `database_id` por ese ID. Guarda y
   sube el cambio:

   ```bash
   git add app_cloudfare/wrangler.jsonc
   git commit -m "Configure the Cloudflare D1 database"
   git push
   ```

5. En el panel D1, abre la base `queens-game`, selecciona **Console** y ejecuta
   el contenido completo de `app_cloudfare/migrations/0001_initial.sql`. Esto
   crea las tablas persistentes `games` y `records`.

La base solo se crea y migra una vez. No borres ni recrees las tablas al hacer
actualizaciones normales de la web.

### 3. Crear Pages y conectarlo a GitHub

1. En Cloudflare abre **Workers & Pages → Create application → Pages → Connect
   to Git** y autoriza el repositorio de GitHub que acabas de subir.
2. Elige el repositorio y la rama de producción.
3. Configura el proyecto:
   - **Project name:** `queens-game` (debe coincidir con `wrangler.jsonc`).
   - **Root directory:** `app_cloudfare`.
   - **Framework preset:** `None`.
   - **Build command:** `bash build.sh`.
   - **Build output directory:** `build/web`.
4. En **Settings → Functions → D1 database bindings**, añade:
   - **Variable name / binding:** `DB`
   - **D1 database:** `queens-game`
   - Aplica la misma vinculación al entorno de Production. Si vas a probar
     Preview Deployments, configura también allí la base que quieras usar.
5. No añadas una variable `API_BASE_URL`: el cliente y la API usan el mismo
   dominio. No introduzcas secretos ni información de pago.
6. Guarda y lanza el primer despliegue. El primer build descarga Flutter y puede
   tardar varios minutos; los siguientes builds pueden reutilizar la caché de
   dependencias de Pages.

`wrangler.jsonc` también declara el binding para despliegues y desarrollo con
Wrangler. Si el panel solicita el binding por separado, verifica que el nombre
sea exactamente `DB` y que apunte a la misma base.

### 4. Comprobar la publicación

Cloudflare mostrará la URL pública al terminar, por ejemplo
`https://queens-game.pages.dev`.

1. Abre `https://<tu-proyecto>.pages.dev/api/health`. Debe responder:

   ```json
   {"status":"ok"}
   ```

2. Abre la web y prueba:
   - crear partidas de tamaños 4 a 12;
   - colocar y quitar reinas y cruces;
   - activar y desactivar Auto-X;
   - deshacer y reiniciar;
   - usar una pista y comprobar la validación;
   - completar una solución y confirmar que aparece el récord;
   - consultar la misma partida desde su identificador usando
     `/api/games/<game_id>` y confirmar que D1 devuelve su estado guardado.
3. Si la API responde `Error interno del servidor`, revisa los logs de Functions
   en Cloudflare y confirma que el binding `DB` existe en el entorno publicado.
   Si responde un error SQL, revisa que ejecutaste la migración en esa base D1.

## Desarrollo y comprobaciones locales (opcional)

Se necesitan Flutter, Node.js y npm. Desde esta carpeta:

```bash
flutter pub get
flutter build web --release
npm install
npm run typecheck
```

Para ejecutar Pages localmente, instala las dependencias y crea las tablas en la
base D1 local con la migración incluida:

```bash
 npm install
npx wrangler d1 migrations apply queens-game --local
npx wrangler pages dev build/web
```

La base local es independiente de D1 remoto. No uses `--remote` ni ejecutes
migraciones remotas salvo que realmente quieras modificar la base publicada.

## Límites y resolución de problemas

- **El frontend abre, pero falla al iniciar partida:** comprueba la URL
  `/api/health`, el binding `DB` y que la base tenga las tablas de la migración.
- **Error de CPU de Worker:** el código evita generar tableros en la petición y
  usa `puzzles.json`; revisa que el despliegue esté ejecutando esta versión.
- **Récords o partidas no aparecen:** asegúrate de que Preview y Production no
  estén enlazados a bases distintas.
- **Se agota una cuota gratuita:** espera a que se restablezca o reduce el uso.
  No cambies a un plan de pago si quieres mantener el requisito de cero coste.
- **No hay identidad ni sincronización por usuario:** como en la API original,
  los identificadores de partida no requieren iniciar sesión. No guardes datos
  privados en ellos.
- **Al recargar la web se inicia una partida nueva:** el cliente actual no
  guarda el identificador de la partida en el navegador. D1 conserva cada
  partida para que la API pueda leerla de nuevo, pero restaurarla automáticamente
  tras recargar requeriría añadir persistencia del identificador en el cliente.

GitHub guarda el código; Cloudflare Pages publica la web; Pages Functions ejecuta
la API; D1 persiste los datos. Publicar en GitHub por sí solo no despliega el
sitio ni crea la base de datos.
