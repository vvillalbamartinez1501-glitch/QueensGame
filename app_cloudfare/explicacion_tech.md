# Explicación Técnica — Queens en Cloudflare

> Documento de referencia del proyecto `app_cloudfare`. Describe qué tecnologías se usan, para qué sirve cada pieza, cómo funciona el sistema de extremo a extremo y dónde quedará disponible la aplicación en la web.

---

## 1. Resumen ejecutivo

`app_cloudfare` es la versión de producción del juego **Queens** desplegada íntegramente en la infraestructura gratuita de Cloudflare. Combina:

| Capa | Tecnología | Papel |
|------|-----------|-------|
| Frontend | Flutter Web | Interfaz de usuario compilada a HTML/JS/CSS |
| Backend | Cloudflare Pages Functions (TypeScript) | API REST del juego |
| Base de datos | Cloudflare D1 (SQLite) | Persistencia de partidas y récords |
| Hosting | Cloudflare Pages | Publica el frontend con HTTPS gratuito |
| Orquestación local | Wrangler + npm | Desarrollo local y despliegue |

La URL pública final es del tipo `https://queensgame-2fk.pages.dev` (dominio gratuito `*.pages.dev`, sin tarjeta de pago requerida).

---

## 2. Stack tecnológico detallado

### 2.1 Frontend — Flutter Web

**Archivos relevantes:** `lib/main.dart`, `lib/services/api_service.dart`, `web/`, `pubspec.yaml`

El cliente está escrito en **Dart/Flutter** y compilado a una aplicación web estática (`flutter build web --release`). Flutter no genera un sitio HTML clásico sino una Single-Page Application (SPA) basada en un canvas/DOM administrado por el runtime de Flutter para web.

**Dependencias Flutter declaradas en `pubspec.yaml`:**

```yaml
dependencies:
  flutter:      sdk: flutter
  http:         ^1.2.2    # Cliente HTTP para llamar a la API
  url_launcher: ^6.3.2    # Abrir páginas legales en nueva pestaña
```

**Qué hace `lib/main.dart`:**

- Define el widget raíz `QueensApp` con tema oscuro Material 3 (color base `#38BDF8`, fondo `#0F172A`).
- `GameScreen` es el único widget de pantalla; gestiona todo el estado de la partida.
- El tablero se construye con un `GridView` responsivo: calcula el tamaño de celda según el ancho disponible y renderiza regiones con colores pastel diferenciados.
- Cada celda puede estar en tres estados: vacía (`0`), reina (`1`, icono `workspace_premium_rounded`) o cruz (`2`, icono `close_rounded`).
- El temporizador funciona con un `Timer.periodic` de 1 segundo en el cliente. El tiempo real se recalcula desde el servidor en cada respuesta para evitar deriva.
- La AppBar incluye botones para ver **récords** y **reglas**, ambos como `ModalBottomSheet` con datos cargados desde la API.

**Qué hace `lib/services/api_service.dart`:**

- Clase `ApiService` que encapsula todas las llamadas HTTP al backend.
- La URL base se resuelve relativa al `Uri.base` del navegador (mismo dominio) cuando no se define `API_BASE_URL` en tiempo de compilación. Esto significa **cero configuración de CORS** para el despliegue normal en Cloudflare Pages.
- Timeout global de 12 segundos por petición.
- Maneja errores HTTP convirtiendo el campo `detail` de la respuesta JSON en una excepción `ApiException`.

**Métodos expuestos por `ApiService`:**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `createGame(size, autoCross)` | `POST /api/games` | Inicia una partida nueva |
| `getGame(id)` | `GET /api/games/:id` | Recupera el estado de una partida |
| `updateCell(id, row, col, action)` | `POST /api/games/:id/cells` | Coloca/quita reina o marca/desmarca cruz |
| `undo(id)` | `POST /api/games/:id/undo` | Deshace el último movimiento |
| `reset(id)` | `POST /api/games/:id/reset` | Reinicia el tablero (mantiene el mapa) |
| `hint(id)` | `POST /api/games/:id/hint` | Coloca una reina de la solución |
| `setAutoCross(id, enabled)` | `PUT /api/games/:id/settings/auto-cross` | Activa/desactiva el modo Auto-cruces |
| `getRecords(size)` | `GET /api/scoreboard?size=N` | Top 10 récords del tamaño indicado |
| `getRules()` | `GET /api/rules` | Devuelve las reglas del juego |

---

### 2.2 Backend — Cloudflare Pages Functions (TypeScript)

**Archivos relevantes:** `functions/api/[[path]].ts`, `functions/api/game.ts`, `functions/api/types.ts`

El backend está escrito en **TypeScript** y se ejecuta como **Cloudflare Workers** (entorno V8 aislado, sin Node.js) mediante el sistema de **Pages Functions**. El nombre de archivo `[[path]].ts` es la convención de Cloudflare para capturar rutas dinámicas bajo `/api/`.

#### `functions/api/types.ts` — Tipos compartidos

Define las interfaces TypeScript del dominio:

```typescript
interface Env         { DB: D1Database }        // Binding a la base D1
interface GameState   { /* estado completo de partida en D1 */ }
interface GameResponse{ /* lo que se envía al cliente (sin solución) */ }
interface Validation  { is_valid, message, error_type, error_cells }
interface RecordEntry { time_seconds, time_formatted, moves, date }
```

`GameState` incluye: `game_id`, `size`, `regions[][]`, `board[][]`, `history[][][]`, `solution[][]`, `move_count`, `elapsed_seconds`, `started_at_ms`, `auto_cross`, `is_won`, `last_message`, `rank_position`.

#### `functions/api/[[path]].ts` — Entry point HTTP

- Exporta la función `onRequest` que Cloudflare invoca en cada petición a `/api/*`.
- Añade cabeceras CORS (`Access-Control-Allow-Origin: *`) a todas las respuestas.
- Captura errores: si es un `HttpError` devuelve el status correspondiente; si es un error inesperado devuelve 500.

#### `functions/api/game.ts` — Lógica de negocio completa

**Lógica del tablero:**

- `setCell(game, row, col, state)` — Coloca/quita una reina. Si `auto_cross` está activo, marca automáticamente con cruces todas las celdas de la misma fila, columna, región y adyacentes. Registra el cambio en `history`.
- `toggleCross(game, row, col)` — Alterna el estado de cruz en una celda.
- `undo(game)` — Extrae el último lote de `history` y revierte cada cambio en orden inverso.
- `reset(game)` — Vacía el tablero y el historial.
- `blockedCells(game, row, col)` — Calcula qué celdas quedan bloqueadas al colocar una reina: toda la fila, columna, región y las 8 celdas adyacentes (ortogonal + diagonal).

**Validación:**

- `validate(game)` — Comprueba en orden: conteo de reinas, reinas adyacentes (ortogonal o diagonal), conflictos por fila, por columna y por región. Devuelve `{ is_valid, message, error_type, error_cells }`.
- `maybeFinishGame(env, game)` — Si se han colocado todas las reinas y son válidas, marca la partida como ganada, detiene el temporizador y registra el récord en D1.

**Puzzles precomputados:**

- `puzzles.json` contiene **20 mapas por cada tamaño** (4×4 a 12×12 → 180 mapas en total). Al crear una partida se elige uno al azar con `Math.random()`.
- Cada mapa incluye `regions[][]` (qué región pertenece cada celda) y `solution[][]` (coordenadas de las reinas en la solución).
- Este diseño es necesario porque generar tableros válidos algorítmicamente supera el límite de **10 ms de CPU** del plan gratuito de Workers.

**Persistencia (D1):**

- `loadGame(env, gameId)` — Lee `data_json` de la tabla `games` y deserializa el `GameState` completo.
- `saveGame(env, game)` — Hace un `INSERT ... ON CONFLICT DO UPDATE` (upsert) para guardar o actualizar el estado.
- `addRecord(env, game)` — Inserta en `records` y calcula el puesto del récord con una consulta de ranking por tiempo y movimientos.
- `topRecords(env, size)` — Devuelve el top 10 para un tamaño concreto ordenados por tiempo ASC, movimientos ASC, id ASC.

**Router interno (sin framework):**

```
GET  /api/health
GET  /api/rules
POST /api/games
GET  /api/games/:id
POST /api/games/:id/cells
POST /api/games/:id/undo
POST /api/games/:id/reset
POST /api/games/:id/hint
PUT  /api/games/:id/settings/auto-cross
POST /api/games/:id/validate
GET  /api/scoreboard
GET  /api/scoreboard?size=N
GET  /api/scoreboard/:size
```

---

### 2.3 Base de datos — Cloudflare D1

**Archivos relevantes:** `migrations/0001_initial.sql`, `wrangler.jsonc`

D1 es la base de datos **SQLite distribuida** de Cloudflare. Se accede desde Workers mediante el binding `DB` (objeto `D1Database` en TypeScript).

**Esquema (`migrations/0001_initial.sql`):**

```sql
-- Estado completo de cada partida como JSON
CREATE TABLE games (
  game_id    TEXT PRIMARY KEY,
  data_json  TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de récords con restricciones de integridad
CREATE TABLE records (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  grid_size      INTEGER NOT NULL CHECK (grid_size BETWEEN 4 AND 12),
  time_seconds   INTEGER NOT NULL CHECK (time_seconds >= 0),
  time_formatted TEXT NOT NULL,
  moves          INTEGER NOT NULL CHECK (moves >= 0),
  date           TEXT NOT NULL
);

-- Índice compuesto para ranking eficiente
CREATE INDEX records_ranking ON records (grid_size, time_seconds, moves, id);
```

El estado de cada partida se serializa como JSON completo (incluyendo `history` para el deshacer) y se almacena en `data_json`.

---

### 2.4 Configuración — `wrangler.jsonc`

```jsonc
{
  "name": "queensgame-2fk",
  "compatibility_date": "2026-10-19",
  "pages_build_output_dir": "./build/web",
  "d1_databases": [{
    "binding": "DB",
    "database_name": "queensgame-2fk",
    "database_id": "2712350a-a9a7-4e0a-bf5d-00b2c81a80d8",
    "migrations_dir": "migrations"
  }]
}
```

Configura Wrangler (CLI de Cloudflare) para el proyecto. El binding `DB` expone la base D1 a las Pages Functions tanto en local como en producción.

---

### 2.5 Build — `build.sh`

Script de compilación ejecutado por Cloudflare Pages en cada despliegue:

1. Detecta si `flutter` está disponible en el PATH.
2. Si no lo está, clona el canal stable de Flutter desde GitHub en `/tmp/flutter-sdk`.
3. Habilita el target web (`flutter config --enable-web`).
4. Instala dependencias (`flutter pub get`).
5. Compila el proyecto (`flutter build web --release`) → genera `build/web/`.

Cloudflare Pages publica el contenido de `build/web/` como archivos estáticos.

---

## 3. Flujo completo de una partida

```
Usuario (navegador)
    │
    │  1. Carga https://queensgame-2fk.pages.dev/
    │     → Cloudflare Pages sirve build/web/index.html + flutter_bootstrap.js
    │     → El runtime de Flutter arranca en el navegador
    │
    │  2. Flutter llama POST /api/games  {size: 8}
    │     → Pages Function recibe la petición
    │     → Selecciona un puzzle aleatorio de puzzles.json para 8×8
    │     → Crea GameState con UUID, tablero vacío, regiones y solución
    │     → Guarda en D1 (tabla games)
    │     → Devuelve GameResponse (sin exponer la solución)
    │
    │  3. Usuario toca una celda (fila 3, col 5)
    │     → POST /api/games/:id/cells  {row:3, col:5, action:"queen"}
    │     → setCell coloca la reina, auto_cross marca adyacentes
    │     → maybeFinishGame comprueba si ya es solución válida
    │     → saveGame actualiza D1
    │     → Devuelve GameResponse actualizado
    │
    │  4. Usuario completa la solución
    │     → validate() confirma que es válida
    │     → addRecord() inserta récord en D1, calcula ranking
    │     → GameResponse incluye is_won:true y rank_position
    │     → Flutter muestra tarjeta de victoria con posición en el ranking
    │
    └───────────────────────────────────────────────────────────
```

---

## 4. Archivos web estáticos

| Archivo | Propósito |
|---------|-----------|
| `web/index.html` | Shell HTML generado por Flutter. Carga `flutter_bootstrap.js`. |
| `web/manifest.json` | Manifest PWA: permite instalar la app en dispositivos móviles. |
| `web/_headers` | Configura cabeceras HTTP de Cloudflare Pages. Elimina `X-Frame-Options` y permite embebido desde `discordsays.com` y `discord.com` (preparado para Discord Activity). |
| `web/favicon.png` | Icono de la aplicación. |
| `web/icons/` | Iconos PWA en tamaños 192×192 y 512×512, incluidas versiones maskable. |
| `web/terms.html` | Condiciones del servicio (borrador; requiere datos reales del titular). |
| `web/privacy.html` | Política de privacidad (borrador; requiere datos reales del titular). |

---

## 5. Límites del plan gratuito de Cloudflare

| Recurso | Cuota gratuita | Impacto si se supera |
|---------|---------------|----------------------|
| Workers (Pages Functions) | 100.000 req/día · 10 ms CPU/req | La API deja de responder hasta el reset diario |
| D1 lecturas | 5 millones/día | Las partidas no cargan |
| D1 escrituras | 100.000/día | No se pueden guardar movimientos ni récords |
| D1 almacenamiento | 5 GB | Límite muy holgado para este juego |
| Pages builds | 500/mes | Cada push a la rama principal consume un build |

El diseño del proyecto (puzzles precomputados, JSON blob para el estado) está optimizado para mantenerse dentro de estos límites.

---

## 6. Dónde estará disponible en web

Una vez desplegado, el proyecto estará accesible en:

```
https://queensgame-2fk.pages.dev
```

Rutas públicas disponibles tras el despliegue:

| URL | Contenido |
|-----|-----------|
| `https://queensgame-2fk.pages.dev/` | Aplicación Flutter (el juego) |
| `https://queensgame-2fk.pages.dev/terms.html` | Condiciones del servicio |
| `https://queensgame-2fk.pages.dev/privacy.html` | Política de privacidad |
| `https://queensgame-2fk.pages.dev/api/health` | Health check de la API (`{"status":"ok"}`) |
| `https://queensgame-2fk.pages.dev/api/rules` | Reglas del juego (JSON) |
| `https://queensgame-2fk.pages.dev/api/scoreboard?size=8` | Récords para 8×8 (JSON) |

> **Dominio personalizado:** Cloudflare Pages permite vincular un dominio propio sin coste adicional de plataforma, aunque el dominio en sí tiene coste en el registrador elegido.

---

## 7. Mapa de archivos del proyecto

```
app_cloudfare/
├── build.sh                    ← Script de compilación para Cloudflare Pages
├── wrangler.jsonc              ← Configuración Wrangler (nombre, D1 binding)
├── package.json                ← Dependencias TypeScript + scripts npm
├── tsconfig.json               ← Configuración del compilador TypeScript
├── pubspec.yaml / pubspec.lock ← Dependencias y lock file de Flutter/Dart
├── puzzles.json                ← Banco de 180 puzzles precomputados (20 × 9 tamaños)
│
├── functions/
│   └── api/
│       ├── [[path]].ts         ← Entry point HTTP + CORS + manejo de errores
│       ├── game.ts             ← Lógica del juego, router, acceso a D1
│       └── types.ts            ← Interfaces TypeScript compartidas
│
├── migrations/
│   └── 0001_initial.sql        ← DDL de las tablas games y records
│
├── lib/
│   ├── main.dart               ← App Flutter: UI, estado, interacción
│   └── services/
│       └── api_service.dart    ← Cliente HTTP que consume la API REST
│
└── web/
    ├── index.html              ← Shell HTML de la SPA Flutter
    ├── manifest.json           ← Manifest PWA
    ├── _headers                ← Cabeceras Cloudflare Pages (CSP para Discord)
    ├── favicon.png             ← Icono del sitio
    ├── terms.html              ← Condiciones del servicio
    ├── privacy.html            ← Política de privacidad
    └── icons/                  ← Iconos PWA (192 y 512 px, maskable)
```
