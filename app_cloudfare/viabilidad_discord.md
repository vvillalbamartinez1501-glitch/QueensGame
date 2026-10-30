# Viabilidad Discord Activity — Queens

> Análisis de si es posible implementar la web de Queens como una **Discord Activity** (aplicación embebida en Discord), qué cambios requeriría y cuál es el estado actual del código al respecto.

---

## 1. ¿Qué es una Discord Activity?

Una **Discord Activity** (antes llamada *Embedded App*) es una aplicación web que se ejecuta dentro del cliente de Discord, embebida en un iframe dentro de una llamada de voz o canal de voz. Los usuarios acceden a ella sin salir de Discord. Discord proporciona el **Embedded App SDK** para que la aplicación pueda comunicarse con el cliente de Discord (autenticación, información del servidor, etc.).

Las Activities se registran en el **Discord Developer Portal** y se someten a revisión antes de su publicación pública. Sin revisión solo funcionan para los miembros de un servidor de prueba autorizado.

---

## 2. Veredicto: ¿Es posible?

**Sí, es técnicamente posible.** La web de Queens puede funcionar como Discord Activity con cambios mínimos en el código. La infraestructura actual ya tiene preparación explícita para ello.

---

## 3. Lo que YA está preparado en el código

El proyecto incluye preparación deliberada para Discord Activities en varios puntos:

### 3.1 Cabecera CSP — `web/_headers`

```
/*
  ! X-Frame-Options
  Content-Security-Policy: frame-ancestors 'self' https://*.discordsays.com https://discord.com
```

Esta configuración:
- **Elimina `X-Frame-Options`**: sin esta eliminación, los navegadores bloquearían el embebido en un iframe (que es exactamente lo que Discord hace con las Activities).
- **Configura `frame-ancestors`** para permitir explícitamente que `discordsays.com` (el dominio de proxy de Discord para Activities) y `discord.com` puedan embeber la página en un iframe.

> Este archivo ya está listo y no necesita ningún cambio para el embebido básico.

### 3.2 Cabeceras CORS — `functions/api/[[path]].ts`

```typescript
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};
```

La API ya acepta peticiones desde cualquier origen, incluyendo el dominio proxy de Discord (`*.discordsays.com`).

### 3.3 Mención en el README

El README del proyecto (`README.md`, sección "Documentos legales y Discord") menciona explícitamente que los documentos legales (`terms.html` y `privacy.html`) deben configurarse en el Developer Portal de Discord, y que si se incorpora el **Embedded App SDK** hay que actualizar la política de privacidad.

---

## 4. ¿Qué falta para que funcione como Activity?

### 4.1 Registrar la aplicación en Discord Developer Portal

- Crear una aplicación en [https://discord.com/developers/applications](https://discord.com/developers/applications).
- Habilitar la actividad en la sección **Activities**.
- Configurar los campos de URL de la aplicación apuntando a `https://queens-game.pages.dev`.
- Configurar las URLs de términos (`/terms.html`) y privacidad (`/privacy.html`).
- Obtener el **Client ID** de la aplicación de Discord.

Este paso es **externo al código** y no requiere tocar ningún archivo del proyecto.

### 4.2 Cambios en el código (opcionales, no obligatorios para funcionar)

Para que la aplicación funcione como Activity en su versión más básica (iframe embebido sin integración con Discord), **no es necesario modificar ningún archivo de código**. El juego carga, la API responde y la partida funciona igual que en el navegador normal.

Sin embargo, para una integración más completa con Discord, sería necesario añadir:

#### A) Discord Embedded App SDK (opcional pero recomendado)

```dart
// En pubspec.yaml añadir una dependencia JS interop o usar un paquete
// Alternativamente, cargar el SDK desde JS en web/index.html
```

El SDK permite:
- Obtener información del usuario de Discord (nombre, avatar, ID) sin que el usuario tenga que iniciar sesión manualmente.
- Sincronizar la sesión entre múltiples usuarios en la misma llamada (modo multijugador).
- Acceder a la API de Discord para funciones como invitar amigos.

Para el juego Queens en su forma actual (puzzle de un solo jugador), **el SDK no es estrictamente necesario**.

#### B) URL de proxy de Discord

Discord redirige el tráfico de Activities a través de su proxy (`discordsays.com`). Esto puede provocar que rutas relativas funcionen incorrectamente si no se configura bien el `base href`.

Flutter ya usa `$FLUTTER_BASE_HREF` en `web/index.html`, que se sustituye durante la compilación por `flutter build web --base-href /`. Para Discord Activities puede ser necesario ajustar esto según la URL del proxy.

**Posible cambio mínimo:**

```bash
# En build.sh, modificar la línea de build:
flutter build web --release --base-href /
# (ya es el valor por defecto, normalmente no necesita cambio)
```

#### C) Ajuste de la política de privacidad y términos

Si se integra el SDK y se acceden a datos de usuarios de Discord (nombre, avatar, etc.), hay que actualizar `web/privacy.html` para reflejar ese tratamiento de datos antes de enviar la Activity a revisión de Discord.

---

## 5. Limitaciones y consideraciones

| Aspecto | Situación |
|---------|-----------|
| **Multijugador** | Queens es actualmente un puzzle de un solo jugador. Cada partida tiene un `game_id` único pero no hay sincronización en tiempo real entre usuarios. Para una Activity multijugador (todos ven el mismo tablero) habría que añadir WebSockets o polling, lo que implicaría cambios significativos. |
| **Autenticación** | La API actual no requiere inicio de sesión. Los récords son anónimos. Si se quiere vincular récords a usuarios de Discord hay que integrar OAuth2 de Discord o el SDK. |
| **Revisión de Discord** | Para publicar la Activity a usuarios fuera del servidor de prueba, Discord revisa la aplicación. Requiere que los documentos legales estén completos con datos reales. |
| **Plan gratuito de Cloudflare** | Las cuotas de Workers (100k req/día) son suficientes para un uso moderado como Activity, pero con muchos usuarios concurrentes se podrían agotar. |
| **Iframe y Flutter Web** | Flutter Web corre en un iframe sin problemas. La cabecera `_headers` ya gestiona correctamente los permisos necesarios. |
| **Persistencia de partida** | Al recargar o cambiar de canal en Discord, la partida se pierde porque el cliente no guarda el `game_id` en `localStorage`. Sería recomendable añadir persistencia del ID en el cliente para mejor experiencia. |

---

## 6. Resumen de cambios necesarios

### Para funcionar como Activity básica (iframe en Discord):

| Cambio | Archivo | ¿Necesario? |
|--------|---------|-------------|
| Registrar app en Discord Developer Portal | (externo, no es código) | ✅ Sí |
| Configurar URLs en Developer Portal | (externo) | ✅ Sí |
| Completar datos reales en `terms.html` y `privacy.html` | `web/terms.html`, `web/privacy.html` | ✅ Sí |
| Cabecera CSP para `discordsays.com` | `web/_headers` | ✅ Ya hecho |
| Cabeceras CORS en la API | `functions/api/[[path]].ts` | ✅ Ya hecho |

### Para una integración más profunda con Discord (opcional):

| Cambio | Archivo | ¿Necesario? |
|--------|---------|-------------|
| Integrar Discord Embedded App SDK | `web/index.html` o nueva dependencia Dart | ❌ Opcional |
| Vincular récords a usuarios de Discord | `functions/api/game.ts`, `migrations/` | ❌ Opcional |
| Persistir `game_id` en `localStorage` | `lib/main.dart` | ⚠️ Recomendado |
| Actualizar política de privacidad si se usan datos de Discord | `web/privacy.html` | ⚠️ Recomendado si se integra el SDK |

---

## 7. Conclusión

La web de Queens **puede implementarse como Discord Activity sin modificar ningún archivo de código**. El proyecto ya incluye:

1. La cabecera CSP que permite el embebido en iframe de Discord (`web/_headers`).
2. Las cabeceras CORS abiertas en la API.
3. Las páginas legales (`terms.html`, `privacy.html`) necesarias para el registro en el Developer Portal.
4. Mención explícita en el README de la integración con Discord.

Los únicos pasos obligatorios son externos al código: crear la aplicación en el Discord Developer Portal, configurar la URL que apunta a `https://queens-game.pages.dev` y completar los datos legales reales en los documentos HTML antes de solicitar la revisión.

La integración del **Embedded App SDK** y la vinculación de récords con cuentas de Discord son mejoras opcionales que enriquecerían la experiencia pero no son necesarias para que el juego funcione dentro de Discord.
